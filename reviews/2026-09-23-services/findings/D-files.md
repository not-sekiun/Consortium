# D-files — Payload / artifact / repository file handling

Reviewed at commit 0a404028a28d402b7e8694e99c1cfa550782d4a6 on 2026-09-23. Effort: high.
Files:
- consortium/server/services/payloads_service.py (686 LOC)
- consortium/server/services/artifacts_service.py (519 LOC)
- consortium/server/services/repository_service.py (679 LOC)

Supporting files read to confirm concerns (not themselves in scope): objects/repository_objects.py, services/utils.py, services/agent_file_manager_service.py, api/repository_apis/_repository_api_factory.py, api/repository_apis/payloads_api.py.

Overall the on-disk storage path is genuinely safe by construction: every resource is stored under a server-generated `uuid4` (`repository_directory_path / str(unique_resource_id)`), never under any operator/agent-supplied string, and the download API sanitizes `name` with `PureWindowsPath(...).name`. The real defects are in concurrency, atomicity/partial-failure of the metadata index, an arbitrary source-path move/copy primitive, and unbounded-input DoS. The service layer does rely on the API/stdlib layers for name-sanitization and archive-member safety rather than validating independently.

## Findings

### [SEV: med] Unsynchronized shared state and concurrent non-atomic metadata writes across worker threads
- **File:** repository_service.py:234-249 (save_repository_metadata), 313-323 (create_file), 382-395 (add_file), 456-467 (create_directory), 529-542 (add_directory), 581-588 (update), 627-643 (delete), 261-263 (reserve_resource_id); payloads_service.py:172-183, 268-280, 367-379, 465-477, 570-576, 627-630; artifacts_service.py:158-165, 222-230, 295-303, 362-370, 421-427, 467-470
- **Category:** concurrency
- **What:** Every payloads/artifacts mutation is dispatched with `asyncio.to_thread(...)`, so concurrent REST requests run `RepositoryService` methods on different worker threads. `RepositoryService` has no lock: `self._resources` (dict) and `self._reserved_resource_ids` (set) are mutated concurrently, and `save_repository_metadata()` opens the single `.repository.json` in `"w"` from multiple threads at once.
- **Failure scenario:** Two simultaneous `create_artifact_file` / `delete_payload` requests interleave: their `save_repository_metadata()` writes race on the same file handle path (truncate-then-write), so one resource's record is lost, or the file is written with interleaved/partial JSON; concurrent dict/set mutation can also drop or resurrect entries. Result: the persisted index diverges from disk, and on next `load_repository_metadata` an unsynced/JSON error can make the whole repository unloadable.
- **Fix:** Guard all `_resources` / `_reserved_resource_ids` mutation and every `save_repository_metadata()` with a single lock (e.g. `threading.Lock`), or serialize repository disk ops onto one dedicated executor.

### [SEV: med] Metadata index is rewritten in place (non-atomic) — a mid-write failure corrupts the entire repository
- **File:** repository_service.py:238-249 (save_repository_metadata); reload dependency at 124-129, 181-185
- **Category:** error-handling
- **What:** `save_repository_metadata()` opens `.repository.json` with `mode="w"` (truncate) and then serializes+writes. There is no write-to-temp-then-atomic-replace. A crash, exception, or full disk between truncate and complete write leaves a truncated/empty/partial file.
- **Failure scenario:** Disk fills (or process is killed) while persisting metadata after a create/delete. `.repository.json` is now partial; on restart `json.loads` raises `RepositoryMetadataFileJSONError` (line 126-129) and every payload/artifact in that repository fails to load — a single interrupted write bricks the whole index, not one resource.
- **Fix:** Serialize to a temp file in the same directory and `os.replace()` it over the target (atomic on the same filesystem); keep a `.bak` of the prior good file.

