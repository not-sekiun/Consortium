# Consortium review — remediation triage

**Implementation handoff (triage done 2026-09-24): see `PLAN.md`. It supersedes the Q1 ordering below.**

**Implementation status (local commits on `fix/code-review-fixes`, not pushed):**
- [x] PLAN #8 per-instance template binding (`515320ca`) - not a Q1 row; design item from the triage.
- [x] PLAN #3 component loader startup DoS = Q1 #3 (`8f5cf068`)
- [x] PLAN #5 API catch-alls = Q1 #5 (`58c03af7`)
- [x] PLAN #7 sync event handlers = Q1 #7 (`75ada98c`)
- [x] PLAN #4 log-format injection = Q1 #4 (`17b87936`)
- [x] PLAN #2 atomic JSON writes = Q1 #2 (`25aa1074`)
- [x] PLAN #1 password / session-id redaction + `log_secrets` = Q1 #1 (`54ff7367`)
- Q1 #6 (secret build/listener params) remains on hold per PLAN.md.

**Q3 mop-up status (2026-09-24, committed; starts at tag `q3-low-complexity-low-gain-start`):** all
items actioned in one pass, landed as nine commits, one per item. Suite green and lint clean. See
the "Q3 mop-up" section in `PLAN.md` for per-item notes. Two did not become code changes:
the E-api upload `None`-name finding is a **non-issue** (both asset create handlers document
and support `name=None`, falling back to the generated UUID), and making `normalize_uuid`
canonicalize is **deferred** as a cross-service behaviour change rather than a mop-up.

Base commit `0a404028a28d402b7e8694e99c1cfa550782d4a6`. Derived from the 9 chunk findings +
the A-auth / C-codeloading Opus re-reviews. See `SUMMARY.md` for context and `findings/` for detail.

**Axes.** *Complexity* = engineering effort + blast radius of the change (Low = localized/mechanical;
High = migration, cross-cutting, or design decision). *Gain* = risk reduction weighted by finding value
(severity + reachability). Order of attack: **Q1 first** (cheap, high payoff), then Q2 (schedule focused
sessions), Q3 as mop-up, Q4 only if the deployment model demands it.

```
                 LOW COMPLEXITY                         HIGH COMPLEXITY
             +----------------------------------+----------------------------------+
   HIGH GAIN | Q1  DO FIRST                     | Q2  SCHEDULE (focused sessions)  |
             |  1 Redact password repr (+drop   |  A Password hashing + on-disk    |
             |    {!r}) — kills A-auth & I leaks |    accounts migration + const-   |
             |  2 Atomic .repository.json write  |    time compare  [HIGH finding]  |
             |  3 Wrap relative_to ValueError +  |  B Repository concurrency lock   |
             |    guard _post_validate  [HIGH]   |  C Partial-failure reconcile     |
             |  4 Log-format injection (logger_  |  D WS re-auth / revocation       |
             |    name out of loguru template)   |  E Profile register→resolve      |
             |  5 E-api catch-all: no str(exc)   |    rollback + load-then-swap      |
             |  6 Stop logging/emitting secret   |  F Arbitrary source-path ingest  |
             |    build/listener params          |    confinement (if reachable)    |
             |  7 iscoroutinefunction guard (H)  |  (G IDOR decision: DONE - peers) |
             +----------------------------------+----------------------------------+
   LOW GAIN  | Q3  MOP-UP (batch in one pass)    | Q4  DEFER (intentional / low ROI)|
             |  - Plugin reload dedup off-by-one |  - Unbounded-registration caps   |
             |  - H two-index reg reorder        |  - Per-agent task-retention cap  |
             |  - Cross-template payload scoping |  - Collection pagination         |
             |  - Pin tar filter='data'          |  - Archive-bomb size caps        |
             |  - Consolidate UUID canonicalize  |  - Auto check-in event debounce  |
             |  - create/add dup-id guard, None- |  - importlib.reload identity      |
             |    name guard, stale-serialize,   |    (prefer pop+import)            |
             |    caller-dict copy, decorator    |  (all "policy at the boundary"   |
             |                                    |   per AGENTS.md — need a human    |
             |                                    |   deployment-model call first)   |
             +----------------------------------+----------------------------------+
```

