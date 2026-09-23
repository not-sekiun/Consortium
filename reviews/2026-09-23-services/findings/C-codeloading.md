# C-codeloading — Plugin / component dynamic loading

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high.

Files:
- consortium/server/services/plugins_service.py
- consortium/server/services/component_loader_services/component_loader_service.py
- consortium/server/services/component_loader_services/plugin_loader_service.py
- consortium/server/services/component_loader_services/agent_profile_loader_service.py
- consortium/server/services/component_loader_services/event_hook_loader_service.py
- consortium/server/services/component_loader_services/listener_profile_loader_service.py
- consortium/server/services/component_registry_services/component_registry_service.py
- consortium/server/services/component_registry_services/plugin_registry_service.py
- consortium/server/services/component_registry_services/event_hook_registry_service.py
- consortium/server/services/component_registry_services/agent_profile_registry_service.py
- consortium/server/services/component_registry_services/listener_profile_registry_service.py

Trust model used: the `manifest.json` (and `pyproject.toml`) inside a component directory, and the `entry_point` string within it, are treated as attacker-controlled input (a dropped/third-party plugin). The `.py` bodies themselves execute by design; the concern is what the loader is made to import/execute and how robustly it fails. Callers: `plugins_service.load_framework_plugins()` is invoked at server startup over the fixed `plugins_directory` (server.py:292); no REST route currently reaches the directory-loading methods with a client-supplied path (no `plugin` routes exist under `server/api`), which bounds the exposure of the arbitrary-`directory` entry points today but not the `entry_point`/manifest surface.

## Findings

### [SEV: high] `entry_point` module is used to build a file path and dotted import path with no confinement to the component directory
- **File:** component_loader_service.py:177-192 (`_get_entry_point_from_manifest_json`), component_loader_service.py:270-319 (`_validate_component_directory_structure`), plugin_loader_service.py:34-42 (schema only checks `entry_point` is a string)
- **Category:** injection
- **What:** The manifest `entry_point` (e.g. `module.path:Symbol`) is validated only as "a string containing a colon". The module part is split on `.` and joined onto `component_directory` to locate a `.py`, then the file's path relative to `consortium_root` is turned back into a dotted module name and passed to `importlib.import_module` / `importlib.reload`. Nothing constrains the module string to stay inside the component's own directory, so `..` segments or an absolute/drive-qualified segment let the manifest point the import at any `.py` under `consortium_root` other than the plugin's own tree.
- **Failure scenario:** A plugin manifest sets `entry_point` to a path that (after `pathlib.Path(component_directory, *parts)` join) resolves onto an existing framework module inside `consortium_root`, e.g. traversing up into `consortium/server/...`. `component_file.exists()` passes, the computed dotted path equals that module's real import name, so `component_module_path in sys.modules` is True (it is already imported) and the loader calls `importlib.reload()` on a live framework module (component_loader_service.py:303-306). Reloading a module other code holds references into re-executes its top-level code and creates duplicate class objects, breaking `isinstance` checks and singletons elsewhere. Even absent a reload, the manifest can force import (top-level execution) of an arbitrary in-tree module the plugin was never meant to touch. `pathlib`'s `relative_to` is purely lexical and does not collapse `..`, so the confinement the code appears to rely on is not actually enforced.
- **Fix:** Reject `entry_point` module strings containing path separators, `..`, leading dots, or anything that is not a plain dotted identifier; after building `component_file`, `.resolve()` it and require `is_relative_to(component_directory.resolve())` before importing; do not `reload` a module whose resolved path lies outside the component directory.

### [SEV: high] Malformed/hostile `entry_point` raises an uncaught `ValueError` from `relative_to`, aborting all plugin loading (startup DoS)
- **File:** component_loader_service.py:294-297 (the `relative_to` call sits *before* the `try` at 300-319), component_loader_service.py:478-489 (batch loop catch set), plugins_service.py:158-168 and 496-499 (propagation path)
- **Category:** crash / dos
- **What:** `component_module_path = ".".join(component_file.relative_to(self._consortium_root).parts)[...]` runs outside any try/except. If `entry_point` yields an existing `.py` that is not under `consortium_root` (an absolute/drive-qualified segment, or `..` traversal to a real file outside the tree), `relative_to` raises `ValueError`. `get_component_from_directory` does not catch it; the batch scanner `get_all_components_from_directory` only catches `ComponentLoadingError`/`ComponentConfigurationError`/`ComponentDependencyError`/`_component_framework_error` (478-488), and `wrap_filesystem_errors` only wraps `OSError` (utils.py:100/118). So the `ValueError` propagates out of discovery.
- **Failure scenario:** One plugin dropped into `plugins_directory` with `entry_point: "C:/Users/x/evil:Sym"` (pointing at any existing `.py` outside `consortium_root`). At startup `load_framework_plugins()` (plugins_service.py:496) calls `get_all_plugins_from_directory` -> `get_all_components_from_directory`; the `ValueError` is not collected per-plugin, it unwinds through `load_framework_plugins` (no try around 496) and crashes server startup. A single malformed manifest thus prevents every other plugin from loading, instead of being reported as one failed component.
- **Fix:** Move the `relative_to` inside the guarded block and convert failure into `entry_point_module_not_found` / `invalid_manifest_file_schema`; add `ValueError` (or the confinement check from the previous finding) to the per-component catch set so one bad manifest cannot abort the whole scan.

