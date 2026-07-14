import asyncio
import dataclasses
import enum
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
from typing import NoReturn

import tomlkit
from rich.console import Console
from rich.panel import Panel
from tomlkit.exceptions import ParseError

_console = Console()

_IS_WINDOWS = sys.platform == "win32"

# Substrings in uv output that indicate the failure is caused by a specific
# component's declared dependencies / pyproject file (and is therefore attributable
# and recoverable by dropping that member), as opposed to a transient or
# environmental failure (network, disk, uv itself) which should abort startup.
_ATTRIBUTABLE_UV_ERROR_MARKERS = (
    "No solution found when resolving dependencies",
    "Failed to parse",
    "is missing a `pyproject.toml`",
    "are both named",  # duplicate package name error
)

_MANIFEST_REQUIRED_KEYS = (("entry_point", str), ("enabled", bool))

_MAX_FAILURE_DETAIL_CHARS = 1200


class _ComponentDependencySyncResult(enum.Enum):
    SUCCESS = enum.auto()
    RESTART = enum.auto()
    FAILURE = enum.auto()


@dataclasses.dataclass
class _ComponentSyncFailure:
    member: str  # component folder path relative to the repository root
    reason: str  # short human-readable summary
    detail: str = ""  # raw error output / exception text


def _check_uv_exists() -> _ComponentDependencySyncResult:
    if not shutil.which("uv"):
        _console.print(
            "Failed to launch server pre-flight checks, startup aborted. Could not "
            "find the uv binary on the system PATH. Either uv is not installed or not "
            "on the system PATH."
        )
        return _ComponentDependencySyncResult.FAILURE
    return _ComponentDependencySyncResult.SUCCESS


def _consortium_root_path() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


async def _run_command_async(command: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if _IS_WINDOWS else 0,
    )  # use `CREATE_NEW_PROCESS_GROUP` flag so that CTRL-C does not interrupt the running process
    try:
        stdout, stderr = await proc.communicate()
        return (
            proc.returncode,
            stdout.decode(errors="replace"),
            stderr.decode(errors="replace"),
        )
    except asyncio.CancelledError, KeyboardInterrupt:
        proc.kill()
        await proc.wait()  # reap it, ensures pipes are actually torn down
        raise


def _read_toml_file(path: pathlib.Path) -> tomlkit.TOMLDocument | None:
    with path.open("r", encoding="utf-8") as f:
        try:
            return tomlkit.parse(f.read())
        except ParseError as exc:
            _console.print(
                "[bold red]Failed to run server pre-flight checks, startup aborted. "
                f"Could not parse '{path}':[/]\n {exc}"
            )
            return None


def _write_toml_file(path: pathlib.Path, data: tomlkit.TOMLDocument) -> None:
    # Newline as an empty string preserves CRLF
    with path.open("w", newline="", encoding="utf-8") as f:
        f.write(tomlkit.dumps(data))


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _truncate_detail(detail: str) -> str:
    detail = detail.strip()
    if len(detail) <= _MAX_FAILURE_DETAIL_CHARS:
        return detail
    return detail[:_MAX_FAILURE_DETAIL_CHARS] + "\n[... output truncated ...]"


def _load_component_manifest(
    manifest_path: pathlib.Path,
    member: str,
) -> dict | _ComponentSyncFailure:
    """Read and validate a component's manifest.json.

    Returns the parsed manifest on success or a `_ComponentSyncFailure` describing
    what is wrong with it.
    """
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return _ComponentSyncFailure(
            member=member,
            reason="Could not read manifest.json",
            detail=str(exc),
        )

    if not isinstance(manifest, dict):
        return _ComponentSyncFailure(
            member=member,
            reason="Invalid manifest.json",
            detail=f"Expected a JSON object, got {type(manifest).__name__}",
        )

    for key, expected_type in _MANIFEST_REQUIRED_KEYS:
        if key not in manifest:
            return _ComponentSyncFailure(
                member=member,
                reason="Invalid manifest.json",
                detail=f"Missing required key '{key}'",
            )
        if not isinstance(manifest[key], expected_type):
            return _ComponentSyncFailure(
                member=member,
                reason="Invalid manifest.json",
                detail=(
                    f"Key '{key}' must be of type '{expected_type.__name__}', got "
                    f"'{type(manifest[key]).__name__}'"
                ),
            )

    return manifest