## Q1 — Low complexity, High gain — DO FIRST (next session, in this order)

| # | Fix | Finding(s) | Files (approx) | Why cheap / why high gain |
|---|---|---|---|---|
| 1 | **Redact `password` in `UserAccountModel.__repr__`** (or type it `SecretStr`); drop the `{!r}` debug lines | A-auth HIGH #1 (leak half); I-infra med + low | `models/...UserAccountModel`; `user_accounts_service.py:93,112,303,334,675`; `users_service.py:75-77,157,185` | One model change neutralizes **every** repr leak site across two chunks (incl. a deleted-account password at `:303`). Does *not* need the hashing migration. Highest value, smallest change. |
| 2 | **Atomic metadata write**: serialize to temp file + `os.replace()`, keep a `.bak` | D-files med (non-atomic rewrite) | `repository_service.py:238-249` | ~10 lines, self-contained; prevents one interrupted write from bricking the entire `.repository.json` index (whole-repo outage). |
| 3 | **Wrap the `relative_to` `ValueError`** and **guard `_post_validate_component_object`** / broaden the batch catch to a catch-all-per-component | C-codeloading **HIGH** (startup DoS) + C-reverify new med (`_post_validate` path) | `component_loader_service.py:294-297,445,478-489` | Closes both "one bad component bricks startup" paths. Small, local. This is the confirmed HIGH after the entry-point downgrade. |
| 4 | **Stop interpolating `logger_name` into the loguru format template** — pass it as an `extra` field or escape `{}`/`<>` | I-infra med (log-format injection) | `logging_service.py:75-86` | Localized to one formatter; stops log-line suppression and markup forging by any controllable logger name. |
| 5 | **API catch-all: `raise InternalServerError() from None` + log server-side** (or one shared translate helper) | E-api med (info-leak, 6 sites) | `listeners_api.py:176-282`; `agent_generators_api.py:188-292` | Mechanical; mirrors the existing FatalError branch. A shared helper also kills the copy-paste. |
| 6 | **Log parameter *names*, not values; redact secret-bearing params from event `data`** | G med (generator build params); F low (listener params) | `agent_generators_service.py:374-388,424-433`; `listeners_service.py` event/log sites | Small edits at the emit/log sites; stops broadcasting keys/tokens to every event subscriber and the log. |
| 7 | **Reject non-coroutine handlers at registration** (`inspect.iscoroutinefunction`) | H med (sync handler defeats isolation) | `events_service.py` register (~:50-80) | A few lines at one function; prevents a mis-registered `def` handler from aborting the entire event fan-out. |

## Q2 — High complexity, High gain — SCHEDULE (each is its own focused unit)

- **A. Password hashing + accounts migration** (A-auth HIGH; also resolves E-api low re-auth). Touches the
  account model, the on-disk accounts file format, login, self-service password change, and the compare
  (`hmac.compare_digest`). **Needs a human decision** on migration strategy (rehash-on-next-login vs one-shot).
  Highest-impact fix overall; deliberately separated from Q1#1 (which stops the *leaks* immediately without migration).
- **B. Repository concurrency lock** (D med): one `threading.Lock` around all `_resources`/`_reserved_resource_ids`
  mutation and every `save_repository_metadata()`, or a single dedicated executor. Medium effort (many call sites)
  but factoring the create/add helper (D design note) makes it one-place.
- **C. Partial-failure reconcile** (D med): reorder persist-before-irreversible-disk-op, or tolerate/reconcile
  missing-on-disk at load. Design care needed.
