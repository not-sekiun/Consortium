# F-listeners — Listener subsystem (network-facing listener lifecycle, profiles, templates)

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high. Files: listeners_service.py, listener_profiles_service.py, listener_templates_service.py.

## Findings

### [SEV: med] `reload_framework_listener_profiles` unloads everything then reloads with no rollback
- **File:** listener_profiles_service.py:442-454 (also unload half 419-439, load half 357-416)
- **Category:** error-handling
- **What:** Reload is implemented as "unload all framework profiles, then load all framework profiles" with no snapshot/rollback. If the load half raises (documented `ListenerProfileDiscoveryFileSystemError`, or any per-profile fatal that escapes — see next finding), the server is left with zero framework listener profiles even though it had a working set a moment earlier.
- **Failure scenario:** An operator triggers a reload while the listeners directory is briefly unreadable (permission blip, directory renamed mid-scan). `unload_framework_listener_profiles()` succeeds and removes every profile; `load_framework_listener_profiles()` -> `get_all_listener_profiles_from_directory()` raises `ListenerProfileDiscoveryFileSystemError`. The reload aborts with all profiles gone. Because `ListenerTemplatesService` derives every template from the loaded profiles (listener_templates_service.py:59-62,92-95,114-117), listener creation now fails with `ListenerTemplateIDNotFoundError` until the process is restarted or a manual reload succeeds.
- **Fix:** Capture the currently-loaded profiles (or their directories) before unloading and, on load failure, restore them; or load-then-swap rather than unload-then-load. At minimum document the "empty on failure" outcome and log a prominent error. (Related to C-codeloading's registry-level "reload has no rollback", but this is the distinct service-orchestration site.)

### [SEV: med] `load_framework_listener_profiles` catches only two exception types; anything else aborts loading of all remaining profiles
- **File:** listener_profiles_service.py:397-407 (per-profile loop) with load_listener_profile:194-200
- **Category:** error-handling
- **What:** The per-profile load loop only catches `ListenerTemplatesFrameworkError` and `ListenerProfilesServiceError`. But `load_listener_profile` also calls `server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles(...)` after registering the component (line 197-199). Any exception from that call, or any non-domain exception (e.g. `AttributeError` if the singleton is not yet wired, or an error raised while iterating agent profiles in c2_types_service.py:308-316), is not caught and aborts the entire loop.
- **Failure scenario:** During startup one profile registers successfully, then compatible-agent-type resolution raises an unexpected error. The loop terminates: every profile after it in `retrieved` is silently never loaded, and the "loaded N / failed M" summary at 409-416 is never reached, leaving the server in a partially-loaded, inconsistent state with no clear signal of which profiles were dropped.
- **Fix:** Wrap the per-profile body in a broad `except Exception` that increments `failed_to_load` and logs, so one profile's failure cannot abort the rest; keep the resolve step inside that guarded region.

### [SEV: med] Unbounded listener registry and no cap on listener creation (resource/memory DoS)
- **File:** listeners_service.py:42, 94-153 (insert at 142)
- **Category:** dos
- **What:** `self._listeners` is an in-memory dict with no upper bound and `create_listener_from_listener_template_by_listener_template_id` performs no count/quota check. Listeners are network-facing; each created (and later started) listener can hold sockets/ports/file descriptors.
- **Failure scenario:** Any authorized caller loops the create endpoint, accumulating unbounded listener objects (memory), and by starting them can exhaust ephemeral ports / FDs on the host. Nothing reclaims them except explicit removal.
- **Fix:** Add an optional server-side ceiling on registered listeners (parameterized, default off per the repo's "limits are policy at the boundary" philosophy) enforced in the create path, mirroring the event-log clamp pattern already in utils. (Same class as B-runtime's unbounded-agent-registration finding; distinct resource and site.)

### [SEV: low] Full listener parameters broadcast in every lifecycle event and written to logs
- **File:** listeners_service.py:144-149, 414-420, 455-461, 496-502 (event `data=listener.to_json()`) and repr logs at 151, 211, 328, 339, 357, 422, 463, 504
- **Category:** info-leak
- **What:** Every listener lifecycle event carries `listener.to_json()`, which includes the full `parameters` dict (base_listener.py:349), and every `self._logger.debug("- {!r}", listener)` renders `__repr__` including `parameters` (base_listener.py:197). If a listener template exposes sensitive options (auth tokens, TLS private material, shared keys for the C2 channel), those values are emitted to every event subscriber and into log sinks.
- **Failure scenario:** An operator with only event-subscribe access (see A-auth: "any operator can subscribe to every event type") receives `LISTENER_CREATED`/`LISTENER_UPDATED` events containing secret parameters they should not see; the same secrets land in plaintext logs.
- **Fix:** Redact or omit option values flagged sensitive when serializing for events/logs (e.g. a `sensitive` marker on options honored by `to_json`/`__repr__`), or scope event payloads. Confidence is conditional on listener components defining secret-bearing options (components not in review scope).

### [SEV: low] `update_listener_by_listener_id` mutates the caller-supplied `parameters` dict and re-validates redundantly/incompletely
- **File:** listeners_service.py:259-312 (back-fill 273-277; manual validation 280-297; re-creation 310)
- **Category:** error-handling
- **What:** The method back-fills missing keys into the caller's `parameters` argument in place (273-277), a side effect on the caller's object. It then hand-rolls per-option validation (280-297) that duplicates what `create_listener` already does at 310 but is incomplete: it never runs the template's `validating_function` (cross-field validator). Cross-field failures therefore surface from `create_listener` as exception types (`ListenerTemplateValidatingFunctionError`, `ListenerTemplateOptionValueValidationError`) not listed in the method's `Raises:` docstring (240-247).
- **Failure scenario:** A caller passes a dict whose individual values are valid but whose combination is rejected by the template validator; the method passes its own checks, then `create_listener` raises an undocumented exception. State stays consistent (mutation happens only at 313+ after temp creation), but the caller's `parameters` dict has been silently altered and the raised type differs from the contract.
- **Fix:** Operate on a local copy of `parameters`; drop the duplicate manual validation loop and rely on `create_listener` (build the temp listener first, translate its errors into `InvalidListenerParameter*` as documented). This also removes ~20 lines.

### [SEV: low] Profiles service reaches into another service's private method via a module-global singleton
- **File:** listener_profiles_service.py:197-199, 262-264, 350-352
- **Category:** design
- **What:** Three code paths call `server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles(...)` — a `_`-prefixed private method reached through a module global rather than an injected dependency. This is a layering violation (the service takes `release_service`/`paths_service` by DI but not `c2_types_service`) and a latent crash: if `server_singletons.c2_types_service` is unset/None during early init or in tests, these raise `AttributeError` from inside otherwise-normal load paths.
- **Failure scenario:** A profile is loaded before `c2_types_service` is assigned on the singletons module -> `AttributeError` escapes `load_listener_profile` and (per the narrow-catch finding above) can abort framework loading.
- **Fix:** Inject `c2_types_service` (or an interface exposing a public resolve method) and call it through the reference; expose a public method instead of the `_`-prefixed one.

### [SEV: low] No per-listener ownership/authz — any authorized caller can act on any listener
- **File:** listeners_service.py:184-211 (remove), 213-383 (update), 385-424 (start), 426-465 (stop), 467-506 (cancel)
- **Category:** perms
- **What:** Listeners carry no owner/principal, and every mutator resolves purely by ID with no ownership or role scoping at the service layer. Any caller that reaches these methods can update, start, stop, cancel, or remove any listener created by anyone.
- **Failure scenario:** In a multi-operator deployment, operator B stops/removes/reconfigures operator A's listener (IDOR-shaped), disrupting active C2 channels.
- **Fix:** If multi-tenant isolation is intended, attach an owner and enforce it (or enforce at the API boundary via AuthorizationService). If single-team-trust is the intended model, document it. (Same class as D-files' "no per-resource ownership/authz" note.)

## Design notes
- `add_listener` emits `LISTENER_ADDED` (174-180) *before* inserting into `self._listeners` (181), whereas create (142 then 143) and remove (202 then 203) insert/pop before emitting. Harmless today because `add_listener` is synchronous and the background event task runs only after it returns, but the asymmetry is a trap if the method ever gains an `await` before line 181. Make ordering consistent (mutate then emit).
- `create_listener_from_listener_template_by_listener_template_id` does `self._listeners[str(listener.listener_id)] = listener` (142) with no duplicate check, unlike `add_listener` (169-172). A listener-id collision would silently overwrite. Improbable with UUIDs, but the inconsistency is worth aligning.
- `listener_templates_service` rebuilds a full list comprehension over all profiles on every `get_*` call (59-62, 92-95, 114-117), an O(profiles) scan per lookup with no index. Fine at current scale; a name/id->template map would simplify and speed lookups. Duplicate template labels/ids across profiles resolve to "first match" silently (related to C-codeloading's duplicate-label note).
- `update_listener_by_listener_id` raises `ListenerAlreadyRunningError` even for a `parameters={}` no-op update (266-269 runs before the equality short-circuit at 299). Consider computing the no-op case first.

## Notes
- Non-canonicalizing UUID handling recurs here: `normalize_uuid` is `str(value)` (utils.py), so `listeners_service.get_listener_by_listener_id` (71-76, dict keyed by `str(listener_id)`) and `listener_templates_service.get_listener_template_by_listener_template_id` (57-72) will miss a real object if the client passes the same UUID with different casing/braces. This is the same root cause already reported in B-runtime ("Agent lookup uses non-canonicalizing normalize_uuid"); flagged here only as additional affected sites, not a new finding.
- Registry/loader-level issues (entry_point path traversal, load-path TOCTOU, per-component reload rollback, discovery scan cost) live in `component_registry_services`/`component_loader_services`, which these files delegate to; already covered in C-codeloading. Not re-reported.
- `unload_framework_listener_profiles` uses `root_directory.resolve().is_relative_to(self._listeners_directory.resolve())` (429-431): a profile whose `root_directory` is a symlink resolving outside the framework listeners dir would be skipped by the framework-unload sweep. Edge case; left for a human to judge against the intended profile layout.
