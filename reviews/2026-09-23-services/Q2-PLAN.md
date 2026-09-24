# Q2 remediation plan: high complexity / high gain

Split out of `PLAN.md` (which stays the Q1/Q3 handoff) on 2026-09-24 to keep each tier readable.
Background: `TRIAGE.md` (quadrants), `SUMMARY.md`, `findings/*.md`. Ground rules: see `PLAN.md`
(repo root, do-not-touch dirs, ASCII `#` comments, commit-only-when-asked, peer authorization).

Triage of the high-complexity/high-gain tier finished 2026-09-24 with the user. Every item below is
decided; **F is deferred** (trust-boundary ruling not yet made) and **G was closed as by-design**
(peer authorization, see the Q2-G note in `TRIAGE.md`). **B and C are now implemented** (commits
`6363427b` factor-out, `01364a04` lock + reconcile) and pushed to `origin/fix/code-review-fixes`; the
full services suite (565 tests) passes. E, D and A remain planned. Line numbers
were captured 2026-09-24 against HEAD `0a404028` (still HEAD; the Q1/Q3 work is on branch
`fix/code-review-fixes`, so verify against that branch before editing) and must be re-checked locally.

Recommended order: **B+C together** (same files/refactor, no decisions) -> **E** (one pattern, but a
real transaction design, not a reorder) -> **D** (isolated, decision made) -> **A** (own session, most
surface). F only after a ruling. Only B+C is a hard dependency; E and D positions are scheduling choices.
D before A is useful but needs explicit D+A integration checks (see "D+A interactions" under A).

**Review round 2 (Codex `gpt-6-astra`, read-only, 2026-09-24, against `fix/code-review-fixes` @
`23adea96`).** Verdict: the two-field credential format is sound, but the plan needed revision before
implementation. Its findings are folded into each item below as **"Spec additions (review 2)"** blocks,
and the statements it showed to be false are corrected inline. File:line refs in those blocks are against
`23adea96`, not `0a404028`. One verified side-finding was fixed immediately (Q1 follow-up, not Q2):
`start_server.py` built `LoggingConfigModel` from an explicit field list that omitted `log_secrets`, so
the Q1#1 flag had no effect from `logging_config.json`; now passed through (see `PLAN.md` #1 note).
Lesson for A: any new config flag (`hash_passwords_at_rest`) must be wired through its loader too.

## Status and implementation order

| Order | Item | Finding(s) | Status |
|---|---|---|---|
| 1 | B Repository concurrency lock | D-files med (unsynced shared state) | implemented (`6363427b`, `01364a04`) |
| 1 | C Repository partial-failure reconcile | D-files med (partial failure) | implemented (`6363427b`, `01364a04`) |
| 2 | E Reload/resolve ordering + rollback | G med, F-listeners med, C-codeloading med | planned |
| 3 | D Session/socket revocation on delete/downgrade | A-auth-reverify med (+ low frame cap) | planned |
| 4 | A Password hashing (opt-in) + constant-time compare | A-auth HIGH; A-auth med; E-api low | planned; **1 open decision** (password-in-response vs hashing/`log_secrets`) |
| - | F Arbitrary source-path ingest confinement | D-files med | **deferred** (trust ruling) |

---

## B. Repository concurrency lock

**Problem.** `RepositoryService` has no lock. Every payloads/artifacts mutation runs via
`asyncio.to_thread`, so concurrent REST requests mutate `self._resources` (dict) and
`self._reserved_resource_ids` (set) on different worker threads and call `save_repository_metadata()`
concurrently. Q1#2 made the *write itself* atomic (`atomic_write_bytes`), so a single write can no
longer truncate the file, but concurrent writers still race (last-writer-wins can drop a record) and
the dict/set mutations are unguarded.

**Design (decided).** One `threading.Lock` on `RepositoryService`, held around every mutation of
`_resources` / `_reserved_resource_ids` and every `save_repository_metadata()` call. Mutation sites
(re-verify): `repository_service.py` `:219` (load), `:263` (reserve), `:307/:322` (create_file),
`:378/:394` (add_file), `:452/:466` (create_directory), `:525/:541` (add_directory), `:589` (update),
`:642/:644` (delete). The metadata write must be inside the lock so two threads cannot interleave a
save. `threading.Lock` (not asyncio) because the mutators run in `to_thread` worker threads.
~~Keep the lock scope tight (guard the state transition, not disk I/O inside the resource objects).~~
Not achievable as written: saving metadata calls every resource's `to_json()`, which includes a
directory-size traversal, so the lock already covers resource I/O (`repository_service.py:235-250`,
`repository_objects.py:453-476`). Either accept that broader serialization (simplest; recommended for a
first cut) or snapshot the serialized forms outside the lock and publish them under it.

