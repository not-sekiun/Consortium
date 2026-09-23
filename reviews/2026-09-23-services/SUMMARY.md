# Consortium core-services review — SUMMARY

Reviewed at base commit `0a404028a28d402b7e8694e99c1cfa550782d4a6` on 2026-09-23.
Method: chunked, resumable, disk-backed review (see `MANIFEST.md`); one reviewer per chunk,
high effort except E-api (low). The two crown-jewel chunks (A-auth, C-codeloading) additionally
got an **Opus verification re-review** (see that section). Threat model: authenticated operators
may be hostile; remote agents fully untrusted. Full per-finding detail lives in `findings/`.

## Status — all 9 chunks complete

| Chunk | Scope | Effort | High | Med | Low | File |
|---|---|---|---|---|---|---|
| E-api | HTTP/WS API layer | low | 0 | 1 | 3 | findings/E-api.md |
| A-auth | Auth / identity / ws tickets | high | 2 | 2→3 | 0→1 | findings/A-auth.md (+ A-auth-opus-reverify.md) |
| C-codeloading | Plugin/component loading | high | 2→1 | 4→6 | 3→5 | findings/C-codeloading.md (+ C-codeloading-opus-reverify.md) |
| B-runtime | Task / agent runtime | high | 0 | 3 | 3 | findings/B-runtime.md |
| D-files | Payload/artifact/repo files | high | 0 | 4 | 4 | findings/D-files.md |
| F-listeners | Listener lifecycle/profiles/templates | high | 0 | 3 | 4 | findings/F-listeners.md |
| G-agentgen | Agent generation/templates/profiles/file mgr | high | 0 | 3 | 4 | findings/G-agentgen.md |
| H-events | Event core + hooks (non-ws) | high | 0 | 2 | 3 | findings/H-events.md |
| I-infra | assets/paths/logging/c2-types/users/release | high | 0 | 2 | 3 | findings/I-infra.md |
| **Total (post-reverify)** | | | **3** | **26** | **30** | |

Arrows show the Opus re-verification adjustment. Base-pass total was 4H/24M/27L; after the Opus
re-review of A-auth and C-codeloading it is **3H / 26M / 30L** (one HIGH downgraded, several meds/lows added).
**Design decision 2026-09-23 (operators are peers, ownership is metadata-only — see below):** 2 med + 2 low
ownership/IDOR findings are closed as by-design, leaving **3H / 24M / 28L actionable**.

Two false positives retracted: (1) the A-auth `except A, B:` "SyntaxError" (valid under Python 3.14 /
PEP 758, verified against CPython 3.14.2); (2) see the entry-point downgrade below.

## G-agentgen — completed on Opus retry
This chunk was initially **blocked**: the real-time `[cyber]` safeguard terminated the reviewer on
both Opus 4.8 and Sonnet 5 (a content-based flag). Re-running on Opus per request cleared it. Result:
0 high / 3 med / 4 low. Notable: template-scoped payloads facade doesn't scope reads/deletes to its
bound template (cross-template IDOR); agent profile registered+started before type resolution with no
rollback (one bad profile aborts startup); generator build parameters (potential secrets) logged at
INFO and broadcast in the `AGENT_GENERATOR_UPDATED` event.

## Opus verification re-review (A-auth, C-codeloading)
A stronger Opus pass independently re-reviewed the two chunks holding all the HIGH findings.

