# I-infra — Supporting infra (assets, paths, logging, c2 types, users, release)

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high. Files: assets_service.py, paths_service.py, logging_service.py, c2_types_service.py, users_service.py, release_service.py.

Threat model: authenticated operators may be hostile; remote agents fully untrusted. Cross-cutting
items already covered elsewhere were deliberately not re-reported as primary findings: the
plaintext-password storage/compare and the `UserAccountModel` default-repr credential leak (A-auth),
and the repository-layer traversal/DoS/IDOR/atomicity issues (D-files). Where an in-scope file adds a
*new* call site of one of those, it is flagged with an explicit cross-reference.

## Findings

### [SEV: med] Log-format injection / log suppression via `logger_name` baked into the loguru format template
- **File:** consortium/server/services/logging_service.py:75-86 (`_log_formatter`); triggered by dynamic `logger_name` bindings e.g. objects/agent_objects.py:208, objects/task_objects.py:173, framework/plugins/base_plugin.py:103, framework/listeners/base_listener.py:174, services/repository_service.py:68
- **Category:** injection
- **What:** `_log_formatter` returns a loguru format *template* built by string-concatenating the runtime `logger_name` into it (`... + color + logger_name + "</></>: {message}\n{exception}"`). loguru re-parses that returned template for both `{field}` placeholders and `<...>` color markup on every record. Because `logger_name` is embedded in the template (not passed as a substituted field value like `{message}` is), any markup or brace characters in a logger name are interpreted, not printed literally.
- **Failure scenario:** A logger bound with a name containing `{` or `}` (e.g. an agent/listener/plugin/task whose `__str__` includes an operator- or agent-supplied name) makes loguru raise a format error while rendering; with loguru's default `catch=True` the record is dropped to stderr instead of the sink, so an attacker who controls a name can selectively suppress the log lines emitted under that logger. A name containing `<red>`/`</>` etc. injects colour markup into every line from that logger (log-forging / garbled operator output). Impact rises to high if any embedded name is remotely controlled (e.g. an agent-chosen name reaching `str(agent)`).
- **Fix:** Do not interpolate dynamic text into the returned format template. Keep `logger_name` a substituted field (e.g. resolve it into `record["extra"]` and reference `{extra[logger_name]}`), or escape braces and markup (`name.replace("{","{{").replace("}","}}")` plus stripping/escaping `<`/`>`) before concatenation.

### [SEV: med] Plaintext operator password written to logs via `{!r}` of `User` on login/logout
- **File:** consortium/server/services/users_service.py:157 (`self._logger.debug("- {!r}", user)`), :185 (same on logout)
- **Category:** info-leak
- **What:** `User.__repr__` renders `User(user_account={self.user_account!r})`, and `UserAccountModel` overrides only `__str__` (not `__repr__`), so pydantic's default repr prints every field including `password`. These two debug lines therefore emit the operator's cleartext password into the log stream on every login and logout.
- **Failure scenario:** With a DEBUG-level sink (the default level is operator-configurable and DEBUG is used throughout), each successful login/logout writes `User(user_account=UserAccountModel(..., password='...'))` to stdout and any file sink, persisting live credentials in logs and support bundles.
- **Fix:** Same root cause as the A-auth "UserAccountModel default repr leaks password" finding; central fix is redacting `password` in `UserAccountModel.__repr__` (or typing it `SecretStr`). Reported here because these two sites are in-scope and were not enumerated in A-auth. As a local mitigation, drop the `{!r}` debug lines or log `str(user)` only.

### [SEV: low] Access token (JWT subject) logged at DEBUG in `get_user_by_access_token`
- **File:** consortium/server/services/users_service.py:75-77
- **Category:** info-leak
- **What:** The lookup logs the raw `access_token` value it was queried with (`"Retrieved user by access value '{}': {!r}"`), and the `{!r}` also drags in the password via the same `User`/`UserAccountModel` repr issue above.
- **Failure scenario:** Session-identifying tokens (and, via repr, credentials) land in DEBUG logs, aiding session correlation/replay by anyone who can read logs.
- **Fix:** Log a non-sensitive correlator (e.g. `user.user_id`) instead of the token, and use `str(user)` not `{!r}`.

