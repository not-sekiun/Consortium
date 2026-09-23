# A-auth — Authentication / authorization / identity

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high.

Files:
- consortium/server/services/authorization_service.py (336 LOC)
- consortium/server/services/user_accounts_service.py (682 LOC)
- consortium/server/services/websocket_tickets_service.py (163 LOC)
- consortium/server/services/events_websocket_service.py (483 LOC)

Threat model: authenticated operators may be hostile; remote agents fully untrusted. Supporting
files (websockets_api.py, login_api.py, user_accounts_api.py, user_account_models.py, user_objects.py,
utils.py) were read only to confirm in-scope concerns; findings below are all about the four files.

## Findings

### [RETRACTED — FALSE POSITIVE] `except json.JSONDecodeError, KeyError:` at events_websocket_service.py:389
- **Status:** Not a defect. Retracted after empirical verification by the orchestrator on 2026-09-23.
- **What the reviewer claimed:** that `except A, B:` is Python-2-only syntax and a SyntaxError on
  Python 3, so the module cannot import and the server won't boot; and that AGENTS.md was wrong to call
  it valid.
- **Why it's wrong:** Python 3.14 (PEP 758) permits unparenthesized exception tuples in `except`/
  `except*` when there is no `as` clause, so `except json.JSONDecodeError, KeyError:` is valid and means
  "catch JSONDecodeError or KeyError" — exactly the code's documented intent. Verified by compiling the
  construct under the project's own interpreter (uv, CPython 3.14.2; `requires-python >=3.14`): it
  compiles cleanly. AGENTS.md's "Environment" note is therefore CORRECT, not wrong.
- **Lesson:** a version-specific syntax/platform claim must be checked against the actual target
  interpreter before being reported. The remaining findings below stand on their own.

### [SEV: high] Passwords stored, compared and persisted in plaintext with a non-constant-time compare
- **File:** consortium/server/services/user_accounts_service.py:331 (compare); also :168-171, :262-263, :485, :548
- **Category:** authn
- **What:** `authenticate_user_account_credentials` verifies with `user_account.password != password`
  against a plaintext-stored password (`UserAccountModel.password: str`, no hashing anywhere; written
  verbatim to the accounts file at :548). Python's `!=` on `str` short-circuits at the first differing
  byte, so it is not constant time. This is the service-layer root cause behind the separately-reported
  API-layer plaintext compare in user_accounts_api.py:212.
- **Failure scenario:** An attacker who can time login responses gets a side channel proportional to the
  matching password prefix length, and anyone who can read the accounts file on disk or a memory dump
  reads every operator credential directly. There is no defense in depth: a single file read is full
  compromise of every operator account.
- **Fix:** Hash passwords with a memory-hard KDF (argon2id / bcrypt) at creation/update; store only the
  hash; verify with the KDF's constant-time `verify`. Do the equality-independent verify even when the
  username is unknown (see enumeration finding) using a dummy hash.

### [SEV: high] Plaintext passwords written to logs (explicit INFO line and every `{!r}` of a user account)
- **File:** consortium/server/services/user_accounts_service.py:264-269; also :93, :112, :334, :375, :507, :544, :675
- **Category:** info-leak
- **What:** `update_user_account_by_user_account_id` logs both the old and new password in cleartext at
  INFO: `"Updated password for user account {} from '{}' to '{}'", user_account, old_password, password`.
  Separately, `UserAccountModel` overrides only `__str__` (user_account_models.py:12) and not
  `__repr__`, so pydantic's default repr renders every field including `password`. Every `{!r}` logging
  of an account (e.g. :93 retrieve, :334 "Authenticated user account", :507 file read, :675 write) emits
  the plaintext password into the debug log.
- **Failure scenario:** Log files, log shippers, or a support bundle now contain live operator
  credentials — longer-lived and more widely readable than the accounts file itself. `{!r}` at :334
  writes the password on every successful login.
- **Fix:** Never log password values; drop the old/new password from the :264-269 message. Give
  `UserAccountModel` a `__repr__` that redacts `password` (or type it as `pydantic.SecretStr`) so no
  `{!r}` can leak it.

### [SEV: med] Username-existence timing oracle in `authenticate_user_account_credentials`
- **File:** consortium/server/services/user_accounts_service.py:324-332
- **Category:** authn
- **What:** For an unknown username the method raises immediately (`get_user_account_by_username`
  throws before any password comparison); for a known username it runs the password compare. The error
  value is identical (good), but the work — and therefore the response time — differs, so username
  presence is observable by timing. `get_user_account_by_username` is itself an O(n) linear scan
  (:110-114), which widens the signal.
