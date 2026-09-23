# H-events — Event core + hooks

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high. Files: event_hooks_service.py, events_service.py.

Threat model: authenticated operators may be hostile; remote agents fully untrusted. Supporting files
read only to confirm in-scope concerns: framework/event_hooks/_event.py, event_type.py, base_event_hook.py,
component_registry_service.py, server/utils.py, agents_service.py, server.py, and the api/ tree (to check
REST exposure). All findings below are about the two in-scope files. A-auth already covered the websocket
broadcast/subscription side (any operator receives every event); that perms issue is not re-reported here.

## Findings

### [SEV: med] Handler registration is not atomic across the two indices; an unhashable handler diverges the "can never diverge" invariant
- **File:** consortium/server/services/events_service.py:74-80 (register); consequence at :109
- **Category:** error-handling
- **What:** `register_event_handler_to_event_type` appends the handler to `_event_handlers` (:77 / :79)
  *before* updating the reverse index `_handler_event_types` (:80). The `setdefault(event_handler, ...)`
  at :80 hashes the handler, which raises `TypeError` if the handler (a bound method keyed on its
  `__self__`) is unhashable. When it raises, the handler is already in `_event_handlers` but never enters
  the reverse index, so the two structures diverge, directly contradicting the class comment that they are
  "kept in lockstep ... so the two can never diverge" (:29-37).
- **Failure scenario:** A handler whose `__self__` is unhashable (a hook/component that defines
  `__eq__` without `__hash__`, or otherwise sets `__hash__ = None`) is registered. `register` raises
  `TypeError` but leaves the handler in `_event_handlers[event_type]`; it now receives events yet is
  invisible to `get_event_types_from_registered_event_handler` / `subscribed_event_types`. A later
  `deregister_event_handler_from_event_type` removes it from the list (:105) then hits
  `self._handler_event_types[event_handler]` at :109 with a raw, unhandled `KeyError` (not the intended
  `EventHandlerNotRegisteredError`).
- **Fix:** Compute/reserve the reverse-index entry first (or validate hashability up front), then mutate
  `_event_handlers`, so a failure leaves both untouched. Alternatively wrap the two mutations so a failure
  rolls back the list append.

### [SEV: med] A mis-registered non-async handler defeats the documented per-handler failure isolation and escapes as a raw exception
- **File:** consortium/server/services/events_service.py:217-220 (gather); registration lacks a guard at :50-80
- **Category:** crash
- **What:** `trigger_event` builds the gather arguments with `event_handler(event)` inside a generator
  (:218). For a real `async def` handler this only creates a coroutine, so body errors surface during
  `await` and are isolated by `return_exceptions=True`. But registration never checks
  `inspect.iscoroutinefunction`, so a handler registered as a plain `def` (or any callable that runs
  synchronously) is invoked at argument-construction time. If it raises synchronously the generator raises
  while gather is materializing its args, and if it returns a non-awaitable `asyncio.gather` raises
  `TypeError`. Either way the *entire* fan-out for that event type is aborted and the error propagates out
  of `trigger_event` as a bare exception rather than the promised `ExceptionGroup`, breaking the failure
  isolation the docstring (:167-196) sells.
- **Failure scenario:** A hook author forgets `async` on `on_triggered`, or a future handler is a sync
  callable. It registers without complaint. The next trigger of that event type runs the sync handler
  during gather setup; it raises (or returns `None`), and every *other* correctly-written handler for that
  event never runs. Because emission is fire-and-forget (`run_async_background_task`), the failure is a raw
  exception logged as a critical unhandled error, and siblings are silently dropped for that trigger.
- **Fix:** Validate `inspect.iscoroutinefunction(event_handler)` (or that it returns an awaitable) at
  `register_event_handler_to_event_type` and reject non-async handlers with a typed error. Optionally wrap
  each `event_handler(event)` call so a synchronous raise is captured as a per-handler result too.

### [SEV: low] `get_registered_event_handlers_from_event_type` leaks the live internal list by reference
- **File:** consortium/server/services/events_service.py:128-133
- **Category:** design
- **What:** On a hit the method returns `self._event_handlers[str(event_type)]` (:129) — the actual
  mutable internal list — while the miss path returns a fresh `[]` (:133). A caller that mutates the
  returned list (append/remove) silently corrupts dispatch state and desyncs it from
  `_handler_event_types`, the exact divergence the class is built to prevent. No current in-tree caller
  mutates it (the method is unused elsewhere), so this is latent rather than live.
- **Failure scenario:** A future caller does `handlers = svc.get_registered_event_handlers_from_event_type(t); handlers.clear()`
  intending a local copy; it instead unregisters every handler for `t` from the reverse index's point of
  view without cleaning `_handler_event_types`, leaving a permanent inconsistency.