### [SEV: med] Partial-failure between disk placement and metadata persistence leaves orphans or an unloadable repository
- **File:** repository_service.py:313-323 (create_file), 382-397 (add_file), 456-467 (create_directory), 529-543 (add_directory), 616-643 (delete_resource_by_resource_id); consumed by payloads_service.py:172-200 / 268-297 / 367-395 / 465-494 and artifacts_service.py:158-174 / 222-239 / 295-312 / 362-379
- **Category:** error-handling
- **What:** In every create/add path the resource is written/moved onto disk and inserted into `self._resources`, and only then is `save_repository_metadata()` called. If that persist fails, the file/dir exists on disk but is not recorded on disk (the `add_*` docstrings even admit "the resource exists on disk without being recorded"). In `delete`, the on-disk object is removed and `del self._resources[...]` runs, then persist; if persist fails after deletion, the on-disk metadata still lists a resource whose file is gone.
- **Failure scenario:** (a) `add_payload_file` moves the source in, then the metadata write fails: the file sits in the repository directory forever untracked (orphan; the source is also already gone when `copy=False`). (b) `delete_artifact` removes the directory, then the metadata write fails: on next `load_repository_metadata`, the still-listed resource is missing from disk and line 181-185 raises `RepositoryMetadataFileUnsyncedError`, refusing to load the entire repository until the file is hand-edited.
- **Fix:** Persist metadata before the irreversible disk mutation where possible, or record intent and reconcile on load (tolerate missing-on-disk during load, or roll back the disk op if the persist fails).

### [SEV: med] Arbitrary source-path move/copy into the repository (arbitrary file read; arbitrary move/delete of any server-readable path)
- **File:** payloads_service.py:203-297 (add_payload_file), 398-494 (add_payload_directory); artifacts_service.py:177-239 (add_artifact_file), 242-312 (create_artifact_directory, `content` as str/Path), 315-379 (add_artifact_directory); forwarded unvalidated to repository_service.py:370-397 (add_file), 517-544 (add_directory)
- **Category:** path-traversal
- **What:** The `add_*` methods accept an arbitrary source `path` (and `create_artifact_directory` accepts a `str`/`pathlib.Path` `content` treated as a source directory) with no validation that it lies inside any allowlisted base directory. With `copy=False` (the default) `shutil.move` relocates the target into the repository; with `copy=True`/`copytree` it copies it in. Absolute paths, `..`, and symlinks are all accepted.
- **Failure scenario:** A caller of the agent-facing facade (`AgentFileManagerService.add_artifact_file`/`add_artifact_directory` pass `path` straight through, agent_file_manager_service.py:219-225, 313-319) or any internal caller registers e.g. `C:\...\server config`, a private key, or another repository's `.repository.json` as an artifact. It is then downloadable via `GET /api/artifacts/download/{id}` (arbitrary file read). Because the default moves rather than copies, the original is also deleted from its location (arbitrary move/delete). `create_artifact_directory(content="C:\\some\\dir")` copytrees an arbitrary directory in the same way.
- **Fix:** Resolve the source path and require it to be under an explicit, configured ingest base directory (reject `..`, absolute escapes, and symlinks that escape it); or document and gate this as a trusted-only primitive not reachable from agent/operator input.

### [SEV: low] Unbounded upload size, entry count, and decompression (archive-bomb / disk-exhaustion DoS)
- **File:** payloads_service.py:108-200 (create_payload_file), 300-395 (create_payload_directory); artifacts_service.py:116-174 (create_artifact_file), 242-312 (create_artifact_directory)
- **Category:** dos
- **What:** Content and archives are accepted and fully materialized/extracted with no size cap, entry cap, or compression-ratio limit (the archive is streamed to a temp file and then `shutil.unpack_archive`d wholesale in repository_objects.py:598-637). A zip/tar bomb or a very large stream exhausts disk.
- **Failure scenario:** An operator/agent with create permission uploads a 100 MB zip that expands to hundreds of GB, or streams an unbounded body; the extraction fills the data volume and takes the server (and co-located repositories) down.
- **Fix:** Per the project's design philosophy this cap is policy for the API boundary, but no cap exists there today for these paths — add a configurable max content size / max extracted size / max entries and enforce it before/while extracting.

### [SEV: low] Zip-slip / tar-slip protection is implicit — relies entirely on the stdlib default, with no member validation in the service/object
- **File:** repository_service.py:399-469 (create_directory forwards attacker-controlled `content` + `archive_file_format`); extraction confirmed at repository_objects.py:598-637 (`shutil.unpack_archive`, no `filter=` passed, no member-path check)
- **Category:** path-traversal
- **What:** Archive members are attacker-controlled and are extracted with `shutil.unpack_archive` without an explicit tar `filter=` and without validating member paths against the destination. On Python 3.14 this is currently safe (tar defaults to the `'data'` filter, and `zipfile` sanitizes member paths), so no traversal exists today, but the safety is entirely implicit.
- **Failure scenario:** A future change passing `filter='fully_trusted'`/`filter=None` explicitly, or running under an older interpreter, silently reintroduces write-outside-destination via a member named `..\\..\\evil` or an absolute path — arbitrary file write as the server user.
- **Fix:** Make the invariant explicit at the extraction call (pin `filter='data'` for tar) and/or validate every resolved member path stays within the destination directory before writing; add a regression test.

