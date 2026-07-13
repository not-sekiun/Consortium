import asyncio
import enum
import hashlib
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
from tomlkit.exceptions import ParseError

_console = Console()

_IS_WINDOWS = sys.platform == "win32"


class _ComponentDependencySyncResult(enum.Enum):
    SUCCESS = enum.auto()
    RESTART = enum.auto()
    FAILURE = enum.auto()


def _check_uv_exists() -> _ComponentDependencySyncResult:
    if not shutil.which("uv"):
        _console.print(
            "Failed to launch server pre-flight checks, startup aborted. Could not "
            "find the uv binary on the system PATH. Either uv is not installed or not "
            "on the system PATH."
        )
        return _ComponentDependencySyncResult.FAILURE


def _consortium_root_path() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


async def _run_command_async(command: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if _IS_WINDOWS else 0,
    )  # use `CREATE_NEW_PROCESS_GROUP` flag so that CTRL-C doesnt interrupt the running process
    try:
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode(), stderr.decode()
    except asyncio.CancelledError, KeyboardInterrupt:
        proc.kill()
        await proc.wait()  # reap it, ensures pipes are actually torn down
        raise


def _read_toml_file(path: pathlib.Path) -> tomlkit.TOMLDocument | None:
    with path.open("r") as f:
        try:
            return tomlkit.parse(f.read())
        except ParseError as exc:
            _console.print(
                "[bold red]Failed to run server pre-flight checks, startup aborted. Could "
                f"not parse '{path}':[/]\n {exc}"
            )
            return None


def _write_toml_file(path: pathlib.Path, data: tomlkit.TOMLDocument) -> None:
    # Newline as an empty string preserves CRLF
    with path.open("w", newline="") as f:
        f.write(tomlkit.dumps(data))


def _reset_pyproject_file_workspace_members(
    pyproject_toml_file: pathlib.Path,
) -> None:
    data = _read_toml_file(pyproject_toml_file)
    if data is None:
        return
    data["tool"]["uv"]["workspace"]["members"] = []
    _write_toml_file(pyproject_toml_file, data)


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _print_hint(uv_output: str, name_to_component_path_map: dict[str, str]) -> None:
    if "No solution found when resolving dependencies" not in uv_output:
        return
    for name, component_path in name_to_component_path_map.items():
        if _normalize_name(name=name) in uv_output:
            _console.print(
                f"Hint: The component at [bold yellow]{component_path}[/] may have "
                f"a dependency conflict. Check its [bold yellow]pyproject.toml[/] "
                f"file for any conflicting dependencies"
            )


def _fail(
    uv_output: str,
    pyproject_toml_file: pathlib.Path,
    name_to_component_path_map: dict[str, str],
) -> _ComponentDependencySyncResult:
    _reset_pyproject_file_workspace_members(pyproject_toml_file=pyproject_toml_file)
    _console.print(
        "[bold red]Failed to run server pre-flight checks, startup aborted. Could not "
        f"resolve server component dependencies via uv:[/]\n {uv_output}"
    )
    _print_hint(uv_output, name_to_component_path_map)
    return _ComponentDependencySyncResult.FAILURE


async def _restart_into_server() -> NoReturn:
    _console.print("[bold]Dependencies changed, restarting server...[/]")
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


def _discover_components(
    components_path: pathlib.Path, consortium_root_path: pathlib.Path
) -> tuple[dict[str, str], list[str]] | None:
    name_to_component_path_map: dict[str, str] = {}
    members: list[str] = []
    for manifest_path in components_path.glob("**/manifest.json"):
        component_pyproject_toml_path = manifest_path.parent / "pyproject.toml"
        if not component_pyproject_toml_path.exists():
            continue

        member = str(manifest_path.parent.relative_to(consortium_root_path))
        component_data = _read_toml_file(component_pyproject_toml_path)
        if component_data is None:
            return None

        name_to_component_path_map[component_data["project"]["name"]] = member
        members.append(member)

    return name_to_component_path_map, members


# Before server starts up, we need to resolve all declared component python
# dependencies against the project root. Then check for any changes to decide whether
# to restart.
# TODO: Maybe consider unifying name in the component class definition with the
#  pyproject.toml file
async def _sync_component_dependencies() -> _ComponentDependencySyncResult:
    if (sync_result := _check_uv_exists()) == _ComponentDependencySyncResult.FAILURE:
        return sync_result

    consortium_root_path = _consortium_root_path()
    uv_lock_file = consortium_root_path / "uv.lock"
    pyproject_toml_file = consortium_root_path / "pyproject.toml"
    components_path = pathlib.Path(__file__).resolve().parents[1] / "components"

    old_uv_lock_hash = hashlib.md5(uv_lock_file.read_bytes()).hexdigest()

    pyproject_toml_data = _read_toml_file(pyproject_toml_file)
    if pyproject_toml_data is None:
        return _ComponentDependencySyncResult.FAILURE

    discovered = _discover_components(components_path, consortium_root_path)
    if discovered is None:
        return _ComponentDependencySyncResult.FAILURE
    name_to_component_path_map, discovered_members = discovered

    # Add any newly discovered components as workspace members so uv can see them
    existing = set(pyproject_toml_data["tool"]["uv"]["workspace"]["members"])
    for member in discovered_members:
        if member not in existing:
            pyproject_toml_data["tool"]["uv"]["workspace"]["members"].append(member)
            existing.add(member)

    _write_toml_file(pyproject_toml_file, pyproject_toml_data)

    # chdir to repository root to run uv commands against it, in case the server was
    # started from a different directory
    original_cwd = pathlib.Path.cwd()
    os.chdir(consortium_root_path)
    try:
        returncode, stdout, stderr = await _run_command_async(command=["uv", "lock"])
        if returncode != 0:
            return _fail(
                stdout + stderr, pyproject_toml_file, name_to_component_path_map
            )

        new_uv_lock_hash = hashlib.md5(uv_lock_file.read_bytes()).hexdigest()
        if new_uv_lock_hash == old_uv_lock_hash:
            return _ComponentDependencySyncResult.SUCCESS

        # Locking changed something: install the new packages, then report that a
        # restart is needed. The actual restart happens later, back in main(), once
        # any live display (the pre-flight spinner) has stopped.
        returncode, stdout, stderr = await _run_command_async(
            command=["uv", "sync", "--all-packages"]
        )
        if returncode != 0:
            return _fail(
                stdout + stderr, pyproject_toml_file, name_to_component_path_map
            )

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
