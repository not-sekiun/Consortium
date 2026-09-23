# G-agentgen — Agent generation / templates / profiles / file manager

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high. Files: agent_generators_service.py, agent_profiles_service.py, agent_templates_payloads_service.py, agent_file_manager_service.py, agent_templates_service.py.

Trust/scope note: agent_templates_payloads_service.py and agent_file_manager_service.py are thin facades over `payloads_service` / `assets_service` / `artifacts_service`. The arbitrary-source-path move/copy (path traversal), unbounded upload/archive-bomb DoS, non-atomic metadata writes, and the generic per-resource IDOR are already reported in **D-files** and are NOT re-reported here except where a facade adds a distinct, in-file defect. Component-loader / entry-point / directory-scan issues that `agent_profiles_service` delegates into are covered in **C-codeloading**.

## Findings

### [SEV: med] Agent profile is registered and started before its type references are resolved, with no rollback and resolve-time errors uncaught by the batch loader (partial/inconsistent state, startup abort)
- **File:** agent_profiles_service.py:204-209 (`load_agent_profile`), 442-452 (`load_framework_agent_profiles` per-profile catch set), also 263-281 / 365-384 (same register-then-resolve order in the from-directory and reload paths)
- **Category:** error-handling
- **What:** `load_agent_profile` first calls `load_component` (which registers AND starts the profile) and only afterwards calls `server_singletons.c2_types_service._resolve_agent_type_references()` / `_resolve_registered_compatible_agent_types_for_listener_profiles()`. If resolution raises (`DuplicateAgentTypeNameError`, `UnresolvableAgentTypeReferenceError`, or the `TypeError` from a string ref that resolves to a profile — all documented in the docstrings), the profile is left registered and started but the reference graph is half-resolved, and nothing is rolled back. In `load_framework_agent_profiles` the per-profile `except` only catches `(AgentTemplatesFrameworkError, AgentProfilesServiceError)` (447-450), so these resolution exceptions are not caught: they abort the entire loop.
- **Failure scenario:** One profile among many on disk declares an agent-type name that collides with, or references, another profile. At startup the loop loads profiles 1..N-1, registers+starts profile N, then `_resolve_agent_type_references()` raises; the exception unwinds out of `load_framework_agent_profiles`, aborting startup (or the reload) with profile N registered-but-unresolved and profiles N+1.. never loaded. A single bad profile thus poisons the whole set instead of being reported as one failed profile.
- **Fix:** Resolve references (or at least validate the name/reference) before committing/starting the profile, and roll back (unload) the just-loaded profile if resolution fails; add the resolution exception types to the per-profile catch set so one profile's failure is collected as a per-profile error rather than aborting the batch.

### [SEV: med] Template-scoped payloads facade does not scope reads/deletes to its bound template (cross-template IDOR / false scoping)
- **File:** agent_templates_payloads_service.py:100-108 (`create_payload_file` injects `self._agent_template_id`), 302-323 (`delete_payload_by_payload_id`), 325-331 (`get_payload_by_payload_id`), 333-337 (`get_all_payloads`)
- **Category:** perms
- **What:** The facade is constructed bound to a single `agent_template_id` and dutifully injects it on every *create* path, presenting itself as a per-template view. But `delete_payload_by_payload_id`, `get_payload_by_payload_id`, and `get_all_payloads` forward the raw id straight to `PayloadsService` with no check that the target payload's `agent_template` matches the bound template. `get_all_payloads` returns every payload in the repository regardless of template.
- **Failure scenario:** Agent-template code holding one template's payloads facade calls `delete_payload_by_payload_id(other_templates_payload_id)` (or enumerates via `get_all_payloads`) and reads/deletes another template's payloads. The binding gives a false sense of isolation that the read/delete methods do not honour.
- **Fix:** Filter `get_all_payloads` to the bound template, and verify `payload.agent_template` matches `self._agent_template_id` before returning/deleting by id (raise not-found otherwise); or document explicitly that this facade is not an isolation boundary. (See D-files for the underlying service-level IDOR.)

### [SEV: med] Agent generator build parameters (potential secrets) are logged at INFO and broadcast in the update event payload
- **File:** agent_generators_service.py:374-377 (full old/new parameter sets placed in event `data`), 383-388 (per-field old/new values logged at INFO), 424-433 (`AGENT_GENERATOR_UPDATED` emitted with that data); comparable exposure in the create/add flows via `to_json()` at 163/204
- **Category:** info-leak
- **What:** On parameter update the complete old and new parameter dicts are deep-copied into the event `data` (broadcast to all event subscribers via `events_service.trigger_event`), and each changed parameter's old and new value is written to the INFO log. Build parameters for agent generation in a C2 commonly carry sensitive material (encryption keys, tokens, callback hosts/credentials). Nothing here redacts by field sensitivity.
- **Failure scenario:** An operator updates a generator's key/credential parameter; the plaintext old and new values land in the server log and in an event delivered to every connected client, widening exposure beyond the caller.
- **Fix:** Log parameter *names* changed, not values; redact or omit sensitive parameter values from event `data` (or let the template mark options as secret and honour that when building log/event payloads).