### [SEV: low] No per-resource ownership/authz — cross-operator and cross-agent read/update/delete (IDOR-shaped)
- **File:** payloads_service.py:497-589 (update), 592-638 (delete), 641-665 (get_by_id), 668-686 (get_all); artifacts_service.py:382-436 (update), 439-478 (delete), 481-496 (get_all), 499-519 (get_by_id)
- **Category:** perms
- **What:** Every accessor/mutator operates on any resource purely by ID with no owner/operator/producing-agent scoping. The stored attribution (`agent` reference for artifacts, `agent_template` reference for payloads) is recorded but never consulted for access control.
- **Failure scenario:** Operator A downloads/deletes operator B's payloads, or agent X reads/deletes artifacts produced by agent Y, simply by enumerating IDs. Access is gated only by the coarse per-endpoint permission (e.g. `READ_ALL_PAYLOADS`, `DELETE_PAYLOAD_BY_PAYLOAD_ID`), not by ownership.
- **Fix:** If per-principal isolation is intended, filter/authorize by the stored attribution at the service boundary; if global sharing is intended, document it explicitly so the API layer does not assume isolation.

### [SEV: low] Reserved resource IDs accumulate without bound and are never reclaimed
- **File:** repository_service.py:251-263 (reserve_resource_id); exposed via payloads_service.py:91-105 and artifacts_service.py:99-113
- **Category:** dos
- **What:** `reserve_resource_id` adds a UUID to `self._reserved_resource_ids` that is only ever removed when the exact ID is later claimed by a create/add call. Reserved-but-never-claimed IDs live for the lifetime of the process, and reservations are not persisted, so they also vanish on restart (a claim after restart then fails as `ResourceIDReservationNotFoundError`).
- **Failure scenario:** A client repeatedly calls the reserve endpoint without ever creating the resource; the in-memory set grows unbounded (slow memory leak). Separately, reserve-then-restart-then-create is a latent correctness surprise.
- **Fix:** Expire reservations (TTL / max count), and either persist reservations or document that they do not survive a restart.

## Design notes
- Heavy duplication across the four create/add wrappers in each service (payloads_service.py:108-494, artifacts_service.py:116-379) and their `_build_*_resource_data` + event-emit + `asyncio.to_thread` boilerplate. A single private helper taking the repository method and the built `data` would remove ~4x repetition and make the (missing) locking/atomicity fix a one-place change.
- `normalize_uuid` (utils.py:169-170) is just `str(value)` — it validates nothing. Path safety currently holds only because the API validates `UUID4` and the create paths re-parse via `uuid.UUID(...)` (repository_service.py:307/378/452/525) and gate on the reservation set. Any future service-internal caller that builds a path from a `normalize_uuid` result without that gate would have no traversal protection. Consider making `normalize_uuid` actually validate/canonicalize a UUID.
- Filesystem errors carry `path=str(path)` (absolute repository path) plus the raw underlying error string (repository_objects.py:36-43, utils.py:104-124). These propagate up through the three services unmodified; whether the absolute path/`underlying_error` reaches API clients depends on the api_exception mapping. Worth confirming absolute server paths are stripped before they reach a response body (info-leak). Flagged as uncertain below.
- `delete_resource_by_resource_id` snapshots `payload.to_json()` / `artifact.to_json()` before deletion (payloads_service.py:616-625, artifacts_service.py:462-466) specifically because `to_json` re-reads disk — good, and worth preserving if the create/add flows are refactored.

## Notes
- Reachability varies by resource type and should be confirmed by the API-surface reviewer: the payloads API (payloads_api.py) exposes no upload endpoint, so `create_payload_directory` archive content is not directly client-uploaded (payloads are built internally by agent_templates_payloads_service). The assets upload endpoint (_repository_api_factory.py:172-269) does stream client-controlled archive content into `create_directory`, and the artifacts agent facade exposes archive/source-path ingest to agent/component code. The `add_*` arbitrary-source-path finding (F4) is only as severe as the trust level of its reachable callers — needs a human to rule on the agent/component trust boundary.
- Info-leak of absolute paths in propagated `RepositoryResourceFileSystemError` / `RepositoryMetadataFileSystemError` messages: confirm at the api_exceptions boundary whether these strings are surfaced to clients. Deferred (boundary is out of scope here).
- Python 3.14 mitigates archive traversal by default (per AGENTS.md environment note); the tar-slip finding is a defense-in-depth / regression concern rather than a live exploit at this commit.
