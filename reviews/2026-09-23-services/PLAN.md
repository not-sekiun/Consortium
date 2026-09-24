# Remediation plan: implementation handoff

Triage finished 2026-09-24. **Every item is decided except #6 (on hold). Next step is implementation.**
This file is self-contained: a fresh agent should be able to start at "Implementation order" without
re-deriving context. Background: `TRIAGE.md` (quadrants), `SUMMARY.md`, `findings/*.md`.

## Ground rules (from `AGENTS.md`, plus decisions made with the user)

- Repo root: `C:\Users\angus\Desktop\Consortium`. Windows, PowerShell, Python 3.14, `uv`.
- Review base commit `0a404028` is still HEAD. `consortium/server/services/tasks_service.py` and
  `tests/services_tests/test_tasks_service.py` have **unrelated uncommitted user work: do not touch**.
- Do NOT read or modify `consortium/components`, `docs`, `scripts`, `data`, `test_agents` (the one
  grep of `components/` needed for #8 is already done, results below).
- Do NOT run tests or lint unless the user says so. Write/update tests, then ask.
- Commit only when asked. Never add Claude/Anthropic attribution to commits.
- Comments: `#` only (docstrings are for public docs), ASCII only, no em dashes, terse, explain why
  not what, rarely more than 3 lines.
- Design philosophy: mechanism in the framework, policy at the boundary; limits parameterized and
  default off; documenting a hazard is preferred over removing the caller's choice.
- Authorization: all operators are peers. Never add ownership-based checks.
- Line numbers below were verified 2026-09-24 against HEAD; re-check locally before editing.
- After finishing an item: set its status to `implemented` in the table and add a one-line note
  (files touched, tests added). `verified` only after the user has run/approved tests.

## Status and implementation order

| Order | # | Item | Status |
|---|---|---|---|
| 1 | 8 | Per-instance template binding (user priority: ASAP) | implemented |
| 1 | 3 | Component loader startup DoS (same loader files as #8, do together) | implemented |
| 2 | 5 | Delete API catch-alls | implemented |
| 3 | 7 | Sync event handlers: accept and adapt | implemented |
| 4 | 4 | Log-format injection | implemented |
| 5 | 2 | Atomic JSON writes | implemented |
| 6 | 1 | Password/session-id redaction + `log_secrets` gate | implemented |
| - | 6 | Generator build / listener params in logs + events | **on hold** (do not implement) |

Implementation notes (committed locally on `fix/code-review-fixes`, not pushed):
- #8 (commit `515320ca`): per-instance binding via `create_agent_generator` /
  `create_listener`; generator `agent_type` / `compatible_listener_types` and listener
  `listener_type` are now derived properties; loaders no longer write onto shared
  classes; `c2_types_service` reference resolution updated. Deviation from the plan: the
  generator also binds the template on its class transiently just before construction,
  because `__init__` builds the per-template payload service and needs the template then
  (the ":481-483 stays" note overlooked this). create_agent_generator is synchronous so
  the transient binding cannot interleave and the per-instance attribute is what every
  read resolves. Tests: added `tests/framework_tests/test_per_instance_template_binding.py`;
  updated `test_agent_type_references.py`, `test_c2_types_service.py`.
- #3 (commit `8f5cf068`): identifier validation of entry point module/symbol in
  `_get_entry_point_from_manifest_json`; wrapped the `relative_to` ValueError; batch
  catch-all in `get_all_components_from_directory`; renamed
  `_post_validate_component_object` -> `_assemble_component` (base + both loaders).
  Tests added to `test_component_loader_service.py` (non-identifier entry points,
  per-component unexpected error). Part (c) needed no change (agent_type/listener_type
  calls were never wrapped).
- #5 (commit `58c03af7`): deleted the six `except Exception` catch-alls in the start/
  stop/cancel routes of `listeners_api.py` and `agent_generators_api.py`; kept each
  `*FatalError` branch. No new tests (deletion; existing API tests still pass).
- #7 (commit `75ada98c`): added `_invoke_event_handler` async helper and used it in the
  `trigger_event` gather; widened `register_event_handler_to_event_type` to sync-or-async
  with a documented inline-execution hazard. Tests: new `test_events_service.py`.
- #4 (commit `17b87936`): formatter now stores the resolved name on the record and
  references `{extra[_resolved_logger_name]}` instead of concatenating it. Test added to
  `test_logging_service.py` (bound name with `{...}`/`<red>` emitted literally).
- #2 (commit `25aa1074`): added `atomic_write_bytes` to `server/utils.py`; routed the
  repository metadata, user accounts and role permissions writers through it. Tests: new
  `test_server_utils.py` (happy path + original intact on replace failure).
- #1 (commit `54ff7367`): `password` marked `repr=False` on both account models;
  `log_secrets` flag added to `LoggingConfigModel` (default off) with `LoggingService.secret()`
  and a startup WARNING; JWT sub and the password-change log line routed through `secret()`;
  access token removed from `UserAccessTokenNotFoundError`. User docs added to
  `docs/server-usage/logging.md`. Tests: new `test_user_account_models.py`, added
  `secret()`/warning tests to `test_logging_service.py`. Note: the direct-interpolation
  password-change log line (`user_accounts_service.py`) was not in the plan's #6 repr list
  but is a real plaintext leak repr=False cannot cover, so it was gated too.

All Q1 low-complexity/high-gain items now implemented locally on `fix/code-review-fixes`
(not pushed). #6 remains on hold per the user. Tests/lint/pre-commit run green per commit.

---

## #8 Per-instance template binding

**Problem.** Template -> generator/listener bindings are written as CLASS attributes. Two templates
sharing one generator (or listener) class overwrite each other: last loaded wins, and every instance,
including ones created from the other template, reports the wrong template, agent/listener type and
compatible listener types. Breaks the user's "multiple templates as presets" model. Effects: update
validates against the wrong template's options (`agent_generators_service.py:335-366`,
`listeners_service.py:281-310`), built agents record the wrong `agent_template_id`
(`base_agent_generator.py:481-483`), wrong JSON, persistence plugins restore under the wrong template.

**Design (decided).** Each instance stores exactly one binding, its creating template. Everything
else is a read-only property derived from that template.

Framework (`consortium/framework/`):
- `agents/base_agent_template.py`
  - Delete `:159` `cls.agent_generator.creating_agent_template = cls()` (and its TODO at `:158`).
  - `create_agent_generator` (`:185`, construct at `:274`): construct, then
    `agent_generator.creating_agent_template = self`, then return it.
  - `to_json` `:298`: `self.agent_generator.agent_type.to_json()` -> `self.agent_type.to_json()`.
- `agents/base_agent_generator.py`
  - Add properties `agent_type` -> `self.creating_agent_template.agent_type` and
    `compatible_listener_types` -> `self.creating_agent_template.compatible_listener_types`.
  - Update the class docstring attributes (`:399-403`): "assigned during loading" -> set per
    instance by the creating template.
  - Existing instance reads stay as they are (`:481-483`, `:793-799`, `:813`).
- `listeners/base_listener_template.py`
  - `create_listener` (construct at `:302`): construct, set
    `listener.creating_listener_template = self`, return.
- `listeners/base_listener.py`
  - `:86-87` class annotations: keep `creating_listener_template` (instance attr), replace
    `listener_type` with a property -> `self.creating_listener_template.listener_type`.
    Existing reads at `:348,360,376` stay.

Server:
- `server/services/component_loader_services/agent_profile_loader_service.py:83-105`: delete the
  class writes at `:88` and `:97-100`. Keep: instantiate `agent_type` unless it is a `str`
  reference (`:95-96`), build `AgentProfile`.
- `server/services/component_loader_services/listener_profile_loader_service.py:79-91`: delete
  `:83` and `:86`. Keep `listener_type` instantiation (`:85`) and `ListenerProfile`.
- `server/services/c2_types_service.py:364-369`: delete `:369`
  (`agent_profile.agent_generator.agent_type = ...`); fix the comment above ("all three" -> the
  profile and template; the generator derives from the template).

All instantiation already goes through `create_agent_generator` / `create_listener` (callers:
`agent_generators_service.py:150,366`, `payloads_service.py:167,265,364,462,559`,
`listeners_service.py:137,310`). No constructor signature change.

`components/` check (user-authorized grep, 2026-09-24): only instance reads of
`.creating_*_template.label` in `plugins/persistent_agent_generators/plugin.py:99-106` and
`plugins/persistent_listeners/plugin.py:106-113`; both recreate via
`create_*_from_*_template_by_*_template_id` so they bind correctly. No generator/listener/type class
in components defines `__init__`. Nothing breaks.

Tests:
- Update `tests/services_tests/test_agent_type_references.py:98,133-134` and
  `tests/services_tests/test_c2_types_service.py:612` (they assert class-level bindings on
  `profile.agent_generator`; assert via the template or a created instance instead).
- Add regression: two templates sharing one generator class each create a generator; each instance
  reports its own `creating_agent_template`, `agent_type`, `compatible_listener_types`. Same for two
  listener templates sharing one listener class.

## #3 Component loader: one bad component must not abort startup

File: `consortium/server/services/component_loader_services/component_loader_service.py`.

- a. `_get_entry_point_from_manifest_json` (`:177-192`): after the `split(":", 1)`, require every
  `component_module.split(".")` part to satisfy `str.isidentifier()` (and the symbol too). Otherwise
  raise `self._component_exceptions.invalid_manifest_file_schema(component_directory=...,
  json_schema_error_message=...)` like the existing `:184` check. This keeps the resolved file inside
  the component dir lexically (no `/`, drive, `..`). No `.resolve()`: symlinked plugin dirs must keep
  working. User confirmed entry point modules must be valid identifiers.
- b. `_validate_component_directory_structure` `:295-297`: the `relative_to(self._consortium_root)`
  is outside any try. Catch `ValueError` and raise `entry_point_module_not_found` (component dir
  outside `consortium_root`, reachable via the un-routed public methods).
- c. Do NOT wrap `agent_type()` / `listener_type()`. Type classes with an `__init__` are not a
  supported framework feature (none exist in components). A violation is contained by (d).
- c2. Rename `_post_validate_component_object` -> `_assemble_component` in: base `:391` and caller
  `:445`; `agent_profile_loader_service.py:83`; `listener_profile_loader_service.py:79`. Update the
  base comment: it assembles the loaded object (profiles link + wrap it), it does not validate.
- d. `get_all_components_from_directory` batch loop (`:468-488`): add a final `except Exception as
  exc:` that records `(directory, self._component_exceptions.internal_error(
  component_directory=str(directory), internal_error_message=str(exc)))` so any unexpected error is
  per-component. The return type stays `list[tuple[Path, ComponentLoadingError]]`.

Tests: a manifest with `entry_point` `"/abs/path/mod:Sym"` / `"a..b:Sym"` / `"a-b:Sym"` is rejected
per-component; a batch scan where one component raises a plain `TypeError` still returns the others.

## #5 Delete the API catch-alls

Delete these six `except Exception as exc: raise InternalServerError(detail={"type": ...,
"message": str(exc)}) from None` blocks. **Keep** the `*FatalError` branch directly above each.
- `consortium/server/api/listeners_api.py:176` (start), `:227` (stop), `:276` (cancel)
- `consortium/server/api/agent_generators_api.py:188` (start), `:239` (stop), `:286` (cancel)

Why (traced with the user): `ComponentLifeCycle` (`framework/_core/components/component_life_cycle.py:
114-246`) already converts every component hook failure into Start/Stop/`*FatalError`, swallows
`on_fatal` failures, and the runtime loop is a background task. `BaseListener`/`BaseAgentGenerator`
overrides only call `super()`; the generator `stop()` build-step teardown only runs `@final` hooks.
So the catch-all only caught framework bugs. Without it they reach `server_middleware.py:173-189`
(traceback logged at ERROR, generic 500 body) after `log_and_propagate_error_on_service_method`
logs them CRITICAL. The server stays up.

## #7 Sync event handlers: accept and adapt

File: `consortium/server/services/events_service.py`, `trigger_event` `:217-220`.
Today `gather(*(h(event) for h in handlers))` runs sync handlers inline while building args (a raise
escapes before `gather` and aborts the whole fan-out) and `gather(None)` raises `TypeError`.

```python
async def _invoke_event_handler(event_handler, event: Event) -> None:
    result = event_handler(event)
    if inspect.isawaitable(result):
        await result
```
Use it in the `gather`. Keep `return_exceptions=True` and the result loop (`zip(event_handlers,
results)` still lines up). Update `register_event_handler_to_event_type` docstring/type hint (`:51-68`)
to accept sync or async callables and document the hazard: a sync handler blocks the event loop
while it runs, keep it quick or offload with `asyncio.to_thread`. No `iscoroutinefunction` check
(misrejects `functools.partial` of async fns and async `__call__` objects). No thread offload.
Tests: sync handler receives the event; a sync handler that raises does not stop sibling handlers
and appears in the `ExceptionGroup`.

## #4 Log-format injection

File: `consortium/server/services/logging_service.py:75-86` (formatter function).
`logger_name` is concatenated into the loguru format template, so `{}`/`<tag>` in a name are parsed.
Fix: in the formatter, `record["extra"]["_resolved_logger_name"] = logger_name` (any private key) and
use `"{extra[_resolved_logger_name]}"` in the template instead of concatenating. Keeps the existing
"no KeyError when no logger_name is bound" behaviour (the formatter always sets the key). The
`color` string is from a fixed map and may stay concatenated.
Test: a bound `logger_name` of `"{message} <red>x</red>"` is emitted literally.

## #2 Atomic JSON writes

Add one helper to `consortium/server/utils.py` (next to `wrap_filesystem_errors` `:104`), e.g.
`atomic_write_bytes(path, data: bytes)`: write `path.with_name(path.name + ".tmp")`, `flush()`,
`os.fsync()`, then `os.replace(tmp, path)`. Call it inside each site's existing error-wrapping
context so `OSError`s still map to the same domain errors:
- `consortium/server/services/repository_service.py:245-249` (`.repository.json`, text utf-8:
  pass `data.encode("utf-8")`; json is ASCII-only so the bytes are identical)
- `consortium/server/services/user_accounts_service.py:574-575` (already writes bytes; keep
  `number_of_bytes_written` for the log line, e.g. `len(encoded_data)`)
- `consortium/server/services/authorization_service.py:147-148` (text utf-8)

Decided: no `.bak` for 0.1.0 (atomic replace covers crash/partial writes; `.bak` needs fallback and
cleanup policy; revisit with the planned SQL move). A leftover `.tmp` after a crash is harmless and
is overwritten by the next save. Test: a failure during write leaves the original file intact.

## #1 Password / session-id redaction + `log_secrets`

Decisions: reprs are always redacted; deliberate secret logging is opt-in via config, default off.
Scope is passwords and the JWT `sub` only (generator/listener params are #6, on hold).

1. `consortium/server/models/user_account_models.py`: `password: str = Field(repr=False)` on
   `UserAccountModel` (`:9`) and `PersistentUserAccountModel` (`:27`, keep `min_length=1`). Pydantic
   drops it from `repr()`; no `SecretStr`, so compare/save code is untouched. This alone neutralizes
   every `{!r}` site, including `User.__repr__` (`server/objects/user_objects.py:70-71`) which reprs
   the account.
2. `consortium/server/models/logging_models.py:7-20`: add `log_secrets: bool = False` to the server
   `LoggingConfigModel` (not the client one). Loaded from `data/server/logging_config.json` via
   `start_server.py:81-91`; default off means the JSON needs no edit.
3. `consortium/server/services/logging_service.py`: add a small method, e.g.
   `secret(value) -> value if self.logging_config.log_secrets else "<redacted>"`. Services reach it
   via `server_singletons.logging_service` (`server/server_singletons.py:43`). In
   `configure_default_logging` (`:329-352`), log a WARNING when `log_secrets` is true.
4. `consortium/server/services/users_service.py:75-77`: log line prints the JWT `sub`
   (`access_token`) on every authenticated request; route it through `secret(...)`.
5. `consortium/server/exceptions/service_exceptions/users_service_exceptions.py:63-73`
   (`UserAccessTokenNotFoundError`): remove the `sub` from the message and `detail` entirely (not
   gated: exceptions travel beyond logs). Keep the constructor arg only if callers need it; callers
   are `users_service.py:79`.
6. Repr sites now safe via (1), no change needed unless a line exists only to dump the password:
   `user_accounts_service.py:93,112,303,334,375,675`; `users_service.py:56,76,157,185`. If you want
   passwords visible with `log_secrets`, add an explicit `secret(account.password)` field to the
   relevant debug line rather than removing `repr=False`.
Already clean, no change: encoded JWT, signing key, `Authorization` header, websocket tickets.
Tests: `repr(UserAccountModel(...))` has no password; `secret()` honours the flag.

## #6 On hold: generator build / listener params

User: build/listener params are a different domain from passwords and need their own treatment.
Do not implement. Sites for later: `agent_generators_service.py:374-388,424-433`;
`listeners_service.py` event/log sites; event `data` payloads.

## Backlog raised during triage (not scheduled)

- Q2-A password hashing: needs a migration decision (rehash-on-login vs one-shot). After hashing,
  plaintext exists only at login/password change, which narrows what #1's flag can show.
- Optional: enforce "type classes define no `__init__`" in `BaseAgentType`/`BaseListenerType`
  `__init_subclass__` (user has not asked for it).

---

## Q3 mop-up (implemented 2026-09-24, committed on `fix/code-review-fixes`)

All Q3 rows from `TRIAGE.md` actioned in one pass, on top of the Q1 commits. Nothing here is a
behaviour change an operator would notice except the plugin reload dedup, which previously never
matched.

| Item | Finding | Change |
|---|---|---|
| Plugin reload dedup | C-reverify med | `plugins_service.py` reload rescan: `plugin.root_directory.parent == path.parent` -> `plugin.root_directory.is_relative_to(path.parent)`. `root_directory` is the entry point module's folder, so the old test compared the *plugins* dir against the *plugin* dir and never matched; a plugin that failed to unload was loaded a second time. `is_relative_to` also covers an entry point in a subpackage. |
| Events two-index order | H med | `events_service.register_event_handler_to_event_type` now updates `_handler_event_types` (the step that hashes the handler, the only one that can fail) before appending to `_event_handlers`, so an unhashable handler leaves both structures untouched. Note: the finding's bound-method premise does not hold on 3.14, which hashes a bound method by its `__self__`'s address; a directly unhashable callable still raises. |
| Facade "not an isolation boundary" | G low | Comment added at the top of `AgentFileManagerService.__init__` and `AgentTemplatesPayloadsService.__init__`. No scoping checks, per the authorization model. |
| Tar extraction filter | D low | `repository_objects._archive_extraction_filter()` passes `filter="data"` to `shutil.unpack_archive` for every tar format and nothing for zip. Verified against the project interpreter: the zip unpacker's signature is `(filename, extract_dir)` and takes no `filter`, so passing one unconditionally would be a `TypeError`. |
| UUID helper consolidation | B low | The two identical `_canonicalize_uuid` copies (`tasks_service`, `task_runtime_service`) are now one `canonicalize_uuid` in `server/utils.py`. **Deferred:** making `normalize_uuid` itself canonicalize. It is called from ~25 sites across 12 services with identifiers that are not always UUIDs, its result is used as a dict key and in error message text, and changing it would turn some current 404s into hits. That is a cross-service behaviour decision, not a mop-up. |
| `create` vs `add` dup-id guard | G low | `create_agent_generator_from_agent_template_by_agent_template_id` now raises `AgentGeneratorAlreadyExistsError` on a colliding ID, matching `add_agent_generator`; docstring `Raises:` updated. |
| `AGENT_CHECKED_IN` ordering | B low | `agents_service.check_in_agent_by_agent_id` updates `datetime_last_checked_in` and `mark_as_active()` before building the event payload, so subscribers no longer see the previous check-in. |
| Caller-dict mutation | F/G low | `update_agent_generator_by_agent_generator_id` and `update_listener_by_listener_id` resolve the back-filled parameter set into a local `resolved_parameters` instead of writing into the caller's dict; the no-op self-assignment in each validation loop is gone. |
| Service decorator | G low | `AgentFileManagerService` gained `_logger`, `__str__`, `__repr__` and `@log_and_propagate_error_on_service_method` on all nine public methods, matching every sibling service. Nested double-logging with the inner services is the existing pattern across the codebase, not new here. |
| Upload `None` name | E low | **No change: non-issue.** `create_asset_file` and `create_asset_directory` both declare and document `name: str | None = None` -> "the asset's generated UUID is used as its name". The reviewer flagged this as low confidence pending exactly this check. |

Tests added (13 cases across 3 modified and 3 new files):
- `tests/services_tests/test_plugins_service.py`: three reload-dedup cases (failed-to-unload skipped,
  nested entry point skipped, cleanly-unloaded reloaded).
- `tests/services_tests/test_events_service.py`: unhashable handler leaves both indices untouched;
  duplicate registration still rejected.
- `tests/services_tests/test_repository_objects.py`: escaping tar member raises
  `tarfile.OutsideDestinationError`; absolute member is contained under the destination (the data
  filter strips the separator rather than raising); well-formed tar and zip still unpack.
- `tests/services_tests/test_update_does_not_mutate_caller_parameters.py` (new): both update methods
  leave the caller's dict alone while still resolving the full set onto the object.
- `tests/services_tests/test_agents_service_check_in.py` (new): emitted payload carries the new
  timestamp; `mark_as_active` lands before `to_json`.
- `tests/services_tests/test_agent_generators_service.py` (new): `create` rejects a colliding ID and
  keeps the live generator; a fresh ID still registers.

Verified 2026-09-24: `uv run pytest` green (1288 passed, 63 subtests), `uv run ruff check consortium`
clean, `ruff format` applied to the three modified test files, and pre-commit passed on every commit.
Landed as nine commits, one per row above, starting at the `q3-low-complexity-low-gain-start` tag.

Note: `ruff check .` cannot parse `tests/services_tests/mocks/plugins/mock_plugin_bad_toml/pyproject.toml`
(deliberately malformed fixture), so lint the `consortium` package directly, per AGENTS.md. Two files
outside this change (`framework/utils/network_utils.py`, `component_loader_service.py`) carry
pre-existing `ruff format` drift and were left alone.
