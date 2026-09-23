# B-runtime — Agent / task runtime

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high.

Files:
- consortium/server/services/task_runtime_service.py (190 LOC)
- consortium/server/services/tasks_service.py (346 LOC, reviewed on-disk / uncommitted state)
- consortium/server/services/connected_agents_service.py (475 LOC)
- consortium/server/services/agents_service.py (673 LOC)

Trust boundaries traced: operator issue (`AgentsService.task_agent_by_agent_id` -> `Agent.submit_task`) -> queue/dispatch (`TaskRuntimeService`, per-task in/out queues) -> agent (results via `dispatch_task_output_message`) -> retrieval (`TasksService.get_*` / drain APIs). The only ownership check inside these four files is *listener* scoping in `ConnectedAgentsService` and *agent* scoping inside the `Agent` object; there is no operator/object-level ownership here (delegated to the API's flat RBAC). Per-task queues are bounded (`QUEUE_MEMORY_LIMIT`), but agent count, task count and runtime maps are not.

## Findings

### [SEV: med] Global terminal-task retention cap lets one agent evict another agent's task records/results
- **File:** tasks_service.py:208-237 (`_prune_terminal_tasks`), 285-292 (`_register_task` calls it), 296-346 (`_error_pending_tasks_for_agent` calls it)
- **Category:** dos
- **What:** `max_retained_terminal_tasks` is a single global bound across all agents and operators. When exceeded, `_prune_terminal_tasks` sorts *all* terminal tasks by completion time and destroys the oldest, tearing down their records and buffered outboxes regardless of which agent/operator owns them.
- **Failure scenario:** With the cap enabled, a noisy or hostile agent that completes many short tasks pushes the global terminal count over the limit on every `_register_task`; eviction deletes another agent's SUCCEEDED/FAILED task records (and their still-undrained event logs / outbox output) before the owning operator has read them. Cross-agent data loss driven by an untrusted agent's task volume.
- **Fix:** Make the retention bound per-agent (or per-owner) rather than global, or at minimum only evict within the registering agent's own tasks. If a global bound is intended, document that it is shared and adversarially evictable.

### [SEV: med] Unbounded agent registration and runtime state (aggregate memory DoS)
- **File:** connected_agents_service.py:64-144 (`register_agent`); agents_service.py:53-184 (`register_agent`, `self._agents[...] = agent`); task_runtime_service.py:29-32, 43-62 (`_runtimes`, `_agent_task_ids` grow per task)
- **Category:** dos
- **What:** Registration is agent-initiated through a listener and has no count/rate cap. `self._agents`, `TaskRuntimeService._runtimes`/`_agent_task_ids`, and `TasksService._tasks` (non-terminal tasks are never pruned) all grow without bound. Per-task queues are bounded by `QUEUE_MEMORY_LIMIT`, but total resident memory is `(#running tasks) * 2 * QUEUE_MEMORY_LIMIT` plus unbounded record/runtime dicts.
- **Failure scenario:** An attacker controlling (or spoofing to) a listener registers agents in a loop, or opens many long-running tasks; server memory grows until OOM. Nothing in these services attributes or caps per-listener/per-source agent counts.
- **Fix:** This is policy that belongs at the listener/service boundary (per design philosophy). Offer an opt-in per-listener agent cap and/or per-agent live-task cap, defaulting off, and enforce it in `register_agent` / `submit_task` paths.

### [SEV: med] `AgentsService.dispatch_task_output_message` performs no connection/listener validation
- **File:** agents_service.py:435-507; contrast connected_agents_service.py:375-441 (which does `_validate_agent_connected_to_listener` + `agent.get_running_task_by_task_id`)
- **Category:** perms / security (confused-deputy, trust of agent-supplied metadata)
- **What:** The `AgentsService` variant resolves the agent purely from the caller-supplied `agent_id` and submits the agent-supplied result. It relies entirely on `Agent.dispatch_task_output_message` scoping the write to that agent's own running task. There is no check that the *caller/connection* is actually that agent; the listener boundary that provides that guarantee exists only in the `ConnectedAgentsService` wrapper.
- **Failure scenario:** Any code path (a transport/listener author, or a future caller) that reaches `AgentsService.dispatch_task_output_message` directly instead of the connected wrapper can inject results into an arbitrary agent's running task by passing that agent's id, spoofing an untrusted agent's output as another agent's. The safety is by convention, not by construction.
- **Fix:** Either make the connection-scoped path the only public one, or push the listener/connection ownership check down so the unscoped `AgentsService` entry point cannot be used to cross agents. At minimum document the invariant loudly at the method.

### [SEV: low] Auto check-in on every message read amplifies untrusted-agent polling into a broadcast event flood
- **File:** connected_agents_service.py:207-213, 245-250, 282-287 (`check_in_agent_by_agent_id` per read); agents_service.py:247-269 (fires `AGENT_CHECKED_IN` via `run_async_background_task`)
- **Category:** dos
- **What:** Each `get_next_task_message_*` call performs an automatic check-in, which schedules a fire-and-forget `AGENT_CHECKED_IN` event broadcast to all subscribers. A non-blocking (`timeout=0`) poll loop from a remote agent therefore emits events as fast as it can call, fanning out to every connected events-API client.
- **Failure scenario:** A hostile agent tight-loops polling with `timeout=0`; the server spawns unbounded background event tasks and floods all operator websockets, degrading the events API for everyone.
- **Fix:** Debounce/rate-limit check-in event emission (e.g. suppress if last check-in was within N ms), or make the auto-check-in event opt-in / coalesced.

### [SEV: low] `AGENT_CHECKED_IN` event serializes the agent before the check-in fields are updated
- **File:** agents_service.py:259-268
- **Category:** error-handling / correctness
- **What:** `data=agent.to_json()` is evaluated when the coroutine argument is built (line 260-266), before `datetime_last_checked_in = utc_now()` and `mark_as_active()` run (267-268). The emitted event carries the *previous* check-in timestamp and pre-update status.
- **Failure scenario:** Subscribers observing `AGENT_CHECKED_IN` see stale `datetime_last_checked_in`/`status`, so anything driven off the event stream (dashboards, liveness logic) lags by one check-in.
- **Fix:** Update the timestamp and status first, then build `to_json()` for the event.

### [SEV: low] Agent lookup uses non-canonicalizing `normalize_uuid`, inconsistent with task lookups
- **File:** agents_service.py:509-530 (`get_agent_by_agent_id`, `normalize_uuid` = bare `str()`); utils.py:169-170; contrast tasks_service.py:40-51 and task_runtime_service.py:13-21 (`_canonicalize_uuid`)
- **Category:** error-handling / design
- **What:** Agents are stored keyed by canonical `str(uuid4())`, but lookups canonicalize with `normalize_uuid`, which is just `str(value)` (no UUID normalization). A valid but non-canonical id (uppercase, braces, `urn:uuid:` form) fails to match and raises `AgentNotFoundError` even though the agent exists. Task lookups in the sibling services do canonicalize, so the two paths disagree.
- **Failure scenario:** A client (or the `ConnectedAgentsService` -> `AgentsService` chain) passing a differently-cased/formatted UUID gets a spurious not-found for a live agent; behavior differs from the task endpoints for the same input.
- **Fix:** Canonicalize agent ids the same way as task ids (parse to `uuid.UUID` then `str`), ideally via one shared helper.

## Design notes
- **No object-level ownership on task read/delete; flat RBAC only.** `TasksService.get_all_tasks`, `get_task_by_task_id`, `find_task`, `delete_task_by_task_id` (tasks_service.py:81-149, 182-206, 239-275) take a bare `task_id` with no owner scoping; the API gates them on coarse role permissions (`READ_ALL_AGENT_TASKS`, `READ_AGENT_TASK_BY_TASK_ID`, `DELETE_AGENT_TASK_BY_TASK_ID` — tasks_api.py:57-64, 80-106, 125-133), not per-operator/per-agent ownership. Any operator holding the permission can read or delete *any* agent's task by id. If the intended model is "all operators are peers", this is fine and worth stating; if not, object-level authz must be added at the boundary since the services deliberately stay global.
- **Duplicated `_canonicalize_uuid`.** Identical helper in task_runtime_service.py:13-21 and tasks_service.py:40-51, and a third divergent `normalize_uuid` in utils.py. Consolidate into one canonicalizing helper and use it everywhere ids are looked up.
- **Duplicated dispatch assembly.** The `task_output_message is None -> build TaskOutputMessageModel` boilerplate is copy-pasted in connected_agents_service.py:418-432 and agents_service.py:482-497, and the connected variant adds a redundant `get_running_task_by_task_id` pre-check whose failure semantics (raises `AgentTaskNotFoundError`) differ from the inner path (logs and drops). Factor the assembly into one place and pick a single not-running semantics.
- **`get_next_task_message_*` docstrings advertise raising `AgentTaskNotFoundError` to the (untrusted) remote agent** (connected_agents_service.py:197-202, 306-311). It only reflects the agent's own task set, so the leak is minor, but the raise-vs-drop inconsistency with `dispatch` is worth aligning.

## Notes
- **Event payload info-leak is out-of-file but relevant.** `AGENT_TASKED` emits full `task.to_json()` including `arguments` (agents_service.py:585-594); agent lifecycle events emit `agent.to_json()` including `remote_ip`, `local_ip`, `user`, `hostname`, `pid`. Whether operator A sees operator/agent B's command arguments and host metadata depends on events-API subscriber authz (events_api.py / events_service.py), which is outside scope. Flagged for a human to confirm the events channel is authorized per-subscriber.
- **Per-task queue bounds confirmed present** (`_agent_communicator.py:35-47` constructs inbox/outbox with `maximum_memory_size=QUEUE_MEMORY_LIMIT`), so a single agent flooding one task's inbox via `dispatch_task_output_message` is bounded — the residual DoS is aggregate (see the unbounded-registration finding), not per-queue.
- **Concurrency of the state machine looks sound.** `claim_for_deletion` (task_objects.py:51-60) fuses the deletable test with the claim, `_destroy_task_record` pops the record before touching the runtime (tasks_service.py:151-173), and `delete`/`teardown`/handler-completion all use `_try_transition_*` CAS, so the QUEUED->RUNNING-vs-delete and teardown-vs-completion races resolve to a single winner. No TOCTOU found in the transition paths reviewed; the delete critical section correctly keeps no `await` between the state check and record destruction. Left as a note rather than a finding.