- **Fix:** Return `list(self._event_handlers.get(str(event_type), ()))` so both paths hand back a copy.

### [SEV: low] Unbounded, un-throttled concurrent fan-out; untrusted-agent-driven events amplify one action into N concurrent handler runs
- **File:** consortium/server/services/events_service.py:197-220 (trigger_event); driven e.g. from agents_service.py:174-180
- **Category:** dos
- **What:** `trigger_event` dispatches all handlers at once via `asyncio.gather` with no cap on concurrency
  and no backpressure, and separate triggers each spawn an independent fire-and-forget task. Events such as
  `AGENT_REGISTERED` / `AGENT_CHECKED_IN` / `AGENT_DEREGISTERED` are emitted from actions that fully
  untrusted remote agents drive at an attacker-chosen rate. Each such action amplifies into one concurrent
  invocation per registered handler (hooks + every subscribed websocket sender), each of which may itself
  do I/O (a websocket send).
- **Failure scenario:** A remote agent floods registrations/check-ins; every one enqueues a background
  `trigger_event` that fans out to all handlers concurrently, multiplying the load by the number of
  subscribers and accumulating unbounded background tasks and per-handler work.
- **Fix:** Per the repo's "limits are policy at the boundary" philosophy this belongs at the agent-facing
  API, but the amplification originates here: consider an optional concurrency bound / semaphore parameter
  on dispatch, and rate-limit agent-driven emission at the ingress that owns the agent identity.

### [SEV: low] No service-level authorization on hook lifecycle or event triggering; attacker-influenced event data forwarded unfiltered
- **File:** consortium/server/services/event_hooks_service.py:182-266 (register/load), 604-625 (trigger_event)
- **Category:** perms
- **What:** `register_event_hook*`, `load_event_hook*`, `reload_*`, `unload_*` and `trigger_event` perform
  no caller authorization and no validation of the event contents they forward; `trigger_event` lets any
  caller emit *any* `EventType` with an arbitrary `message`/`data` to every registered hook and subscriber
  (event spoofing, e.g. a fabricated `AGENT_DELETED` / `USER_LOGGED_IN`). The forwarded `data` also carries
  unsanitized untrusted agent-supplied fields (hostname, `agent_data`, `remote_ip` via `agent.to_json()`)
  straight into every hook's `on_triggered` and every subscriber. This is currently mitigated: no REST/API
  route calls these methods (hooks are loaded from the trusted framework directory at startup), so the
  attack surface is internal only.
- **Failure scenario:** If any of these methods is later exposed to operators over the API without an authz
  gate, a low-privilege operator could load/unload hooks or spoof arbitrary events; and any hook that
  renders/logs/`eval`s/shells out on event `data` becomes an injection sink fed by untrusted agents.
- **Fix:** Decide and document the trust boundary: if these ever reach the API, gate them with a
  permission and validate `event.event_type`; keep event payloads treated as untrusted data by hook
  authors (document the hazard, per the framework's stated philosophy).

## Design notes
- **Empty handler lists are never pruned from `_event_handlers`.** `deregister_event_handler_from_event_type`
  deletes the reverse-index key when its set empties (:111-112) but leaves an empty `[]` behind under the
  event-type key in `_event_handlers` (:105). Harmless (bounded by the ~36 `EventType` members and skipped
  correctly by `trigger_event`), but it is an asymmetry with the reverse index and worth a `del` for
  consistency.
- **`deregister` does not validate the event type** the way `register` does (`EventType(event_type)` at
  :70). An invalid type just yields `EventHandlerNotRegisteredError` via the `KeyError` path. Minor
  inconsistency, not a security issue.
- **`event_hooks_service.trigger_event` is a thin pass-through** to `events_service.trigger_event`
  (:620-625) and re-documents the same `ExceptionGroup` contract; fine, but the two docstrings must be kept
  in step by hand.

## Notes
- Dynamic import / instantiation of hook code from directories (`*_from_directory` paths) is delegated to
  `EventHookLoaderService` / `EventHookRegistryService`, which are out of scope here and belong to the
  code-loading review (C-codeloading). No code in the two in-scope files does `eval`/`exec`/`subprocess`
  or unsafe deserialization directly.
- The `trigger_event` snapshot (`list(self._event_handlers[...])` at :210) correctly defends against a
  handler deregistering itself mid-dispatch; the ExceptionGroup classification in
  `is_domain_error`/`_log_background_task_error` (server/utils.py) correctly handles the group when
  emission is fire-and-forget. Both are sound — no finding.
- `unload_framework_event_hooks` iterates a copy (`get_all_components` returns `list(...)`), so mutating
  the registry during unload is safe; `is_relative_to(...resolve())` means a hook whose `root_directory`
  is a symlink out of the hooks dir would be skipped by the framework unload — edge case, not pursued.