### [SEV: low] `update_agent_generator_by_agent_generator_id` mutates the caller-supplied `parameters` dict in place
- **File:** agent_generators_service.py:325-329 (back-fills missing keys into the caller's `parameters`), 352 (redundant self-assignment)
- **Category:** design
- **What:** The method back-fills missing keys by writing them into the caller's `parameters` argument (`parameters[parameter_name] = copy.deepcopy(...)`), so the caller's dict is silently expanded from a partial update into the full resolved set. If the caller reuses or logs that dict it now contains fields it never supplied (including other parameters' values). Line 352 (`parameters[parameter_name] = parameter_value`) is a no-op self-assignment.
- **Failure scenario:** A caller passes a request-derived dict expecting only its own keys, then logs/re-sends it; it now carries back-filled values (possibly secrets) it did not intend to handle.
- **Fix:** Build the resolved set in a local copy (`resolved = {**existing, **parameters}` or deep-copy first) and never mutate the argument; drop the dead line 352.

### [SEV: low] `create_agent_generator_from_agent_template...` silently overwrites an existing entry on ID collision (inconsistent with `add_agent_generator`)
- **File:** agent_generators_service.py:155-157 (unconditional dict assignment) vs 191-194 (`add_agent_generator` raises `AgentGeneratorAlreadyExistsError` on collision)
- **Category:** error-handling
- **What:** `create` writes `self._agent_generators[str(id)] = agent_generator` with no membership check, whereas `add` guards against a duplicate id. IDs are template-generated UUIDs so collision is unlikely, but the two registration paths enforce different invariants; a colliding/reused id would silently replace a live generator (orphaning it while still referenced) rather than being rejected.
- **Fix:** Apply the same duplicate-id guard in `create` as in `add`, or factor the insert into one helper used by both.

### [SEV: low] `AgentFileManagerService` methods lack the `log_and_propagate_error_on_service_method` decorator used by every sibling service
- **File:** agent_file_manager_service.py:28-319 (all public methods; none decorated), contrast agent_generators_service.py / agent_profiles_service.py / agent_templates_service.py where every service method carries the decorator
- **Category:** error-handling
- **What:** Unlike the other services in scope, no method here is wrapped by `log_and_propagate_error_on_service_method`, so exceptions raised on this agent-facing facade (including unhandled/non-domain ones) are not run through the standard critical-logging path. Errors from agent-driven file operations pass through unlogged at the service boundary.
- **Failure scenario:** An agent triggers an unexpected exception via `create_artifact_file` / `add_artifact_directory`; it propagates without the service-level critical log the rest of the codebase relies on for post-hoc diagnosis.
- **Fix:** Apply the decorator consistently, or document why this facade deliberately opts out.

### [SEV: low] Agent file-manager facade grants each agent unscoped read of all assets and all artifacts
- **File:** agent_file_manager_service.py:28-34 (`get_all_assets`), 55-61 (`get_all_artifacts`), 82-145 (`read_asset_by_asset_id`), 63-80 (`get_artifact_by_artifact_id`)
- **Category:** perms
- **What:** The facade is bound to a single owning agent and attributes *writes* to it, but every read (`get_all_assets`, `get_all_artifacts`, `read_asset_by_asset_id`, `get_*_by_*_id`) returns any resource regardless of producing agent. Any agent's component code can enumerate and read every other agent's assets/artifacts by id.
- **Failure scenario:** Agent X reads artifacts produced by agent Y (or the full asset pool) that it should not see, by id or via the list methods.
- **Fix:** If cross-agent visibility is intended, document it; otherwise scope reads by the owning agent's attribution. (Underlying service-level IDOR is in D-files; this notes the agent-facing facade specifically presents no isolation.)

## Design notes
- **Private cross-service reach-in, repeated 5x.** `agent_profiles_service` calls `server_singletons.c2_types_service._resolve_agent_type_references()` and `._resolve_registered_compatible_agent_types_for_listener_profiles()` (207-208, 278-279, 305, 380-381) — reaching into another service's underscore-private methods from five sites. Expose a single public "reconcile agent types" method on `c2_types_service` and call that once; it removes the leaked private coupling and the copy-paste.
- **`update` no-op self-assignment.** agent_generators_service.py:352 assigns a value back onto itself inside the validation loop; delete it.
- **`agent_templates_service` lookups build a full list for a single hit.** get_agent_template_by_agent_template_id (58-61) and get_agent_template_by_label (88-91) materialize a list comprehension over every profile's template, then iterate; a generator would short-circuit on first match. Also duplicate labels resolve to first-match with no detection — mirrors the duplicate-label ambiguity flagged in C-codeloading; worth a consistency pass.
- **`create` vs `add` duplication.** The two registration paths (agent_generators_service.py:150-157 and 191-198) plus their event-emit boilerplate could share one insert helper, which is also the natural place to make the duplicate-id guard uniform (low finding above).

## Notes
- The unbounded content/archive DoS, arbitrary source-path move/copy (path traversal), and non-atomic metadata persistence reachable through `agent_templates_payloads_service.create_payload_*/add_payload_*` and `agent_file_manager_service.create_artifact_*/add_artifact_*` are the same defects reported in **D-files** (payloads_service / artifacts_service / repository_service); not re-scored here. These facades forward `path`, `content`, `payload_data`, `chunk_size`, and `encoding` through unvalidated, so any hardening added at the service layer covers them.
- `read_asset_by_asset_id` forwards `chunk_size` and `encoding` to `asset.read` without validating them (e.g. non-positive `chunk_size`, unknown `encoding`); behaviour then depends on the repository object layer. Docstring documents the expected `LookupError`/`UnicodeDecodeError`, so treated as deferred to the object layer rather than a service defect — worth a human confirming `chunk_size <= 0` is handled sanely downstream.
- All event emissions use fire-and-forget `run_async_background_task` (agent_generators_service.py:159-165 etc.), which calls `asyncio.create_task` and requires a running loop; the sync `create`/`add`/`update` methods would raise `RuntimeError` if ever called outside an event loop. This is a cross-cutting pattern across services (see H-events); noted, not scored here.
- `agent_profiles_service` is documented (line 32-34) as internal-only and not exposed on the external REST API, which bounds the exposure of its arbitrary-`directory` parameters; if a profile-management route is ever added, the `directory` inputs need `is_relative_to(agents_directory)` confinement (parallels the C-codeloading note).