**A-auth** — 3 prior findings CONFIRMED, 2 REFINED, 0 refuted; +1 med, +1 low new.
- CONFIRMED both HIGH plaintext-password findings (storage/compare + logging).
- REFINED the password-leak site list: the real `{!r}` leak sites are
  `user_accounts_service.py:93,112,303,334,675`; the base pass wrongly listed `:507`/`:544` (both use
  `{}` → safe `__str__`) and **missed `:303`** (leaks a *deleted* account's password).
- REFINED the timing-oracle mechanism: both paths run the full O(n) scan first, so the real signal is
  the plaintext `!=`-compare prefix leak on the known-username path, not an immediate-raise oracle.
- **NEW [med]** `events_websocket_service.py:379-440,457-483` — a live events socket is authorized only
  at handshake and never re-checked, so account deletion / role downgrade / permission revocation does
  not tear down the stream; combined with the confirmed "subscribe to every event" gap, a de-authorized
  operator keeps a full live event feed until they disconnect.

**C-codeloading** — 4 CONFIRMED, 4 REFINED, 0 refuted; +2 med, +1 low new. **HIGH count for this chunk
drops 2→1.**
- **DOWNGRADE (HIGH → LOW):** the entry-point "module escapes the component dir / arbitrary framework
  import" finding is overstated. `component_module.split(".")` can't emit a `..` segment, and an
  absolute/drive-rooted segment lands *outside* `consortium_root` so `relative_to` raises `ValueError`
  (the DoS path) rather than importing anything; the derived dotted name is always
  `consortium.components.plugins.*`, which can't collide with a live framework module. Hardening
  (reject separators/`..`, resolve + `is_relative_to`) is still worth doing, but it is not an RCE escalation.
- CONFIRMED the startup-DoS HIGH (malformed `entry_point` → uncaught `ValueError` aborts the whole scan),
  but corrected the trigger: the prior Windows `C:/...:Sym` example fails (`split(":",1)` eats the drive
  colon); a real trigger is a dot-free absolute path to an existing out-of-tree `.py`.
- CONFIRMED (strengthened) the async-load path skips label/dependency validation — and since `plugin_id`
  is a fresh uuid4 per instance, the id check is near-dead, so **label is the only real duplicate guard
  and the load/reload path omits it**.
- REFINED the TOCTOU finding: no lock is real, but the "double-start/overwrite" mechanism can't occur
  (per-instance uuid4 ids); the true gap is missing directory/label dedup + locking.
- **NEW [med]** `plugins_service.py:689` — reload "already-loaded" dedup compares
  `root_directory.parent` vs `path.parent`, which never matches the normal layout, so a failed-to-unload
  plugin is re-loaded as a second running instance.
- **NEW [med]** `component_loader_service.py:445` — non-domain exceptions from
  `_post_validate_component_object` (agent/listener profile author code) escape the batch catch set →
  one broken profile DoSes the whole discovery scan (reachable without any path trickery).

## The HIGH findings — fix first (now 3)

1. **Plaintext passwords, stored + compared + logged** (A-auth) — `user_accounts_service.py:331`
   stores/compares in plaintext, non-constant-time; `:264-269` logs old+new passwords; a missing
   redacting `__repr__` on `UserAccountModel` leaks the password on every `{!r}`. Opus-verified leak
   sites: `:93,112,303,334,675` (incl. a deleted account at `:303`), plus two more in I-infra
   (`users_service.py:157,185`). One file/log read = full operator compromise.
   *Fix needs a human migration call (touches the account model + on-disk accounts file format).*
2. **One bad manifest aborts all plugin loading** (C) — `component_loader_service.py:294-297`; uncaught
   `ValueError` from `relative_to` (outside the try, not `OSError`) → startup DoS. Opus confirmed; the
   C-reverify also found a *second* path to the same "one bad component DoSes discovery" outcome
   (`_post_validate_component_object`, `:445`).
3. **Plaintext password comparison (auth bypass-adjacent weakness)** (A-auth) — same root as #1's compare
   half at `user_accounts_service.py:331`; grouped as the second confirmed HIGH in A-auth's file.

(The former 4th HIGH — entry-point RCE — was downgraded to LOW by the Opus re-review, above.)

## Cross-cutting themes (appear in multiple chunks)

- **No object-level ownership / IDOR — RESOLVED, by design (2026-09-23).** The flat-RBAC / no-ownership
  posture seen across tasks (B), event subscriptions (A), files (D), listeners (F), assets (I) and the
  agent-facing facades (G) is **intended and now authoritative**: all operators are peers, and ownership
  metadata is attribution/display only, never an access-control input (see AGENTS.md "Authorization Model").
  These are therefore **not defects** — the following are closed as by-design: B's task read/delete ownership
  note; D's per-resource IDOR (low); G's cross-template payload "false isolation" (med) and unscoped
  file-manager reads (low); A's "operator subscribes to every event" (med); E's ownership note.
  *Not* closed by this decision (different axis — a revoked principal, not a peer): the WS re-auth /
  revocation-teardown finding (A-reverify med) stays open.
- **Credential / secret leakage through repr, logs, and event payloads.** Password repr (A + I sites);
  **log-format injection/suppression** where `logging_service.py:75-86` bakes `logger_name` into the
  loguru template; access tokens logged at DEBUG (I); listener `parameters` broadcast in lifecycle
  events + logs (F); **generator build parameters (keys/tokens) logged at INFO and broadcast in
  `AGENT_GENERATOR_UPDATED` (G: `agent_generators_service.py:374-388,424-433`)**.
- **Stale authorization on long-lived connections.** NEW from A-reverify: the events websocket is
  authorized only at handshake and never re-checked, so revocation doesn't cut the stream.
- **Unbounded growth / global (not per-principal) caps = DoS.** Terminal-task retention (B); agent maps
  (B); uploads/archives (D); registry `rglob("*")` (C); listener registry (F); unbounded event fan-out
  amplified by untrusted-agent events (H). Several sit on agent-drivable paths.
- **Non-atomic persistence / no-rollback lifecycle ops.** `.repository.json` in-place rewrite (D);
  listener-profile reload wipes all on any error (F); **agent-profile register+start before resolve with
  no rollback (G)**; event-handler registration non-atomic across its two indices (H); plugin
  reload-no-rollback + off-by-one dedup re-loads duplicates (C-reverify).
- **Narrow exception catches abort batch loading (recurring startup-DoS shape).** F (listener profiles),
  G (agent profiles), C (both the `ValueError` and `_post_validate_component_object` paths).

## What's solid (verified, no change needed)

- `websocket_tickets_service.py` — single-use synchronous pop, monotonic expiry, uniform errors, no logging.
- Per-task queues bounded via `QUEUE_MEMORY_LIMIT` (B); task state-machine CAS has no TOCTOU (B).
- On-disk storage paths always server-generated uuid4; download API sanitizes names; tar/zip-slip covered (D).
- `paths_service` is clean as a traversal surface — all static literal joins off `consortium_root` (I).
- `trigger_event` snapshots handlers before dispatch (self-deregistration safe); ExceptionGroup handling sound (H).
- **Opus-verified:** no `eval`/`exec`/`pickle`/`yaml.unsafe_load`/archive-extraction anywhere in scope;
  the `importlib` entry-point remains the only dynamic-exec surface, and its confinement forces imports
  to descend within the plugin's own directory (C-reverify). The `event_hook_registry_service`
  register-then-rollback pattern is the model the plugin reload path should copy.

## Suggested fix order

1. Password hashing + stop logging passwords/tokens (A + I sites) — highest impact; schedule the migration.
2. Wrap the `relative_to` ValueError AND guard `_post_validate_component_object` (C) — closes both
   startup-DoS paths; small, self-contained.
3. Log-format injection: stop interpolating `logger_name` into the loguru template (I).
4. Re-check authorization on the live events websocket / tear down on revocation (A-reverify).
5. Atomic `.repository.json` write + lock (D); load-then-swap for listener- and agent-profile reload (F/G);
   fix the plugin reload dedup off-by-one + add a load lock (C-reverify).
6. `iscoroutinefunction` guard + atomic two-index registration in the event core (H).
7. Stop broadcasting/logging secret-bearing build & listener parameters (G/F); scope the payload/file
   facades to their bound template/agent (G).
8. Add connection/listener validation to `AgentsService.dispatch_task_output_message` (B).
9. ~~Decide the ownership/IDOR posture~~ **DECIDED 2026-09-23: all operators are peers, ownership is
   metadata-only, never auth (baked into AGENTS.md "Authorization Model"). All ownership/IDOR findings
   closed as by-design. Only remaining task: optionally add "not an isolation boundary" docstrings to
   the payload/file-manager facades.**
10. Factor one exception-translation helper to stop internal-detail leaks (E/C/I).
11. Optionally harden the entry-point path (reject separators/`..`, resolve + `is_relative_to`) — low now,
    but cheap defense-in-depth.

## Coverage

All 9 service chunks reviewed — ~13,156 of ~13,255 services LOC, plus the whole API layer. Still out of
scope (not services): `server/objects` (~2,825), `server/models` (~1,191), `server/exceptions` (~5,181),
`server/database` (~143), the `framework/` and `client/` trees, and `components/` (off-limits per AGENTS.md).

## Notes for a future agent
- Resumable from `progress.json`; all 9 chunks are `done` against the base commit. G-agentgen's ledger
  note records that it needs Opus (the `[cyber]` safeguard blocks it on Opus 4.8 / Sonnet 5).
- A-auth and C-codeloading each have a companion `*-opus-reverify.md` with per-finding verdicts; the base
  `A-auth.md` / `C-codeloading.md` are unchanged, so read the reverify file for corrected line numbers
  and the entry-point downgrade rationale.
- If the tree has moved since `0a404028`, re-run affected chunks (set their status back to `todo`).