def _load_component_pyproject_name(
    pyproject_path: pathlib.Path,
    member: str,
) -> str | _ComponentSyncFailure:
    """Read a component's pyproject.toml and return its normalized project name.

    Validates the minimum shape uv requires of a workspace member so that a broken
    file becomes a per-component failure here instead of a whole-workspace `uv lock`
    error later.
    """
    try:
        with pyproject_path.open("r", encoding="utf-8") as f:
            data = tomlkit.parse(f.read())
    except (ParseError, OSError) as exc:
        return _ComponentSyncFailure(
            member=member,
            reason="Could not parse pyproject.toml",
            detail=str(exc),
        )

    project = data.get("project")
    if not isinstance(project, dict):
        return _ComponentSyncFailure(
            member=member,
            reason="Invalid pyproject.toml",
            detail="Missing the required '[project]' table",
        )

    name = project.get("name")
    if not isinstance(name, str) or not name.strip():
        return _ComponentSyncFailure(
            member=member,
            reason="Invalid pyproject.toml",
            detail="'[project]' table is missing a non-empty 'name' field",
        )

    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        return _ComponentSyncFailure(
            member=member,
            reason="Invalid pyproject.toml",
            detail=(
                "'[project]' table is missing a 'version' field. uv requires every "
                "workspace member to declare a literal version, e.g. version = "
                '"0.0.0"'
            ),
        )

    return _normalize_name(name)


def _discover_components(
    components_path: pathlib.Path,
    consortium_root_path: pathlib.Path,
) -> tuple[dict[str, str], list[_ComponentSyncFailure]]:
    """Walk the components tree and collect workspace member candidates.

    Returns a map of normalized project name -> member path (relative to the
    repository root, POSIX separators as required by TOML/uv), plus a list of
    per-component failures for anything that could not be validated. Disabled
    components are skipped entirely: they are never loaded, so their dependencies
    are not installed (and get pruned on the next sync if previously present).
    """
    name_to_member_map: dict[str, str] = {}
    failures: list[_ComponentSyncFailure] = []

    for manifest_path in sorted(components_path.glob("**/manifest.json")):
        component_dir = manifest_path.parent
        member = component_dir.relative_to(consortium_root_path).as_posix()

        manifest = _load_component_manifest(manifest_path, member=member)
        if isinstance(manifest, _ComponentSyncFailure):
            failures.append(manifest)
            continue

        if not manifest["enabled"]:
            continue

        component_pyproject_path = component_dir / "pyproject.toml"
        if not component_pyproject_path.exists():
            # Components with no third-party dependencies don't need a pyproject and
            # don't participate in the workspace at all
            continue

        name = _load_component_pyproject_name(component_pyproject_path, member=member)
        if isinstance(name, _ComponentSyncFailure):
            failures.append(name)
            continue

        if name in name_to_member_map:
            failures.append(
                _ComponentSyncFailure(
                    member=member,
                    reason="Duplicate project name",
                    detail=(
                        f"Project name '{name}' is already used by workspace member "
                        f"'{name_to_member_map[name]}'. uv requires workspace member "
                        f"names to be unique."
                    ),
                )
            )
            continue

        name_to_member_map[name] = member

    return name_to_member_map, failures


def _set_workspace_members(
    pyproject_toml_data: tomlkit.TOMLDocument,
    pyproject_toml_file: pathlib.Path,
    members: list[str],
) -> None:
    """Overwrite `tool.uv.workspace.members` with exactly the given member list.

    The list is fully reconciled (not appended to) so that deleted or dropped
    components disappear from the workspace instead of lingering as stale entries
    that break `uv lock` with 'missing pyproject.toml' errors forever.
    """
    members_array = tomlkit.array()
    members_array.multiline(True)
    for member in sorted(members):
        members_array.append(member)

    tool = pyproject_toml_data.setdefault("tool", tomlkit.table())
    uv = tool.setdefault("uv", tomlkit.table())
    workspace = uv.setdefault("workspace", tomlkit.table())
    workspace["members"] = members_array

    _write_toml_file(pyproject_toml_file, pyproject_toml_data)


def _is_attributable_uv_error(uv_output: str) -> bool:
    return any(marker in uv_output for marker in _ATTRIBUTABLE_UV_ERROR_MARKERS)


def _implicated_members(
    uv_output: str,
    name_to_member_map: dict[str, str],
    active_members: set[str],
) -> list[str]:
    """Find active members that uv's error output points at.

    Matches both the member's normalized project name (resolver conflicts name
    packages) and its folder path (parse/member errors name files), so both classes
    of failure attribute to a component.
    """
    normalized_output = _normalize_name(uv_output)
    implicated = []
    for name, member in name_to_member_map.items():
        if member not in active_members:
            continue
        name_pattern = rf"\b{re.escape(name)}\b"
        windows_member = member.replace("/", "\\")
        if (
            re.search(name_pattern, normalized_output)
            or member in uv_output
            or windows_member in uv_output
        ):
            implicated.append(member)
    return implicated