**Finalized 2026-09-24 (decisions made with the user).**
- **Lock type:** one `threading.Lock` per `RepositoryService` instance (not `RLock`), with the
  **public/private save split**: `save_repository_metadata()` acquires the lock and calls
  `_save_repository_metadata_locked()`; mutators call the private form inside their own critical
  section. The split keeps the "lock is held here" invariant explicit rather than relying on reentry.
- **Lock scope:** broad. Hold the lock across serialization + write, including the directory size walk
  in `to_json`. Accepted for a first cut; revisit only if these repos become hot.
- **Compound ops each in one critical section:** reserve-check -> consume; delete's
  get -> `resource.delete()` -> `del` -> save (closes the two-concurrent-delete `KeyError`); update's
  mutate -> save.
- **Reader guarantee:** documented, not copied. `get_all_resources` / `get_resource_by_resource_id`
  return live objects whose fields may change concurrently; state this in their docstrings.
- **`atomic_write_bytes` `.tmp` corruption:** `utils.py:135` uses a fixed sibling temp path
  (`.repository.json.tmp`), so two concurrent saves clobber the same temp file and `os.replace` can
  publish torn/foreign bytes. **Closed by B's serialization alone** — no change to `utils.py`.
- **`save_repository_metadata` dict-iteration:** the `self._resources.items()` comprehension
  (`:236-238`) would raise `RuntimeError: dictionary changed size during iteration` under a concurrent
  mutation; also closed by the lock.

**Do B and C together and factor first.** The D-files design note flags ~4x duplication across the
create/add wrappers (`payloads_service.py:108-494`, `artifacts_service.py:116-379`) and their
`_build_*_resource_data` + emit + `to_thread` boilerplate. Factoring the create/add path into one
helper makes both the lock (B) and the ordering fix (C) a one-place change instead of eight.

**Spec additions (review 2).**
- **No nested acquisition (deadlock).** create/add/update/delete call `save_repository_metadata()`
  internally (`repository_service.py:303-324`). With a non-reentrant lock, locking both the mutator and
  the public save deadlocks. Split into a public `save_repository_metadata()` that takes the lock and a
  private `_save_repository_metadata_locked()` that asserts/assumes it is held; mutators call the
  private one.
- **Compound operations share one critical section.** "Every mutation" is not enough:
  reservation check + consume must be atomic; delete's get-resource -> delete-contents -> `del` record
  must be atomic, or two concurrent deletes both fetch the resource and the second `del` raises
  `KeyError` (`:617-644`). Update vs delete has the same stale-reference race.
- **Reader guarantees.** Getters return live resource objects (`:646-680`), so locking only collection
  access does not make a later serialization consistent with a concurrent update. Document the
  guarantee (e.g. "getters return a snapshot list; object fields may change concurrently") or return
  copies.
- **Assets are in scope.** `assets_service.py:157,462` has the same threaded create/add/update/delete
  paths. Put the lock and C's ordering in `RepositoryService` itself (the real single enforcement point);
  factoring only the payload/artifact wrappers does not cover assets.

Tests: two concurrent creates both land (no dropped record); concurrent create+delete leaves a
consistent index; two concurrent deletes of the same resource yield one success + one not-found (no
`KeyError`); a mutator calling save does not deadlock; the asset paths get the same coverage.

## C. Repository partial-failure reconcile

**Problem.** Create/add paths write/move onto disk, insert into `_resources`, *then* persist metadata.
If the persist fails the file is an untracked orphan (and with `copy=False`, the default, the source is
already gone). Delete removes the on-disk object then persists; a persist failure after deletion leaves
metadata listing a resource whose file is gone. On next load, that unsynced state makes
`load_repository_metadata` refuse to load the **entire** repository
(`repository_service.py:181-185`, `RepositoryMetadataFileUnsyncedError`) rather than one resource.

**Design (decided direction; confirm the exact mix at implementation).** Two complementary changes:
1. **Reconcile-on-load, not refuse.** Downgrade the hard `RepositoryMetadataFileUnsyncedError` for a
   *missing-on-disk* resource to a logged warning + drop that one entry (and re-save), so one orphaned
   record cannot brick the whole repository. Keep hard failures for genuine corruption (bad JSON,
   schema, encoding). This is the higher-value half: it turns a whole-repo outage into a single lost
   resource.
2. **Best-effort rollback on the write paths.** Where a persist fails right after a disk op, roll back.
   Document any residual window in the method docstring rather than pretending it is atomic.
   ~~restore is not possible for a moved source, so prefer `copy` semantics~~: too categorical, and
   silently turning `copy=False` into copy-only changes the caller's chosen semantics (AGENTS.md). Keep
   move semantics; attempt move-back on failure (see below).