### [SEV: low] Non-constant-time access-token comparison / linear session scan
- **File:** consortium/server/services/users_service.py:73-79
- **Category:** security
- **What:** `get_user_by_access_token` linear-scans all sessions and compares with `str(user.json_web_token.subject) == access_token`, a short-circuiting non-constant-time compare.
- **Failure scenario:** Marginal timing side channel on the session-subject value; low because the subject is a random UUID that is normally signature-verified upstream before this lookup. Noted for completeness alongside the analogous A-auth password-compare finding.
- **Fix:** If this lookup is ever reached with unauthenticated input, index sessions by subject in a dict and/or use `hmac.compare_digest`.

### [SEV: low] `delete_asset_by_resource_id` reads asset JSON on the event loop before the threaded delete
- **File:** consortium/server/services/assets_service.py:457-465
- **Category:** dos
- **What:** The delete path snapshots `asset.to_json()` (which, per the inline comment, reads from disk — for a directory asset this can walk the tree) directly on the event-loop thread, while only the subsequent `delete_resource_by_resource_id` is offloaded via `asyncio.to_thread`.
- **Failure scenario:** Deleting a large directory asset stalls the event loop during the synchronous `to_json()` read, degrading concurrent request handling.
- **Fix:** Move the `to_json()` snapshot into the same `asyncio.to_thread` call (or a preceding one) so no blocking disk I/O runs on the loop.

## Design notes
- assets_service.py:57-77 (`_build_asset_resource_data`): attribution stores a *snapshot* of `username` + `role` at create/update time. After a later rename or role change on the uploading account, the asset's recorded attribution silently diverges from the live account. If that snapshot is ever used for a trust/authz decision this is a correctness hazard; if it is purely display metadata, document it as intentionally point-in-time.
- paths_service.py: confirmed clean as a traversal surface — every path is a static literal join off `consortium_root` (derived from `__file__`, not user input); no user-controlled `join`/`/` anywhere. The traversal chokepoint the theme expected lives in repository_service (covered by D-files), not here. `_auto_create_missing_directories` correctly places the "file where a directory expected" raise outside the `wrap_filesystem_errors` block; logic verified.
- logging_service.py:382-392: when `logging_config.log_file` is set but `rotation`/`retention` are `None`, the file sink grows unbounded. This is consistent with CLAUDE.md's "limits are policy, default to off" philosophy (they are explicit config knobs), so noted rather than filed as a defect.
- release_service.py:60-76 and paths_service error raises embed the absolute filesystem path (`str(self._release_json_file)`, etc.) into typed error messages. Minor internal-path disclosure, but these are static server paths and the pattern is codebase-wide; low priority.
- c2_types_service.py:143-159: `get_compatible_listener_types_from_agent_type_name` iterates `agent_profile.agent_template.compatible_listener_types` assuming it is always iterable; if a template ever leaves it `None`, this raises `TypeError` rather than returning empty. Guard with `or ()` if templates do not guarantee the attribute.

## Notes
- assets_service IDOR: `get_asset_by_resource_id`, `get_all_assets`, `update_asset_by_resource_id`, `delete_asset_by_resource_id` carry no per-resource ownership/authz — any resource_id is fully accessible. This is the same cross-operator/cross-agent IDOR class already filed in D-files ("No per-resource ownership/authz"); not re-scored here since assets_service is a thin wrapper over the repository layer that finding covers.
- users_service session mutations are NOT an IDOR: the API layer gates them with distinct permissions (users_api.py update_own_display_name -> `UPDATE_OWN_USER` on `/me` vs update_user_display_name_by_user_id -> `UPDATE_USER_BY_USER_ID` on `/{user_id}`; logout_api.py -> `LOGOUT_USER_BY_USER_ID`). Authorization is correctly enforced at the boundary; the unrestricted service methods are by design per CLAUDE.md (business logic at the API surface). Verified, no finding.
- `self._users` mutation in `login_user`/`logout_user_by_user_id` is race-free under the single-threaded asyncio model (both are synchronous, no `await` between read and mutate). No lock needed as written; flagged only if either is ever made `async` with an interior await.
