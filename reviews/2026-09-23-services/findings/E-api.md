# E-api — HTTP/WS API layer

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: low.
Files: login_api.py, logout_api.py, server_api.py, websockets_api.py, tasks_api.py,
users_api.py, user_accounts_api.py, agents_api.py, agent_templates_api.py,
agent_generators_api.py, listeners_api.py, listener_templates_api.py,
repository_apis/_repository_api_factory.py, repository_apis/artifacts_api.py,
repository_apis/payloads_api.py, repository_apis/assets_api.py.
(Confirmed against supporting files: server_dependencies.py, server_exception_handlers.py,
http_exceptions.py, base_api_exception.py, utils.py — not themselves reviewed.)

## Findings

### [SEV: med] Catch-all handler echoes internal exception type and message to the client
- **File:** listeners_api.py:176-182, 227-233, 276-282; agent_generators_api.py:188-194, 239-245, 286-292
- **Category:** info-leak
- **What:** The final `except Exception as exc:` on the start/stop/cancel handlers raises
  `InternalServerError(detail={"type": type(exc).__name__, "message": str(exc)})`. The
  `BaseAPIError` handler serializes `exc.to_json()` including `detail` straight into the
  500 response body (server_exception_handlers.py:137-141, base_api_exception.py:40-47), so
  the raw internal exception class name and message reach the caller.
- **Failure scenario:** An authenticated operator with START/STOP/CANCEL permission triggers
  any unforeseen error deep in a listener/generator component (a socket bind failure, an OS
  error, a bug). `str(exc)` for such errors routinely contains filesystem paths, host/port
  values or internal object detail, all of which are handed to the client. This directly
  contradicts the sibling `ListenerFatalError`/`AgentGeneratorFatalError` branch immediately
  above it, which deliberately returns a generic body and logs server-side.
- **Fix:** Make the catch-all mirror the FatalError branch: `raise InternalServerError() from None`
  and log the exception server-side (or drop the catch-all entirely and let the service's
  logging + a global 500 handler take it). Never put `str(exc)`/type names in `detail`.

### [SEV: low] Plaintext, non-constant-time password re-auth check at the API boundary
- **File:** user_accounts_api.py:211-213
- **Category:** security
- **What:** The self-service password change re-authenticates with
  `request_data.password.old_password != user_account.password`, a plaintext `!=` comparison
  performed in the handler. This both relies on plaintext password storage being readable at
  the API layer and uses a non-constant-time compare.
- **Failure scenario:** A stolen-JWT holder needs the old password to change it (good), but the
  `!=` compare is a timing side-channel on the stored secret, and the check being in the API
  layer (rather than a service method) means the boundary handles the cleartext secret directly.
  Low practical impact given the attacker is already authenticated, but it is the wrong place
  and the wrong primitive for a secret comparison.
- **Fix:** Delegate re-authentication to a service method that does a constant-time comparison
  (`hmac.compare_digest`) against a hashed credential; keep the cleartext secret out of the
  handler.

### [SEV: low] Unpaginated collection endpoints return the entire set
- **File:** users_api.py:60-66; user_accounts_api.py:73-79; agents_api.py:63-66; tasks_api.py:57-69; listeners_api.py:74-86; agent_generators_api.py:82-94; repository factory create_get_all_resources_endpoint (_repository_api_factory.py:43-65)
- **Category:** dos
- **What:** Every `/all` endpoint returns one model per resource with no limit/offset. Per-item
  event logs are omitted to bound per-item size, but the number of items is unbounded.
- **Failure scenario:** With very large numbers of agents/tasks/resources a single authenticated
  request materializes and serializes the whole set in memory. Authenticated-only and consistent
  with the project's "limits are opt-in policy at the boundary" philosophy, so this is a noted
  residual risk rather than a defect. Flagging so a human decides whether a cap belongs here.
- **Fix:** Optional: offer limit/offset on the collection endpoints (default unbounded) as the
  detail endpoints already do for event logs.

### [SEV: low] Upload can forward a `None` resource name to the create handler
- **File:** _repository_api_factory.py:249, 261
- **Category:** crash
- **What:** `name=name if name else file.filename` is passed to the create handlers. When the
  caller supplies no `name` and the multipart part carries no `filename` (`file.filename is None`),
  `None` is forwarded as the resource name. The directory branch guards `file.filename is None`
  for the archive-format path but the name argument itself can still be `None`.
- **Failure scenario:** A crafted multipart upload with empty `name` and no `filename` reaches the
  asset create service with `name=None`; whether that is a clean 4xx or an unhandled 500 depends on
  the service. Low confidence / low impact — flagged to confirm the create handlers tolerate `None`.
- **Fix:** Fall back to a non-None default (e.g. the resource id or a generated name) before calling
  the handler, or validate `name`/`filename` presence and return a 422.

## Design notes
- The catch-all `except Exception -> InternalServerError(detail=...)` plus the identical
  `FatalError -> InternalServerError()` branch are copy-pasted across all six start/stop/cancel
  handlers in listeners_api.py and agent_generators_api.py. Factoring the framework-exception ->
  api-exception translation + a single safe fallback into a shared helper/decorator would remove
  the duplication and eliminate the info-leak (finding 1) in one place.
- Every module repeats the `try: svc_call() except svc_excs.X as exc: raise api_excs.X.from_consortium_exception(...) from None` shape. It is readable and explicit, but a declarative exception-map
  (service-exc class -> api-exc class) applied by one wrapper would collapse a lot of near-identical
  boilerplate. Optional; current form trades brevity for grep-ability.
- `repository_apis/_repository_api_factory.py` is genuinely clean: the six `create_*_endpoint`
  factories share auth/validation/exception-translation uniformly, and the three repository modules
  are thin `add_api_route` wiring. The path-traversal handling in the download factory
  (PureWindowsPath name stripping, exists_on_disk pre-check, temp-dir + BackgroundTask cleanup) is
  careful and well-commented. No change needed.
- Doc/schema bug: `get_all_agent_generators` declares `responses={200: {"model": AgentGeneratorModel}}`
  (singular) while the handler returns and is annotated `list[AgentGeneratorModel]`
  (agent_generators_api.py:78-79). The OpenAPI schema advertises a single object for a list endpoint.
  Compare the correct `list[...]` declarations on the other `/all` routes.

## Notes
- Websocket auth (server_dependencies.py) is solid and out of scope to report on: tickets are
  server-side random tokens bound to the issuing session's user_id, single-use, TTL-bounded, and
  every rejection reason collapses to WS_1008 with per-reason detail only in the debug log. Ticket
  issuance is rate-limited (20/min) and guarded by a server-wide cap; login is 5/min with 401
  fingerprint-suppression. No forgery/oracle issue found in the API layer.
- Authorization is uniformly role-based via `AuthorizeUserRequest`; there is no per-resource
  ownership model (any operator with the role permission may act on any agent/listener/resource).
  This appears intentional for a shared-operator C2 and is not reported as IDOR, but a human should
  confirm that "no ownership scoping" is the intended trust model.
- Finding 4 (upload None-name) needs a glance at the assets create service to confirm severity;
  flagged low-confidence.
- The prior scan artifact `CLAUDE-SECURITY-20260819-074658/` in the repo root contains only run
  metadata (no findings file), so nothing here overlaps a previously reported issue.