- **D. Events-websocket re-authorization / revocation teardown** (A-reverify med): live socket authorized only at
  handshake; add revocation-driven teardown. Touches ws connection lifecycle. Pairs with the "subscribe to every
  event" gap.
- **E. Profile register→resolve ordering + rollback** (G med) and **load-then-swap reloads** (F med, G, C-reverify):
  resolve/validate before commit, roll back on failure; make reload non-destructive.
- **F. Arbitrary source-path ingest confinement** (D med, path traversal): resolve + `is_relative_to` an ingest
  base, reject symlinks/`..`. Gate on the human ruling of the agent/component trust boundary (may be Q1-cheap if the
  decision is "trusted-only, document it").
- ~~**G. Ownership / IDOR policy decision**~~ **DECIDED 2026-09-23: all operators are peers; ownership is
  metadata-only, never an auth input. Baked into AGENTS.md "Authorization Model".** All ownership/IDOR findings
  (B task read/delete, D per-resource IDOR, G cross-template payload + file-manager reads, A subscribe-to-all-events,
  E ownership note) are **closed as by-design — do not implement scoping**. The only residual is an optional Q3
  docstring nicety (label the payload/file-manager facades "not an isolation boundary"). NOTE: this does *not* close
  the WS re-auth/revocation finding (Q2-D) — that is a revoked principal, not a peer.

## Q3 — Low complexity, Low/Med gain — MOP-UP (batch in a single cleanup pass) — DONE 2026-09-24

- [x] Plugin reload dedup off-by-one (`plugins_service.py:689` — now `is_relative_to(path.parent)`).
- [x] Event handler two-index registration reorder / hashability check (`events_service.py:74-80`).
- [x] Payload / file-manager facade docstrings: state they are "not an isolation boundary" (G) — the *only*
  residual of the ownership decision; do NOT add scoping checks (ownership is metadata-only per AGENTS.md).
- [x] Pin tar `filter='data'` explicitly at extraction (D low) — defense-in-depth + regression test.
- [~] Consolidate the three UUID helpers (B/D/F): the two identical `_canonicalize_uuid` copies are now one
  shared `canonicalize_uuid` in `server/utils.py`. Making `normalize_uuid` itself canonicalize is **deferred**
  as a cross-service behaviour change, not a mop-up — see PLAN.md.
- Small correctness nits: [x] `create` vs `add` dup-id guard (G); [n/a] upload `None`-name guard (E — non-issue,
  both asset create handlers document and support `name=None`); [x] `AGENT_CHECKED_IN` serialize-after-update (B);
  [x] `update_listener`/`update_agent_generator` operate on a copy not the caller's dict (F/G); [x] apply the
  `log_and_propagate_error` decorator to `AgentFileManagerService` (G).

## Q4 — High complexity, Low gain — DEFER (intentional design per AGENTS.md, or low ROI)

These are mostly the "limits are opt-in policy at the boundary" items — deliberately unbounded by design, so
"fixing" them is a product decision, not a bug fix. Revisit only if the deployment threat model changes.
- Unbounded agent/registration caps; per-agent task-retention cap; collection-endpoint pagination; archive-bomb /
  upload size caps; auto check-in event debounce; `importlib.reload` class-identity (prefer `sys.modules.pop` +
  fresh import).

## Suggested next-session plan
Knock out **Q1 #1–#7** in one session (all localized; no migration). They clear the confirmed HIGH startup-DoS,
stop every password/secret leak vector without a migration, and close the log-injection and API info-leak. Then
book a dedicated session for **Q2-A (password hashing)** — the last remaining HIGH-gain migration.

**Q2-G (ownership/IDOR) is DECIDED (2026-09-23): all operators are peers, ownership is metadata-only, baked into
AGENTS.md. All ownership/IDOR findings closed as by-design.** This removed the largest batch of Q2/Q3 work; the
only residual is the optional facade docstring nicety in Q3.