**Finalized 2026-09-24 (decisions made with the user).**
- **Reconcile-on-load:** a *missing-on-disk* record is downgraded from `RepositoryMetadataFileUnsyncedError`
  to a logged warning + drop-the-entry + re-save. A re-save failure still serves the survivors from
  memory. Hard failures stay for genuine corruption (UTF-8, JSON, schema, `data_model`). Build a fresh
  index dict and swap it in; repeated `load_repository_metadata()` = replace, not merge.
- **Rollback runs inside B's critical section** on every write path: create/add remove the new
  `_resources` record and restore-or-release the reservation; **update restores the pre-update
  name/description/data** (chosen: a failed update must not leak in on the next save); `copy=False`
  failure moves the source back, and if move-back fails keeps the bytes in the repo dir, logs both
  paths, and raises.
- **Residuals (explicit):** unindexed on-disk orphans (create-path persist failure leaves a file the
  loader never notices), partially deleted directory contents, and general crash consistency.

**Sequencing (finalized): two commits.** (1) factor the ~4x-duplicated create/add path into one helper;
(2) apply B (lock + split) and C (reconcile-on-load + rollback wrapper) together on the factored helper.
Do B and C only in this pass; nothing else in the Q2 tier.

**Spec additions (review 2).**
- **Rollback restores memory + reservations, not just disk.** Create registers in `_resources` before
  saving; update mutates the live object before saving (`repository_service.py:314-324,578-589`).
  Disk-only cleanup leaves a phantom entry, or a failed update that becomes persistent on the *next*
  successful save. On persist failure: remove the new record / restore the pre-update field values, and
  release or restore the reservation.
- **Never delete the destination of a failed move unless the source is back.** It may be the only
  remaining copy. Order: try to move back to the original source path; only if that succeeds is the
  destination gone. If move-back fails (or the source path has been reused), **keep the bytes** in the
  repository dir, log loudly with both paths, and raise. Losing data is worse than an orphan, and
  reconcile-on-load can surface orphans later. Existing move contract: `:339-369`.
- **Reconcile re-save failure must not recreate the outage.** If dropping missing entries succeeds but
  the re-save fails, still serve the surviving resources from memory, log the failure, and retry on the
  next save. Do not make "repair persisted" a precondition for loading.
- **Stage the reconstructed index, then publish.** The loader currently inserts into the existing dict
  without replacing it (`:188-219`), so a second load merges. Build a fresh dict, validate, then swap;
  define repeated-load semantics as "replace".
- **Residual (explicit, best-effort design):** this repairs missing-file records only. Unindexed files
  on disk, partially deleted directory contents, and general crash consistency stay out of scope.

Pairs with B (same lock, same factored helper). Tests: a simulated persist failure after disk placement
does not leave the repository unloadable, leaves no phantom in-memory record, and releases the
reservation; a failed update persist restores the old values; a failed `copy=False` ingest moves the
source back, and when move-back also fails the bytes are kept; load tolerates a single missing-on-disk
record; a failed reconcile re-save still serves survivors; loading twice replaces rather than merges.

## E. Reload / resolve ordering + rollback (load-then-swap)

**Problem (one shape, several sites).** Unload/commit happens *before* validation/resolution, with no
rollback, so one failure leaves the server worse than before it started. Q1#3 already fixed the *batch
discovery* catch (one bad component no longer aborts a scan); this item is the distinct **reload and
resolve-ordering** family:
- `agent_profiles_service.py:204-209` (`load_agent_profile` registers, *then*
  `_resolve_agent_type_references()`), and the per-profile catch set at `:442-452` does not include the
  resolution exceptions, so a resolve failure aborts the whole batch (G med). Same order in the
  from-directory / reload paths `:263-281`, `:365-384`.
- `listener_profiles_service.py:442-454` reload = unload-all-then-load-all, no rollback; on load
  failure the server has zero listener profiles and listener creation then fails until restart
  (F-listeners med). Its per-profile load loop `:397-407` also catches only two exception types.
- `component_registry_service.py:166-187` (`reload_component_by_component_id`) unloads (stops + del)
  before loading, no rollback; a failed reload permanently drops a working plugin (C-codeloading med).

**Design (decided).** Consistent pattern across all three:
- Resolve/validate references **before** committing/starting the profile or component; on failure do
  not leave it registered.
- Reloads: **load-then-swap** (build the new instance, swap under the relevant lock, unload the old),
  or snapshot-and-restore on failure, so a failed reload leaves the previous working set intact.
