# Consortium core-services review — 2026-09-23

Incremental, resumable security + correctness review of the core service layer.
Built because `/code-review` is single-shot (no chunking, no disk state) and would
lose all progress on a 5-hour usage lockout + stale prompt cache.

- **Base commit:** `0a404028a28d402b7e8694e99c1cfa550782d4a6`
- **Effort:** high (bugs + security; C2 threat model)
- **Ledger:** `progress.json` is the source of truth for what's done.

## How to run / resume (for me, the user, or a future agent)

1. Open `progress.json`. Find the **first chunk with `status: "todo"`**.
2. Review **only that chunk's files** against the [checklist](#review-checklist) below.
   Keep the working set small — one chunk fits comfortably inside usage limits.
3. Write results to the chunk's `findings_file` using the [findings template](#findings-file-template).
4. In `progress.json`, set that chunk's `status: "done"`, `reviewed_commit` to the
   current `git rev-parse HEAD`, and `reviewed_at` to today.
5. Repeat until no `todo` chunks remain, then write `SUMMARY.md`.

A dead session loses **at most one chunk**. The next agent starts cold from the ledger,
not from context — stale cache is irrelevant.

## Chunks (review order: auth → code-loading → runtime → files)

| Order | ID | Theme | LOC | Status |
|---|---|---|---|---|
| 1 | `A-auth` | Auth, authz, identity, websocket ticketing | 1,664 | todo |
| 2 | `C-codeloading` | Plugin + component dynamic loading (RCE surface) | 2,338 | todo |
| 3 | `B-runtime` | Agent + task runtime (command dispatch) | 1,684 | todo |
| 4 | `D-files` | Payload/artifact/repository file handling | 1,884 | todo |

Order rationale (C2 threat model): auth and dynamic code-loading are where a real bug
is catastrophic, so they go first while attention/budget is freshest.

## Review checklist

Per chunk, look for:
- **AuthZ gaps** — endpoints/actions missing an ownership or role check; confused-deputy.
- **AuthN** — token/ticket forgery, weak session/ticket lifetime, missing revocation.
- **Injection / RCE** — dynamic import, `eval`/`exec`, unsafe deserialization, plugin code trust.
- **Path traversal** — user-controlled paths in payload/artifact/repo handling.
- **Concurrency** — races on shared state, TOCTOU, unbounded buffers/queues.
- **Input validation** — trust boundaries between agent → server and client → server.
- **Error handling** — swallowed exceptions, info leaks in errors, partial-failure states.
- **Correctness** — logic bugs in the modified/core paths.

Cross-reference `CLAUDE.md` / `AGENTS.md` conventions and the prior scan
`CLAUDE-SECURITY-20260819-074658` to avoid re-reporting known items.

## Findings file template

```markdown
# <chunk id> — <theme>

Reviewed at commit <sha> on <date>. Files: <list>.

## Findings

### [SEV: high|med|low] <one-line title>
- **File:** path:line  (REQUIRED — file + approximate line/line-range, e.g. `foo.py:118-134`; rough is fine, never omit. List each site if it spans several.)
- **What:** the defect.
- **Failure scenario:** concrete inputs/state -> wrong/unsafe outcome.
- **Fix:** suggested direction.

(repeat; if none: "No issues found. Checked: <what>.")

## Notes
- Anything deferred, uncertain, or worth a human's eyes.
```