async def _uv_lock() -> tuple[int, str]:
    returncode, stdout, stderr = await _run_command_async(command=["uv", "lock"])
    return returncode, stdout + stderr


def _fatal(message: str, uv_output: str) -> None:
    _console.print(
        f"[bold red]Failed to run server pre-flight checks, startup aborted. "
        f"{message}:[/]\n {uv_output.strip()}"
    )


async def _lock_with_degradation(
    pyproject_toml_data: tomlkit.TOMLDocument,
    pyproject_toml_file: pathlib.Path,
    name_to_member_map: dict[str, str],
    failures: list[_ComponentSyncFailure],
) -> list[str] | None:
    """Run `uv lock`, dropping components that break resolution until it succeeds.

    Returns the final list of workspace members that locked successfully, or None
    on a fatal (non-attributable) failure. Every dropped component is recorded in
    `failures` along with uv's output.

    Strategy: attempt the full member set and use uv's error output to attribute
    failures to specific members, dropping them and retrying. If an error can't be
    attributed to any member, fall back to verifying the root locks on its own and
    then re-admitting members one at a time.
    """
    member_to_name_map = {v: k for k, v in name_to_member_map.items()}
    active = set(name_to_member_map.values())

    # Phase 1: whole-set lock with attribution-based dropping. Each retry drops at
    # least one member, so this loop is bounded by the member count.
    for _ in range(len(active) + 1):
        _set_workspace_members(pyproject_toml_data, pyproject_toml_file, sorted(active))
        returncode, uv_output = await _uv_lock()
        if returncode == 0:
            return sorted(active)

        if not _is_attributable_uv_error(uv_output):
            # Transient/environmental failure (network, uv itself, root project
            # misconfiguration). Dropping components can't fix this - abort.
            _fatal("Could not resolve server component dependencies via uv", uv_output)
            return None

        implicated = _implicated_members(uv_output, name_to_member_map, active)
        if not implicated:
            break  # attributable error but can't tell whose - fall back to phase 2

        detail = _truncate_detail(uv_output)
        for member in implicated:
            active.discard(member)
            failures.append(
                _ComponentSyncFailure(
                    member=member,
                    reason="Dependency resolution failed",
                    detail=detail,
                )
            )

    # Phase 2: incremental fallback. First make sure the root project locks with no
    # members at all - if it can't, the baseline environment itself is broken.
    _set_workspace_members(pyproject_toml_data, pyproject_toml_file, [])
    returncode, uv_output = await _uv_lock()
    if returncode != 0:
        _fatal(
            "The root project failed to resolve on its own (no components included)",
            uv_output,
        )
        return None

    accepted: list[str] = []
    for member in sorted(active):
        _set_workspace_members(
            pyproject_toml_data, pyproject_toml_file, [*accepted, member]
        )
        returncode, uv_output = await _uv_lock()
        if returncode == 0:
            accepted.append(member)
            continue
        if not _is_attributable_uv_error(uv_output):
            _fatal("Could not resolve server component dependencies via uv", uv_output)
            return None
        failures.append(
            _ComponentSyncFailure(
                member=member,
                reason=(
                    "Dependency resolution failed against the accepted workspace "
                    f"(as '{member_to_name_map.get(member, member)}')"
                ),
                detail=_truncate_detail(uv_output),
            )
        )

    # The loop leaves the members list set to `accepted + [last failed member]` if
    # the final candidate failed, so reconcile it to exactly the accepted set.
    _set_workspace_members(pyproject_toml_data, pyproject_toml_file, accepted)
    returncode, uv_output = await _uv_lock()
    if returncode != 0:
        # Should be impossible - this exact set just locked incrementally
        _fatal("Could not re-lock the accepted workspace member set", uv_output)
        return None

    return accepted


def _print_failure_report(failures: list[_ComponentSyncFailure]) -> None:
    if not failures:
        return

    _console.print(
        f"{len(failures)} component(s) excluded from server pre-flight "
        f"dependency sync. The server will start without them\n",
        style="red",
    )
    for failure in sorted(failures, key=lambda f: f.member):
        panel = Panel(
            failure.detail,
            title=f"[bold white]{failure.member} ({failure.reason})[/]",
            expand=False,
            style="red",
        )
        _console.print(panel)
        _console.print()