- **Failure scenario:** An unauthenticated attacker submits candidate usernames and distinguishes
  "valid user, wrong password" from "no such user" by latency, enumerating the operator roster before
  attacking passwords.
- **Fix:** Always perform a constant-time verify against a fixed dummy hash when the user is absent so
  both paths do equivalent work, then raise the single `UserAccountAuthenticationError`. (The dead
  `existing_usernames` scan at :324-326/:331 does not close this and should be removed — see design.)

### [SEV: med] Any operator can subscribe to every event type — no per-event authorization
- **File:** consortium/server/services/events_websocket_service.py:257-308 (`_handle_subscribe_action`), 457-484 (`handle_connection`)
- **Category:** perms
- **What:** Authorization is a single `USE_EVENTS_WEBSOCKET` permission checked once at the handshake
  (websockets_api.py:122). Once connected, `_handle_subscribe_action` registers the connection's sender
  for any event type in `EventType` with no role/ownership filtering. Every authenticated operator can
  therefore receive every server event.
- **Failure scenario:** In a C2 with multiple operators of differing trust, a low-privilege operator
  subscribes to all event types and passively receives other operators' activity (agent check-ins,
  tasking, results) that their role would not otherwise grant. Confused-deputy: the socket faithfully
  relays events the subscriber was never authorized to see.
- **Fix:** Gate subscription per event type against the caller's permissions (pass the authenticated
  `user`/role into the handler and check each requested event), or document explicitly that the events
  stream is all-or-nothing and that `USE_EVENTS_WEBSOCKET` grants full visibility by design.

## Design notes
- **Dead/confusing logic in `authenticate_user_account_credentials` (:324-332).** `existing_usernames`
  is built by scanning all accounts, but `get_user_account_by_username` already guarantees the account
  exists, so `username not in existing_usernames` at :331 can never be true. Drop the list and the
  clause; keep only the constant-time password verify. Two full scans (`get_all_user_accounts` +
  `get_user_account_by_username`) run per login attempt today.
- **Centralize password verification** (user_accounts_service.py:331; also user_accounts_api.py:212).
  Login (this service, :331) and self-service change (user_accounts_api.py:212) each re-implement
  `plaintext == plaintext`. A single
  `verify_password(account, candidate)` helper (constant-time, hash-based) used by both would remove the
  divergence and make the correct comparison the only comparison available.
- **`get_user_account_by_username` is O(n) (:110-114).** Accounts are keyed by ID only; a secondary
  username->account index would make lookup/auth constant time and shrink the timing surface above.
- **Duplicated event-validation boilerplate.** `_handle_subscribe_action` and
  `_handle_unsubscribe_action` (:257-359) repeat the same "unknown event type / already-in-wrong-state"
  loop with mirrored messages; a shared validator taking the desired-state predicate would halve it and
  keep the two enforcement points from drifting (note the subscribe errors attach `detail={"event":...}`
  while the unsubscribe errors do not — already drifted).
- **`create_role` accepts role names the loader will later reject (authorization_service.py:228-248).**
  It performs no `^[A-Z][A-Z0-9_]*$` validation, so a role created at runtime can silently fail to load
  on the next `load_server_role_permissions`. Documented in the docstring, but validating on create
  would make the in-memory and on-disk contracts agree. Low priority.

## Notes
- Password hashing (the fix for the two high authn/info-leak findings) is a cross-cutting change that
  touches `UserAccountModel` and the on-disk accounts-file format, which are outside the four in-scope
  files. It needs a human decision on migration of existing plaintext account files.
- (Struck) The earlier note here inferred a missing import/lint gate from the supposed SyntaxError;
  that finding was retracted (valid under Python 3.14 / PEP 758), so this inference no longer applies.
- `redeem_ticket` (websocket_tickets_service.py) is sound: single-use via synchronous `dict.pop`,
  monotonic-clock expiry, uniform `InvalidWebsocketTicketError` for unknown/expired/redeemed (no
  oracle), ticket value never logged. The global `MAX_OUTSTANDING_TICKETS` cap has no per-principal
  split, but that cross-operator DoS is already mitigated at the boundary (websockets_api.py `20/minute`
  slowapi limit), consistent with the repo's "policy at the boundary" philosophy — no finding.