### [SEV: med] Async load path (`load_component`) skips the duplicate-label and component-dependency validation that `register_component` enforces
- **File:** component_registry_service.py:120-137 (`load_component`) vs component_registry_service.py:81-101 (`register_component`); reached via plugins_service.py:332-336 (`load_plugin_from_directory`)
- **Category:** perms / error-handling (inconsistent enforcement)
- **What:** `register_component` checks id uniqueness, label uniqueness, and `validate_component_component_dependencies` before inserting. `load_component` (the async path used by `load_plugin_from_directory` and `reload`) checks only id uniqueness, then runs `_component_load_procedure` (which *starts* the plugin) and inserts. Duplicate labels and unsatisfied/incompatible component dependencies are silently accepted on this path.
- **Failure scenario:** Two plugins share a `label`, or a plugin declares a dependency on a component that is not registered / is an incompatible version. Loading them via `load_framework_plugins` (which uses `register_plugin`) is rejected; loading the same plugin via `load_plugin_from_directory` (single-plugin load / reload) is accepted and started, producing an ambiguous label space and a plugin running with unmet dependency invariants.
- **Fix:** Have `load_component` run the same id + label + dependency validation as `register_component` (factor the checks into one helper both call) before invoking `_component_load_procedure`.

### [SEV: med] TOCTOU in `load_component`: the id check and the insert straddle an `await`, so a component can be loaded and started twice
- **File:** component_registry_service.py:127-136 (`await _component_load_procedure` between the `in self._components` check and the assignment); plugins_service.py:655-704 (`reload_framework_plugins` gathers load tasks concurrently), plugins_service.py:585-602 (concurrent unloads)
- **Category:** concurrency
- **What:** `self._components` is a plain dict with no lock. `load_component` checks `id in self._components` (127), awaits the load procedure (132, which calls `component.start()` with a timeout for plugins), then inserts (136). Two concurrent loads for the same id both pass the check before either inserts.
- **Failure scenario:** `reload_framework_plugins` builds `load_plugin_tasks` and runs them under a single `asyncio.gather` (701). If discovery yields the same plugin directory twice (e.g. a stray nested `manifest.json`, or a plugin that also failed to unload), both tasks pass the id check and both call `component.start()` on the plugin, double-starting it and leaving one instance overwritten in the registry but still running. Same window exists between concurrent `load`/`unload`/`reload` calls generally.
- **Fix:** Guard registry mutation (`load`/`unload`/`register`/`reload`) with an `asyncio.Lock`, or re-check membership and insert a placeholder before the `await` so the second caller fails fast.

### [SEV: med] `reload_component_by_component_id` unloads before loading with no rollback: a failed reload permanently drops the component
- **File:** component_registry_service.py:166-187
- **Category:** error-handling / crash (inconsistent state)
- **What:** Reload captures `root_directory`, calls `unload_component_by_component_id` (which stops and `del`s the entry, 155-164), then `load_component_from_directory`. If the load half fails (manifest now invalid, dependency missing, module import raises, start times out) the exception propagates and the component is already gone from the registry with nothing restored.
- **Failure scenario:** Operator reloads a running plugin after its on-disk `manifest.json` was edited to something invalid, or its `on_started` now raises. The plugin is stopped and deregistered, the reload raises, and the previously-working plugin is neither running nor registered; it can only be recovered by a full framework reload. Also, between the `await` at 179 and 183 the component is absent, so concurrent `get_component_by_component_id` returns not-found for a plugin that is supposed to exist.
- **Fix:** On load failure, re-register/restart the previously-loaded instance (or load the new instance first and swap atomically under a lock), and document that reload is not atomic if this cannot be guaranteed.