def _hash_file_if_exists(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


async def _restart_into_server() -> NoReturn:
    _console.print("[bold]Dependencies changed, restarting server...[/]\n")
    sys.stdout.flush()
    sys.stderr.flush()
    uv_path = shutil.which("uv") or "uv"
    try:
        proc = await asyncio.create_subprocess_exec(
            uv_path, "run", "consortium.py", "server"
        )
    except OSError as exc:
        _console.print(f"[bold red]Failed to launch server process:[/]\n {exc}")
        sys.exit(1)
    # Ignore SIGINT ourselves for the duration of the wait. The server is in the
    # same foreground process group and receives the same Ctrl-C directly, so it
    # already handles its own shutdown - we don't need to react to the signal at
    # all. (An earlier version of this tried to catch KeyboardInterrupt/CancelledError
    # around the wait and retry, but with asyncio that exception doesn't reliably
    # land inside this specific try/except; ignoring the signal outright avoids
    # depending on exactly where the interrupt would otherwise surface.)
    previous_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        returncode = await proc.wait()
    finally:
        signal.signal(signal.SIGINT, previous_handler)
    sys.exit(returncode)  # forward the server's exit code as our own


# Before server starts up, we need to resolve all declared component python
# dependencies against the project root. Components that fail validation or break
# dependency resolution are dropped from the workspace (and reported) rather than
# aborting startup - the server boots with every component that can be satisfied.
async def _sync_component_dependencies() -> _ComponentDependencySyncResult:
    if (sync_result := _check_uv_exists()) == _ComponentDependencySyncResult.FAILURE:
        return sync_result

    consortium_root_path = _consortium_root_path()
    uv_lock_file = consortium_root_path / "uv.lock"
    pyproject_toml_file = consortium_root_path / "pyproject.toml"
    components_path = pathlib.Path(__file__).resolve().parents[1] / "components"

    # uv.lock may not exist yet on a first boot; hash None then so the first
    # successful lock registers as a change and triggers the install + restart path
    old_uv_lock_hash = _hash_file_if_exists(uv_lock_file)

    pyproject_toml_data = _read_toml_file(pyproject_toml_file)
    if pyproject_toml_data is None:
        return _ComponentDependencySyncResult.FAILURE

    name_to_member_map, failures = _discover_components(
        components_path=components_path,
        consortium_root_path=consortium_root_path,
    )

    # chdir to repository root to run uv commands against it, in case the server was
    # started from a different directory
    original_cwd = pathlib.Path.cwd()
    os.chdir(consortium_root_path)
    try:
        accepted_members = await _lock_with_degradation(
            pyproject_toml_data=pyproject_toml_data,
            pyproject_toml_file=pyproject_toml_file,
            name_to_member_map=name_to_member_map,
            failures=failures,
        )
        if accepted_members is None:
            _print_failure_report(failures)
            return _ComponentDependencySyncResult.FAILURE

        _print_failure_report(failures)

        new_uv_lock_hash = _hash_file_if_exists(uv_lock_file)
        if new_uv_lock_hash == old_uv_lock_hash:
            return _ComponentDependencySyncResult.SUCCESS

        # Locking changed something: install the new packages, then report that a
        # restart is needed. The actual restart happens later, back in main(), once
        # any live display (the pre-flight spinner) has stopped.
        returncode, stdout, stderr = await _run_command_async(
            command=["uv", "sync", "--all-packages"]
        )
        if returncode != 0:
            # The lock already succeeded, so this is environmental (network fetch of
            # a wheel, disk) rather than a component conflict - nothing to drop.
            _fatal("Could not install resolved dependencies via uv", stdout + stderr)
            return _ComponentDependencySyncResult.FAILURE

        return _ComponentDependencySyncResult.RESTART
    finally:
        os.chdir(original_cwd)


async def main():
    try:
        with _console.status(
            "Server start pre-flight check: resolving component dependencies...",
            spinner="dots",
            spinner_style="bold white",
        ):
            result = await _sync_component_dependencies()
    except asyncio.CancelledError, KeyboardInterrupt:
        _console.print("[bold red]Interrupted, aborting startup.[/bold red]")
        sys.exit(0)

    # The `with` block above has now closed and the spinner has stopped, so it's
    # safe to launch a process that writes to the terminal directly.
    if result is _ComponentDependencySyncResult.FAILURE:
        sys.exit(1)
    if result is _ComponentDependencySyncResult.RESTART:
        os.chdir(_consortium_root_path())
        # launch a new server process and upon that process completing, sys.exit. Also
        # disables keyboard interrupting for the wrapper process launching that new
        # server process
        await _restart_into_server()