- Widen the per-profile catch sets to collect resolution/unexpected errors as one per-profile failure
  instead of aborting the batch (mirror the Q1#3 batch catch-all shape).

**Spec additions (review 2).** Not a mechanical reorder; each of these needs a design decision at
implementation time.
- **Stale premise:** profiles are not "started". Profile registry subclasses only override ID
  extraction and inherit a no-op load (`agent_profile_registry_service.py:12-16`,
  `component_registry_service.py:41-47`). The register-before-resolve defect is real; activation is not.
- **Resolve against a candidate graph.** `_resolve_agent_type_references()` reads only *registered*
  profiles and mutates profiles/templates as it goes (`c2_types_service.py:318-373`). Simply calling it
  before registration would miss the candidate itself, and a dict snapshot cannot undo mutations inside
  shared objects. Build the candidate set (registered minus the instance being replaced, plus the new
  one), resolve and validate against it without mutating live objects, and only then publish bindings.
- **Forward references within a batch.** Profiles load sequentially, so a reference to a later profile
  in the same batch fails. Resolve the whole batch together (or order by dependency).
- **Reverse indices only grow.** Listener-compatibility reconstruction only adds to sets
  (`c2_types_service.py:298-316`, `agent_profiles_service.py:439-452`), so a removal or replacement leaves
  stale relationships. Rebuild the indices from the published set, don't append.
- **Prepare / activate / tear down are separate stages.** Plugin load can start the candidate
  (`plugin_registry_service.py:21-29`); event-hook load registers subscriptions before awaiting setup
  (`event_hook_registry_service.py:40-79`). Load-then-swap would therefore run old and new *at once*.
  Define: prepare the candidate (no side effects), stop the old one, activate the new one, and on activation
  failure try to re-activate the old one. A registry swap cannot undo arbitrary lifecycle side effects.
- **Structured failure results.** The batch loader logs failures and returns normally
  (`listener_profiles_service.py:377-416`), so "load completed" can mean "loaded zero". The replace
  transaction needs a result it can inspect (per-item success/failure) to decide whether to keep the old
  set. Widening catches must not hide a failed reload.
- **Narrow the "old instance keeps working" promise.** Candidate construction calls
  `importlib.reload()` on the existing module (`component_loader_service.py:324-333`), which mutates the
  old instance's module in place. Import-state isolation is deferred in `TRIAGE.md:123-129`, so the
  guarantee is "the old instance stays registered", not "stays working". Bring isolation into scope only
  if the stronger promise is wanted.
- **Related paths not covered by fixing the generic reload.** Framework-wide agent/plugin/event-hook
  reloads orchestrate unload-before-load independently (`agent_profiles_service.py:508-510`,
  `plugins_service.py:650-705`, `event_hooks_service.py:549-550`). Also `load_component()` skips the
  label/dependency checks that `register_component()` performs (`component_registry_service.py:81-137`).
  Include these, or record them as residuals.

No external decision. Tests per site: a profile whose type-ref resolution raises is reported as one
failed profile and does not abort the batch; a reload whose load half fails leaves the prior instance
registered; a batch with a forward reference to a later profile resolves; replacing a profile removes
its stale reverse-index entries; a plugin reload never has old and new active at the same time; a reload
that loads zero items reports failure rather than success.

## D. Session / socket revocation on operator delete or downgrade

**Problem.** A live events websocket is authorized only at the handshake
(`events_websocket_service.py` `run` loop never re-checks); and account **deletion** pops from
`user_accounts_service._user_accounts` without ending that operator's live sessions or sockets. A
deleted or downgraded operator keeps a REST session (its `User` holds the same `UserAccountModel` by
reference, so a role change *is* seen live for REST authz, but the session itself is never torn down)
and keeps receiving events on its socket until it chooses to disconnect. Per AGENTS.md this is session
lifecycle, explicitly in-scope, and **not** closed by the peer-ownership decision.

**Decision (made): a revocation hook on delete/downgrade** that terminates the affected operator's live
sessions and sockets. Chosen over ws-loop-only re-checking because it fixes both the REST and websocket
sides in one place.

**Design.**
1. **Live-connection registry (new).** There is currently no registry of open websockets
   (`websockets_api.py:104-129` -> `handle_connection` -> `_EventsWebsocketHandler` holds
   `self._websocket`, but nothing indexes it). Give `EventsWebsocketService` a registry keyed by
   `user_id` (session id): `handle_connection` registers the handler on entry and removes it in a
   `finally`. Add `async def terminate_connections_for_user(user_id)` that closes each registered
   socket. ~~closing makes `receive_json` raise~~: **unverified** (review 2). Existing cleanup runs
   when `run()` exits, not when another task asks it to close (`events_websocket_service.py:379-440`).
   Give each handler an explicit termination mechanism (a cancel/stop event its `run()` loop checks, or
   cancelling the handler task) and prove with a test that a pending `receive_json()` is woken.
2. **Session teardown helper (new) on `users_service`.** `_users` is keyed by session `user_id`; each
   `User` has `.user_account.user_account_id`. Add a helper that pops every session whose
   `user_account_id` matches a given account, and for each triggers
   `events_websocket_service.terminate_connections_for_user(user_id)`. Reach the ws service via
   `server_singletons` (the codebase's existing cross-service pattern) to avoid an import cycle.
3. **Wire the hook.** Call the teardown helper from the two revocation points: account **delete**
   (`user_accounts_service.delete_user_account_by_user_account_id`, API `user_accounts_api.py:~330`)
   and account **role change** (`update_user_account_by_user_account_id`, the role branch after
   `:246`). Rule: on delete or any role change, terminate that operator's live sessions+sockets and
   force re-login. Simpler and safer than re-deriving whether the new role still passes each open
   socket's permission. **Review 2 expands this to four points:** account delete, account role
   change, role-permission change / role delete, and ordinary logout (see the bypasses below).
4. **(Fold in) frame/subscription cap** (A-auth-reverify low): bound `receive_json` frame size and the
   `events` list length in `_handle_subscribe_action`, consistent with policy-at-the-boundary and
   default-off philosophy. Optional; keep separate if it bloats the change. Note (review 2): checking
   list length *after* `receive_json()` cannot bound frame buffering or JSON parsing; the frame-size
   cap has to be set on the transport (uvicorn `ws_max_size`) or checked on the raw frame before
   parsing. Both limits stay parameterized and default-off.

**Spec additions (review 2): three revocation bypasses in the design as written.**
- **Handshake race.** Auth happens before `await websocket.accept()`; registry insertion happens
  after it, in `handle_connection` (`websockets_api.py:120-129`). A delete during that `await` revokes
  every known session and connection, then the already-authenticated socket registers and starts
  serving. Fix: re-check that the session is still live immediately before registering, with **no
  `await` between the check and the insert**. Alternatively register a pending connection before
  `accept()`.
- **Logged-out sockets escape the account scan.** Logout removes the session but leaves its websocket
  running (`users_service.py:164-187`). Account deletion finds sessions via `_users`, so it can never
  reach that socket. Fix: make ordinary logout use the same connection teardown (recommended; it closes
  the gap at the source), and/or key the connection registry by account id as well as session id.
- **Role *permission* edits bypass both hooks.** Removing `USE_EVENTS_WEBSOCKET` from a role, replacing
  a role's permissions, or deleting a role changes the role, not any account's `role` field
  (`authorization_service.py:250-318`). The original finding covers these
  (`findings/A-auth-opus-reverify.md:21-26`). Add a third hook: on any role-permission change or role
  delete, tear down every session whose account holds that role.

**Teardown contract.**
- First invalidate *all* affected sessions and mark/deregister their handlers synchronously. Only then
  await the individual socket closes.
- One close failure must not stop the rest: gather with `return_exceptions=True` and log the failures.
- Account and role mutators are currently synchronous, so specify how they trigger the async closes.
  E.g. the sync mutator invalidates and deregisters in-line and schedules the closes on the loop; the
  API route awaits them.

Tests: deleting/downgrading an operator with a live session closes its socket and drops its
subscriptions; a still-valid operator's socket is untouched; a delete landing between auth and
`accept()` still ends that connection; logout closes the session's socket; removing
`USE_EVENTS_WEBSOCKET` from a role (and deleting a role) tears down that role's sockets; one socket
whose close raises does not prevent the others from closing; a pending `receive_json()` is actually
woken by termination.

## A. Password hashing (opt-in, at-rest) + constant-time compare

**Finding.** A-auth HIGH: passwords stored, compared (`!=`), persisted in plaintext. Q1#1 already
stopped the *leaks* (repr/log redaction); this closes the plaintext-at-rest and the non-constant-time
compare, and folds in A-auth med (username-enumeration timing) and E-api low (API re-auth timing).

**User constraint (decisive):** hand-editing `user_accounts.json` with plaintext passwords must keep
working; no dedicated CRUD client. Resolution: the file accepts **plaintext as an input form**, hashing
is the at-rest form, and moving plaintext off disk is **opt-in, default off** (matches AGENTS.md
"limits parameterized, default off").

**Type is out-of-band, never sniffed from the value (2026-09-24 revision).** An earlier draft used a
single tagged string (`plain:`/`argon2id:` prefix) and decided the type by inspecting the value. That is
unsafe because the value is user-controlled: a legitimate password of `argon2id:hunter2` gets
misclassified as a hash and becomes unusable, and a crafted valid PHC string (`$argon2id$v=19$m=...`)
set as someone's own password is parsed as a real hash (contained to that account, but it turns verify
into a confused deputy and lets the load-migration *skip* an attacker-controlled entry, leaving those
bytes in the hash slot). You cannot reserve a prefix against user input without escaping. So the type is
carried by **which field** holds the value, not by its bytes.

**Design (decided).**
1. **Two separate optional fields, exactly one required.** `password` is **always plaintext** (never
   parsed for a tag: `argon2id:hunter2` is just a plaintext password). `password_hash` is **always a
   hash**, produced only by the migration or the helper tool. On-disk model
   (`PersistentUserAccountModel`, `user_account_models.py:27`): both optional, `repr=False`; a pydantic
   model validator requires **exactly one** to be present. **Both present or neither is a schema error**
   that fails the load loudly. Rejecting "both" removes ambiguity; it is **not** a defence against a
   file-writer (review 2: anyone who can rewrite the file can simply replace the hash).
   Add the KDF dep with `uv add argon2-cffi` (never edit pyproject by hand, per AGENTS.md).
2. **Constant-time verify, always (independent of the flag).** `authenticate_user_account_credentials`
   (`user_accounts_service.py:336`) and the API re-auth (`user_accounts_api.py:212`): if the account
   carries a `password_hash`, verify with `PasswordHasher.verify`; else `hmac.compare_digest` on the
   plaintext. On an unknown username, run a dummy KDF verify, and lets us drop the dead
   `existing_usernames` scan at `:329-336`. Move the API-layer re-auth into a service method so the
   handler neither retrieves stored credentials nor implements verification (E-api low). (It still
   necessarily *receives* the submitted candidate; ~~"cleartext never sits in the handler"~~ was wrong.)
   **Correction (review 2): as written this does NOT close the enumeration oracle, it makes it worse.**
   Known-plaintext accounts (the default config) get a fast `compare_digest` while unknown usernames get
   a slow KDF, so "unknown user" becomes easier to detect. See "Uniform verify work" below. Also, the
   early-return username lookup (`user_accounts_service.py:112-116`) remains, so never describe total
   request timing as constant.
3. **`hash_passwords_at_rest: bool = False`** on the server `LoggingConfigModel` sibling config (put it
   with the account/security config, next to Q1#1's `log_secrets`; confirm the right model). Default
   off: file stays plaintext (`password` field), hand-editable, compares now constant-time -- no
   behaviour change to the operator workflow. **Wire it through the loader** (review 2): the config is
   built from an explicit field list in `start_server.py`, which is exactly how `log_secrets` ended up
   silently ignored. Add a test that the flag set in JSON reaches the service.
4. **Write-back on load (whole file at once), only when the flag is ON** (user chose load-migrate over
   lazy). In `load_user_accounts_from_user_accounts_file` / `load_framework_user_accounts`
   (`user_accounts_service.py:591`), after loading, if the flag is on and any entry still carries a
   `password` (plaintext) field, hash it into `password_hash`, **drop the `password` field**, and
   rewrite the file via `write_user_accounts_to_user_accounts_file` (`:568`, already atomic from Q1#2).
   Migration keys on field *presence*, not value content, so it cannot be fooled into skipping. First
   boot after flipping the flag => fully hashed file; hand-typed plaintext is gone by design.
   **Not atomic as described (review 2); see "Migration transaction" below.** Q1#2's helper gives
   whole-file replacement, not a transaction across parse -> hash -> publish -> persist, and its fixed
   `.tmp` path needs serialized writers (`utils.py:126-139`).
5. **`tools/hash_password.py` helper.** Prints the `"password_hash": "$argon2id$..."` line to paste into
   the JSON, so an operator can hand-write a hashed entry even with the flag off. Output makes the
   contract explicit: paste into `password_hash`, not `password`. Small standalone script.
6. **In-memory + write path.** Mirror the two fields on `UserAccountModel` (`:9`) with the same
   exactly-one validator, so the in-memory account holds whichever form it was loaded/created with and
   `write_user_accounts_to_user_accounts_file` (`:548-553`) serializes back the field that is set.
   No `SecretStr`. `create_user_account` / `update_user_account` set `password_hash` when the flag is on
   and `password` otherwise (so a later load-migrate is uniform). The only residual is pilot error:
   pasting a hash into the plaintext `password` field double-hashes it on migration -- acceptable, the
   field name is the contract and the helper/docs state it. A construction-time validator alone does
   not make *updates* safe; see "Credential transitions" below.

**Spec additions (review 2).**

*Uniform verify work (replaces the step-2 timing claim).* The three paths must cost about the same:
known-plaintext, known-hashed, and unknown username. Options:
(a) on a known-plaintext account, also run one dummy KDF verify, so every path does exactly one KDF;
(b) at load, derive an in-memory verifier (a KDF hash) for plaintext accounts and always verify against
it, while the on-disk form stays whatever the flag says.
(b) is cleaner but is effectively hashing in memory regardless of the flag; (a) is the smallest change.
Either way:
- The dummy hash is precomputed once with the *current* parameters, and a successful dummy verify can
  never authenticate (always return failure on that path).
- Hand-supplied hashes with different KDF parameters make timing differ per account. Document this,
  and optionally rehash on successful login (`check_needs_rehash`) when the flag is on.

*Encoding and errors.*
- `hmac.compare_digest(str, str)` raises on non-ASCII. Compare `.encode("utf-8")` bytes, and don't
  change password normalization.
- Map argon2 `VerifyMismatchError` / `InvalidHashError` / `VerificationError` to the existing
  `UserAccountAuthenticationError`. Login currently catches only that (`login_api.py:37-54`).
- Run the KDF off the event loop (`asyncio.to_thread`), not inline in the async route.

*Exactly-one, precisely defined.*
- **On disk:** exactly one of the two keys, holding a non-empty string. Reject explicit `null`, both,
  or neither.
- **In memory:** exactly one non-`None` value.
- **Serialization:** omit the unused key entirely (`exclude_none`, or an explicit serializer). Default
  dumping of two optional fields writes one as `null`, which the loader then rejects.
- Keep `extra="forbid"` and the non-empty constraints on the persistent model
  (`user_account_models.py:25-30`).
- Do **not** replace the explicit persistent serializer with `UserAccountModel.model_dump()`. That model
  carries `user_account_id`, which is deliberately excluded from disk.

*Hash-format validation.* The field name decides how a value is interpreted; it does not prove the
string is a usable hash. At load, validate that `password_hash` parses as a supported argon2 PHC string.
Reject it otherwise, and a malformed hash must **never** fall back to plaintext comparison. Report the
error with the sanitized validation formatter (`utils.py:73-97`) so credential values never reach the
message.

*Credential transitions.*
- The current password change mutates `password` in place (`user_accounts_service.py:263-278`).
  Converting plaintext to hash must set `password_hash` **and** clear `password` as one validated step
  (e.g. build the new credential pair, validate it, then assign both). Otherwise the model briefly
  violates the exactly-one rule.
- If the implementation replaces the whole account object instead, keep its `user_account_id` and
  rebind live sessions. `User` holds the account object by reference and reads its role through it
  (`user_objects.py:36-51`), so replacing only the registry entry leaves sessions on stale
  credentials/roles.
- **Flag transitions:** turning hashing *off* must keep existing hashes verifiable and must never need
  plaintext recovered. Username-only or role-only updates keep the credential form as it is.
- Revisit the "new password equals old" no-op check, which compares directly against
  `user_account.password`. With a hashed account it must verify instead.

*Migration transaction (replaces step 4's implied atomicity).*
- Validate every entry, derive all hashes into **staged** state, persist the complete candidate file,
  and only then publish the accounts. On any failure, keep the previous live state and report migration
  failure.
- Current hazards:
  - The loader registers accounts before the proposed write-back. The framework wrapper catches
    service errors and returns `False`, which startup ignores (`user_accounts_service.py:375-381,
    605-611`, `server.py:274-275`). So a failed migration would leave accounts registered, plaintext on
    disk, and the server running. Decide: fail startup, or run with a loud error (flag on means the
    operator asked for hashing, so failing startup is defensible).
  - `write_user_accounts_to_user_accounts_file` serializes **all registered** accounts (`:522-556`).
    Reusing it to migrate one input file could write unrelated accounts into it. Migration needs a
    file-specific candidate collection.
- Create/password-change already mutate memory before persisting; a write failure returns 500 but the
  new in-memory state stays (`user_accounts_api.py:215-242`). Either keep that as documented behaviour
  or improve it; don't imply atomic replacement fixed it.

*Peer-auth interaction.* The format adds no peer-model conflict. Keep the existing split: self-service
change verifies the current password, while permission-authorized admin updates do not
(`user_accounts_api.py:192-223, 257-276`). Moving verification into the service must not add ownership
checks, or require a peer admin to know the target's current password.

*Password in API responses: intentional, coupled; OPEN DECISION.* The account endpoints return
`UserAccountModel` directly, password included (`user_accounts_api.py:67-178`). `repr=False` only
affects `repr()`, not JSON. **User decision 2026-09-24: this is an intentional administrative feature**
(admins holding `READ_ALL_USER_ACCOUNTS` can read account passwords), not a leak. Review 2 flagged it
anyway; that concern is noted but does not override the decision. The user sees three things as coupled:
secret logging (`log_secrets`), hashing at rest (`hash_passwords_at_rest`), and password-in-response.
The design must decide how they combine *before* A is implemented, because once `password_hash` exists
the endpoints will start returning it too, by accident:
- Flag off: the account holds `password` and the response shows plaintext. Today's behaviour; the admin
  feature works.
- Flag on: there is no plaintext left to show. The response would carry `password_hash` (useless to
  an admin, offline-crackable) unless told otherwise.
- Options to pick from:
  (1) show `password` when present and always omit `password_hash`, so the feature degrades naturally
  once hashing is on;
  (2) put password display behind its own default-off flag, alongside `log_secrets`;
  (3) put display behind `log_secrets` itself (one "reveal secrets" switch);
  (4) keep returning whatever field is set, hash included.
- Also affected: `/me` returns the caller's own password (`READ_OWN_USER_ACCOUNT`), and create/update
  responses echo the credential.
- Whatever is chosen, add a comment at the model/endpoint saying it is deliberate, so future reviews
  don't re-flag it.

*`log_secrets` interaction.* Keep the flags independent in mechanism:
- Both credential fields stay out of `repr` regardless of either flag.
- Hashing never turns on secret logging.
- With hashing on and `log_secrets=True`, the password-change log line still writes the *new* plaintext
  to disk (`user_accounts_service.py:263-274`, `logging_service.py:53-62`). That is consistent with the
  opt-in, but it rules out any blanket "plaintext is gone from disk" claim. Say so in the docs.
- A hashed account has no "old password" for that log line to print. Define the message explicitly
  (e.g. "<hashed>"), and never log the hash in its place.

*D+A interactions (ordering check).*
- Account reload deletes every account and builds fresh IDs (`user_accounts_service.py:636-646`). Once
  D's delete hook exists, a reload revokes every session, even if the reload then fails. Either make
  reload match accounts by username and keep the IDs, or accept "reload = everyone re-logs in" and
  document it.
- With the KDF off the event loop, the account can be deleted, downgraded or have its password changed
  while verification is running. Before issuing a session, re-check that the account still exists and
  that its credential is the one that was verified (a credential version counter, or an identity check
  on the credential string) (`users_service.py:128-149`).

Its own session. Tests: plaintext entry authenticates (flag off) with constant-time compare; a password
that is literally `argon2id:...`/`$argon2id$...` authenticates as plaintext (regression for the sniffing
bug); an entry with both fields, or neither, is rejected at load; unknown username does equal work;
flag-on load rewrites every `password` to `password_hash` and drops the plaintext, and the hashed
entries still authenticate; hand-added plaintext with flag on is migrated on next load; the helper's
output loads and authenticates.
Added by review 2:
- **Timing and verify:** known-plaintext, known-hashed and unknown-username paths each do one KDF
  (count calls, don't time them); the dummy hash never authenticates; a non-ASCII plaintext password
  authenticates; a mismatched or malformed hash yields `UserAccountAuthenticationError`, not a 500.
- **Schema:** explicit `null` in either field is rejected; saving writes only the key that is set; a
  malformed `password_hash` is rejected at load and never compared as plaintext; the error message
  contains no credential value.
- **Migration:** a failed migration persist leaves the previous live accounts and the original file
  untouched; migrating one file does not write accounts from another.
- **Transitions:** a password change with the flag on clears `password` and sets `password_hash`;
  flag on -> off still authenticates hashed accounts; a role-only update keeps the credential form.
- **Wiring and races:** `hash_passwords_at_rest` set in JSON reaches the service; deleting an account
  while its login's KDF is running issues no session.
- **Responses:** whichever response option is chosen, a test pins it (e.g. flag on -> no
  `password_hash` in `/user_accounts/all`).

## F. Deferred: arbitrary source-path ingest confinement

`add_*` accepts an arbitrary source `path` with no allowlist; `copy=False` (default) `shutil.move`s the
target into the repo (arbitrary read via download, plus arbitrary move/delete of the original). Severity
depends entirely on whether the agent file-manager facade reaches it with agent/component-controlled
input. **User deferred pending a trust-boundary ruling.** If the ruling is "trusted-only", this
collapses to a docstring hazard note (Q1-cheap); if agent-reachable, add real confinement (resolve +
`is_relative_to` a configured ingest base; reject `..`, absolute escapes, escaping symlinks). Sites:
`payloads_service.py:203-297,398-494`; `artifacts_service.py:177-379`; forwarded unvalidated to
`repository_service.py:370-397,517-544`; facade passthrough `agent_file_manager_service.py:219-225,
313-319`.