### [SEV: low] Internal import/instantiation exception text and absolute server paths are surfaced in error payloads
- **File:** component_loader_service.py:315-319 and 384-388 (`internal_error_message=str(exc)`), plus `component_directory=str(directory)` / `entry_point_module=str(component_file)` throughout (e.g. 148-159, 289-292, 329-333)
- **Category:** info-leak
- **What:** When import or instantiation of a component raises, the raw exception string is embedded into `InternalComponentError` and carried outward; component/entry-point errors embed absolute filesystem paths. These exceptions are domain errors that the API layer wraps and returns to clients.
- **Failure scenario:** A crafted or broken plugin raises during import with a message containing environment details; that text (and the absolute path layout of the server, `consortium_root`-derived) reaches the API/log consumer. In a C2 the operator may be trusted, but arbitrary import-time exception text is an uncontrolled channel.
- **Fix:** Log the full exception server-side; return a generic "failed to import component" detail without the raw `str(exc)`; consider relativizing paths in client-facing error detail.

### [SEV: low] Discovery scans every file with `rglob("*")` and dependency resolution is super-linear — unbounded work driven by plugin-dir contents
- **File:** component_loader_service.py:461-464 (`directory.rglob("*")` then filter `name == "manifest.json"`), plugins_service.py:684-700 (same pattern in `reload_framework_plugins`), component_loader_service.py:563-597 (`in_skipped_components` O(n) inside an O(n^2) `while True` prune loop)
- **Category:** dos
- **What:** Discovery walks the entire subtree (every file, not `rglob("manifest.json")`) under the plugins directory; a plugin can ship a very deep/wide tree that makes discovery expensive. Load-order resolution nests a linear membership scan inside a repeated full-graph pass, so pathological dependency graphs are roughly cubic.
- **Failure scenario:** A malicious/oversized plugin directory (huge file count, or many mutually-invalid dependencies) makes each discovery/reload pass slow enough to stall startup and every reload.
- **Fix:** Use `rglob("manifest.json")`; optionally cap discovery depth. Replace the skipped-set membership scan with a set and resolve invalid-dependency propagation with a worklist instead of repeated full passes.

### [SEV: low] Duplicate component labels silently collapse in `resolve_component_load_order`, dropping a component from the load order
- **File:** component_loader_service.py:533-538 (label->component dict comprehensions), 581, 603-606
- **Category:** crash / error-handling
- **What:** Load order is computed over `label`-keyed maps. Two components with the same label collapse to one map entry, so one is silently omitted from `ordered_load_components`, and `current_batch_label_component_map[label]` (581/604) only ever yields the last-wins instance. Duplicate-label detection only happens later at register time.
- **Failure scenario:** Two plugins declare the same label; one is dropped from the resolved load order entirely (not even reported as skipped), and dependency edges pointing at that label resolve to the wrong instance.
- **Fix:** Detect duplicate labels within a batch up front and report each as a skipped/errored component, or key the graph on component id and map labels to id-sets.

## Design notes
- The manifest JSON schema (`{"entry_point": string, "enabled": bool}`, `additionalProperties: False`) is duplicated verbatim across all four domain loaders (plugin_loader_service.py:34-42, agent_profile_loader_service.py:50-58, event_hook_loader_service.py:50-58, listener_profile_loader_service.py:46-54). Hoist to a shared constant so the entry-point contract (and any hardening added per the high findings) is defined once.
- The four domain loaders otherwise differ only by `_component_type`, `_component_framework_error`, `_component_exceptions`, and an optional `_post_validate_component_object`. This is already well factored; the only real per-domain logic is the profile post-validation. Good separation.
- `_validate_component_directory_structure` conflates three responsibilities (path resolution, import/reload, symbol lookup). Splitting path-resolution (with the confinement check) into its own method would make the trust boundary explicit and testable, and is the natural home for the fix to the two high findings.
- Reload trusts on-disk contents via `component.root_directory` (component_registry_service.py:177-187) with no re-verification that the directory is still under the framework plugins directory. Combined with the arbitrary-`directory` entry points on `PluginsService` (`get/register/load_plugin_from_directory` accept any path), the trust boundary is "whatever path a caller supplies"; today no REST route feeds these, but if one is ever added it must enforce `is_relative_to(plugins_directory)` at the API boundary.

## Notes
- No `eval`/`exec`/`pickle`/`yaml.unsafe_load` or archive extraction (zip-slip) exists in scope; the only dynamic-execution surface is the `importlib` entry-point path covered above. `pyproject.toml` is parsed with `tomllib` (safe) and dependencies are only version-checked via `importlib.metadata.version`, never imported here.
- `normalize_uuid` is just `str(value)` (utils.py:169-170), so `get_component_by_component_id` cannot crash on a malformed id — a bad id cleanly becomes not-found. No finding.
- Exposure of the arbitrary-`directory` load methods depends on API wiring outside scope; confirmed no current `plugin` routes under `server/api`, so rated design-note rather than a live authz finding. Worth a human check if a plugin-management API is planned.
- The `event_hook_registry_service` load/unload rollback handling (register-then-setup with explicit deregister on failure, 40-125) is notably more careful than the plugin path; it is the model the reload finding should follow.
