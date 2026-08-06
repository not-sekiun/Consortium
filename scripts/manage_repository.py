import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from collections import deque
from datetime import datetime

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Inline (non fullscreen) menu widgets styled after Charm-like TUIs. These
# render in the normal terminal flow and erase themselves on exit, after which
# a compact "answer" line is printed so the transcript stays readable. Kept in
# sync with scripts/create_component_project.py so both scripts feel the same.
POINTER = "❯"  # heavy right-pointing angle
CHECKED = "[x]"
UNCHECKED = "[ ]"
HELP_SINGLE = "  (up/down to move, enter to select, ctrl-c to cancel)"
HELP_MULTI = "  (up/down to move, space to toggle, enter to confirm)"
HELP_CONFIRM = "  (left/right or y/n to change, enter to confirm)"

MENU_STYLE = Style.from_dict(
    {
        "qmark": "ansicyan bold",
        "qtext": "bold",
        "question": "bold",
        "pointer": "ansicyan bold",
        "selected": "ansicyan bold",
        "option": "",
        "checked": "ansigreen bold",
        "unchecked": "",
        "help": "ansibrightblack",
    },
)

# Resolve the server data directory relative to this script so the tool works
# regardless of the current working directory.
SCRIPT_DIRECTORY = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIRECTORY.parent
SERVER_DATA_DIRECTORY = PROJECT_ROOT / "data" / "server"

# The metadata index and the placeholder file are never treated as clearable
# resources: the index is reset in place and the placeholder keeps the empty
# directory tracked in git.
METADATA_FILENAME = ".repository.json"
KEEP_FILENAME = ".gitkeep"
PROTECTED_FILENAMES = {METADATA_FILENAME, KEEP_FILENAME}

# Repositories share the exact same metadata schema; only the per-entry "data"
# field carries domain-specific metadata, which this tool renders generically.
REPOSITORIES = {
    "assets": "Assets",
    "artifacts": "Artifacts",
    "payloads": "Payloads",
}

# How many rows a selection menu shows at once before it starts scrolling. File
# listings can grow large, so long menus scroll instead of blowing past the
# terminal height.
MENU_MAX_VISIBLE = 15

# Matches consortium/server/objects/repository_objects.py so a manually computed
# checksum reproduces the value the framework would have stored.
_MD5_CHUNK_SIZE = 64000


def _run_menu(get_text, key_bindings: KeyBindings, height: int):
    control = FormattedTextControl(get_text, focusable=True)
    window = Window(
        content=control,
        height=height,
        always_hide_cursor=True,
        wrap_lines=False,
    )
    application = Application(
        layout=Layout(HSplit([window])),
        key_bindings=key_bindings,
        style=MENU_STYLE,
        full_screen=False,
        erase_when_done=True,
        mouse_support=False,
    )
    return application.run()


def print_answer(message: str, answer: str) -> None:
    console.print(
        f"[green]?[/green] [bold]{message}[/bold] [cyan]{answer}[/cyan]",
    )


def select_one(
    message: str,
    options: list[tuple],
    default_index: int = 0,
    max_visible: int | None = None,
):
    # options: list of (value, label). Returns the chosen value, or None if the
    # user cancels. When max_visible is set and there are more options than fit,
    # the menu scrolls to keep the highlighted row in view.
    total = len(options)
    if max_visible is None or max_visible >= total:
        visible = total
    else:
        visible = max_visible
    state = {"index": default_index, "offset": 0}
    key_bindings = KeyBindings()

    @key_bindings.add("up")
    @key_bindings.add("k")
    @key_bindings.add("c-p")
    def _(event) -> None:
        state["index"] = (state["index"] - 1) % total

    @key_bindings.add("down")
    @key_bindings.add("j")
    @key_bindings.add("c-n")
    def _(event) -> None:
        state["index"] = (state["index"] + 1) % total

    @key_bindings.add("enter")
    def _(event) -> None:
        event.app.exit(result=options[state["index"]][0])

    @key_bindings.add("c-c")
    @key_bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=None)

    def get_text() -> FormattedText:
        # Keep the highlighted row inside the visible window.
        index = state["index"]
        offset = state["offset"]
        if index < offset:
            offset = index
        elif index >= offset + visible:
            offset = index - visible + 1
        state["offset"] = offset

        fragments = [("class:question", f"? {message}\n")]
        for position in range(offset, min(offset + visible, total)):
            _value, label = options[position]
            if position == index:
                fragments.append(("class:pointer", f"{POINTER} "))
                fragments.append(("class:selected", f"{label}\n"))
            else:
                fragments.append(("", "  "))
                fragments.append(("class:option", f"{label}\n"))
        if visible < total:
            fragments.append(
                (
                    "class:help",
                    f"  (up/down to move, enter to select; {index + 1}/{total})",
                ),
            )
        else:
            fragments.append(("class:help", HELP_SINGLE))
        return FormattedText(fragments)

    return _run_menu(get_text, key_bindings, visible + 2)


def select_many(message: str, options: list[tuple], preselect_all: bool = False):
    # options: list of (value, label). Returns a list of checked values in the
    # order they appear, or None if the user cancels.
    checked = {value for value, _label in options} if preselect_all else set()
    state = {"index": 0, "checked": checked}
    key_bindings = KeyBindings()

    @key_bindings.add("up")
    @key_bindings.add("k")
    @key_bindings.add("c-p")
    def _(event) -> None:
        state["index"] = (state["index"] - 1) % len(options)

    @key_bindings.add("down")
    @key_bindings.add("j")
    @key_bindings.add("c-n")
    def _(event) -> None:
        state["index"] = (state["index"] + 1) % len(options)

    @key_bindings.add("space")
    def _(event) -> None:
        value = options[state["index"]][0]
        if value in state["checked"]:
            state["checked"].discard(value)
        else:
            state["checked"].add(value)

    @key_bindings.add("enter")
    def _(event) -> None:
        chosen = [value for value, _label in options if value in state["checked"]]
        event.app.exit(result=chosen)

    @key_bindings.add("c-c")
    @key_bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=None)

    def get_text() -> FormattedText:
        fragments = [("class:question", f"? {message}\n")]
        for index, (value, label) in enumerate(options):
            pointer_style = "class:pointer" if index == state["index"] else ""
            pointer = POINTER if index == state["index"] else " "
            is_checked = value in state["checked"]
            mark_style = "class:checked" if is_checked else "class:unchecked"
            mark = CHECKED if is_checked else UNCHECKED
            label_style = (
                "class:selected" if index == state["index"] else "class:option"
            )
            fragments.append((pointer_style, f"{pointer} "))
            fragments.append((mark_style, f"{mark} "))
            fragments.append((label_style, f"{label}\n"))
        fragments.append(("class:help", HELP_MULTI))
        return FormattedText(fragments)

    return _run_menu(get_text, key_bindings, len(options) + 2)


def confirm(message: str, default: bool = True):
    # Returns True/False, or None if the user cancels.
    state = {"value": default}
    key_bindings = KeyBindings()

    @key_bindings.add("left")
    @key_bindings.add("right")
    @key_bindings.add("h")
    @key_bindings.add("l")
    @key_bindings.add("tab")
    def _(event) -> None:
        state["value"] = not state["value"]

    @key_bindings.add("y")
    def _(event) -> None:
        event.app.exit(result=True)

    @key_bindings.add("n")
    def _(event) -> None:
        event.app.exit(result=False)

    @key_bindings.add("enter")
    def _(event) -> None:
        event.app.exit(result=state["value"])

    @key_bindings.add("c-c")
    @key_bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=None)

    def get_text() -> FormattedText:
        if state["value"]:
            yes = ("class:selected", "[ Yes ]")
            no = ("class:option", "  No  ")
        else:
            yes = ("class:option", "  Yes  ")
            no = ("class:selected", "[ No ]")
        return FormattedText(
            [
                ("class:question", f"? {message}  "),
                yes,
                ("", " "),
                no,
                ("", "\n"),
                ("class:help", HELP_CONFIRM),
            ],
        )

    return _run_menu(get_text, key_bindings, 2)


def format_size(num_bytes) -> str:
    # Human-readable byte count for the listings. Falls back to a dash when the
    # metadata does not carry a usable size.
    if not isinstance(num_bytes, (int, float)):
        return "-"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def format_timestamp(value) -> str:
    # Metadata stores ISO-8601 strings. Show them as-is when unparseable so the
    # raw value is never hidden from the operator.
    if not value:
        return "-"
    if not isinstance(value, str):
        return str(value)
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def load_metadata(repository_path: pathlib.Path) -> dict:
    # Read the metadata index explicitly. A missing or unreadable index is
    # treated as empty so the tool can still operate on a broken repository.
    metadata_path = repository_path / METADATA_FILENAME
    try:
        with metadata_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        console.print(
            f"[yellow]Warning: could not parse {metadata_path}. "
            "Treating it as empty.[/yellow]",
        )
        return {}
    if not isinstance(data, dict):
        console.print(
            f"[yellow]Warning: {metadata_path} is not a JSON object. "
            "Treating it as empty.[/yellow]",
        )
        return {}
    return data


def save_metadata(repository_path: pathlib.Path, metadata: dict) -> None:
    (repository_path / METADATA_FILENAME).write_text(
        json.dumps(metadata, indent=4) + "\n",
        encoding="utf-8",
    )


def reset_metadata(repository_path: pathlib.Path) -> None:
    (repository_path / METADATA_FILENAME).write_text("{}\n", encoding="utf-8")


def ensure_keep(repository_path: pathlib.Path) -> None:
    keep_path = repository_path / KEEP_FILENAME
    if not keep_path.exists():
        keep_path.write_text("", encoding="utf-8")


def resolve_entry_path(
    repository_path: pathlib.Path,
    resource_id: str,
) -> pathlib.Path:
    # Files and directories alike are stored on disk as a bare "<resource_id>".
    # An entry's "name" is what the resource is served and downloaded under and
    # never appears in its path, so nothing in the entry is needed to find it.
    return repository_path / resource_id


def safe_entry_name(item: dict) -> str:
    # An entry's name is operator supplied and stored verbatim, so it can carry
    # path separators or "..". Only its last component can name a single file,
    # and an entry with no usable last component falls back to the on-disk name.
    # Windows path semantics are used regardless of platform because they treat
    # both separators, and a drive prefix, as significant.
    name = pathlib.PureWindowsPath(str(item["name"])).name
    if name in ("", ".", ".."):
        name = item["path"].name
    return name


def copy_resource(source: pathlib.Path, destination: pathlib.Path, is_directory: bool):
    if is_directory:
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def _hash_file_content(path) -> str:
    # Chunked MD5 of a single file, matching RepositoryFile.compute_md5_checksum.
    md5_hash = hashlib.md5()
    with open(path, "rb") as handle:
        while chunk := handle.read(_MD5_CHUNK_SIZE):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def _walk_directory_entries(root: pathlib.Path):
    # Mirror of RepositoryDirectory._walk_entries: return (relative_path,
    # os.DirEntry|None, is_file) tuples sorted by relative path, with empty
    # directories yielded as (relative_path, None, False). Kept byte-for-byte
    # compatible so the folded directory hash reproduces the framework's value.
    root_path = str(root)
    prefix = root_path if root_path.endswith(os.sep) else root_path + os.sep
    prefix_len = len(prefix)

    results = []
    stack = deque([root_path])
    while stack:
        current = stack.pop()
        with os.scandir(current) as iterator:
            entries = list(iterator)
        if not entries and current != root_path:
            results.append((current[prefix_len:], None, False))
        for entry in entries:
            if entry.is_dir():
                stack.append(entry.path)
            else:
                results.append((entry.path[prefix_len:], entry, True))
    results.sort(key=lambda item: item[0])
    return results


def compute_md5_checksum(path: pathlib.Path, is_directory: bool) -> str | None:
    # Reproduce the framework's checksum for a resource missing one in metadata.
    # Directories fold each file's relative path and content hash (and each empty
    # directory's relative path) into one overall MD5, mirroring
    # RepositoryDirectory.compute_md5_checksum.
    if not path.exists():
        return None
    if not is_directory:
        return _hash_file_content(path)

    overall_hash = hashlib.md5()
    for rel_path, entry, is_file in _walk_directory_entries(path):
        if is_file:
            file_hash = _hash_file_content(entry.path)
            overall_hash.update(rel_path.encode())
            overall_hash.update(file_hash.encode())
        else:
            overall_hash.update(rel_path.encode())
    return overall_hash.hexdigest()


def collect_tracked(repository_path: pathlib.Path, metadata: dict) -> list[dict]:
    # Build the list of resources straight from the metadata index. Entries
    # whose backing file is missing are flagged stale.
    tracked = []
    for resource_id, entry in metadata.items():
        if not isinstance(entry, dict):
            # Malformed entry: keep it visible so it can be cleaned up, but there
            # is no reliable on-disk path to resolve.
            tracked.append(
                {
                    "resource_id": resource_id,
                    "name": str(resource_id),
                    "path": repository_path / str(resource_id),
                    "size": None,
                    "is_directory": False,
                    "tracked": True,
                    "stale": True,
                    "malformed": True,
                    "entry": entry,
                },
            )
            continue
        path = resolve_entry_path(repository_path, resource_id)
        tracked.append(
            {
                "resource_id": resource_id,
                # An entry that recorded no name at all is shown under its resource
                # ID, which is the same fallback the server itself loads it with.
                "name": entry.get("name") or resource_id,
                "path": path,
                "size": entry.get("size"),
                "is_directory": bool(entry.get("is_directory")),
                "tracked": True,
                "stale": not path.exists(),
                "malformed": False,
                "entry": entry,
            },
        )
    return tracked


def collect_untracked(
    repository_path: pathlib.Path,
    tracked: list[dict],
) -> list[dict]:
    # On-disk entries the index does not reference, excluding the protected
    # metadata index and placeholder. These have no metadata to display.
    tracked_names = {item["path"].name for item in tracked}
    untracked = []
    for child in sorted(repository_path.iterdir(), key=lambda entry: entry.name):
        if child.name in PROTECTED_FILENAMES:
            continue
        if child.name in tracked_names:
            continue
        try:
            size = child.stat().st_size if child.is_file() else None
        except OSError:
            size = None
        untracked.append(
            {
                "resource_id": None,
                "name": child.name,
                "path": child,
                "size": size,
                "is_directory": child.is_dir(),
                "tracked": False,
                "stale": False,
                "malformed": False,
                "entry": None,
            },
        )
    return untracked


def collect_all_files(repository_path: pathlib.Path) -> list[pathlib.Path]:
    # Every on-disk entry except the protected metadata index and placeholder.
    # Used by hard reset so untracked resources are removed as well.
    return sorted(
        (
            child
            for child in repository_path.iterdir()
            if child.name not in PROTECTED_FILENAMES
        ),
        key=lambda child: child.name,
    )


def remove_path(path: pathlib.Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def open_in_viewer(path: pathlib.Path):
    # Hand the file off to the platform's default application. Returns
    # (ok, error_message).
    try:
        if sys.platform.startswith("win"):
            # os.startfile exists only on Windows; guarded by the platform check.
            os.startfile(str(path))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except FileNotFoundError:
        # The opener command (open / xdg-open) is not available.
        return False, "no default opener command is available on this system"
    except (OSError, subprocess.SubprocessError) as error:
        return False, str(error)
    return True, None


def status_counts(tracked: list[dict], untracked: list[dict]) -> dict:
    live = [item for item in tracked if not item["stale"]]
    stale = [item for item in tracked if item["stale"]]
    total_size = 0
    for item in live:
        if isinstance(item["size"], (int, float)):
            total_size += int(item["size"])
    for item in untracked:
        if isinstance(item["size"], (int, float)):
            total_size += int(item["size"])
    return {
        "tracked": len(tracked),
        "live": len(live),
        "stale": len(stale),
        "untracked": len(untracked),
        "size": total_size,
    }


def render_status_line(display_name: str, counts: dict) -> None:
    console.print(
        f"[bold]{display_name}[/bold]  "
        f"[cyan]{counts['live']}[/cyan] tracked file(s), "
        f"[yellow]{counts['stale']}[/yellow] stale, "
        f"[magenta]{counts['untracked']}[/magenta] untracked  "
        f"([green]{format_size(counts['size'])}[/green])",
    )


def file_label(item: dict, name_width: int) -> str:
    # Plain-text (no rich markup) row for a selection menu.
    name = item["name"]
    if len(name) > name_width:
        name = name[: name_width - 1] + "…"
    kind = "dir " if item["is_directory"] else "file"
    if item.get("malformed"):
        status = "malformed"
    elif item["stale"]:
        status = "stale"
    elif not item["tracked"]:
        status = "untracked"
    else:
        status = "tracked"
    size = format_size(item["size"]).rjust(9)
    return f"{name.ljust(name_width)}  {kind}  {size}  {status}"


def render_metadata(display_name: str, item: dict) -> None:
    # Full metadata view for one resource. Untracked files have no metadata, so
    # only basic on-disk facts are shown.
    if not item["tracked"] or item["entry"] is None:
        table = Table(show_header=False, box=None, padding=(0, 2, 0, 0), expand=False)
        table.add_row("Name", item["name"])
        table.add_row("On-disk file", item["path"].name)
        table.add_row("Type", "directory" if item["is_directory"] else "file")
        table.add_row("Size", format_size(item["size"]))
        table.add_row("Tracked", "no (untracked)")
        console.print(
            Panel(
                table,
                title=f"{display_name}: {item['name']}",
                border_style="cyan",
                expand=False,
            ),
        )
        return

    entry = item["entry"]
    if not isinstance(entry, dict):
        console.print(
            Panel(
                "This entry is malformed (not a JSON object) and cannot be\n"
                "rendered. Deleting it will remove it from the index.",
                title=f"{display_name}: {item['name']}",
                border_style="yellow",
                expand=False,
            ),
        )
        return

    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0), expand=False)
    table.add_row("Resource ID", str(item["resource_id"]))
    table.add_row("Name", str(entry.get("name", "-")))
    table.add_row("Description", str(entry.get("description") or "-"))
    table.add_row("On-disk file", item["path"].name)
    table.add_row(
        "Size",
        f"{format_size(entry.get('size'))} ({entry.get('size')} bytes)"
        if isinstance(entry.get("size"), (int, float))
        else "-",
    )
    table.add_row("Is directory", "yes" if entry.get("is_directory") else "no")
    table.add_row(
        "Exists on disk",
        "yes" if item["path"].exists() else "no (stale)",
    )
    table.add_row("Created", format_timestamp(entry.get("datetime_created")))
    table.add_row("Modified", format_timestamp(entry.get("datetime_modified")))
    # Metadata may not carry a checksum (it is only stored when explicitly
    # requested), so compute it on demand from the on-disk resource.
    checksum = entry.get("md5_checksum")
    computed = False
    if not checksum and item["path"].exists():
        try:
            with console.status("Computing MD5 checksum..."):
                checksum = compute_md5_checksum(
                    item["path"],
                    bool(entry.get("is_directory")),
                )
            computed = True
        except OSError as error:
            console.print(f"[yellow]Could not compute MD5 checksum: {error}[/yellow]")
            checksum = None
    if checksum:
        table.add_row(
            "MD5 checksum",
            f"{checksum} [dim](computed)[/dim]" if computed else str(checksum),
        )
    else:
        table.add_row("MD5 checksum", "-")
    console.print(
        Panel(
            table,
            title=f"{display_name}: {item['name']}",
            border_style="cyan",
            expand=False,
        ),
    )

    # The "data" field is domain-specific and varies per repository, so it is
    # rendered generically as pretty-printed JSON rather than parsed field by
    # field.
    data = entry.get("data")
    if data in (None, {}, []):
        console.print("[dim]Domain data: (none)[/dim]")
    else:
        try:
            rendered = json.dumps(data, indent=2, default=str)
        except (TypeError, ValueError):
            rendered = str(data)
        console.print(
            Panel(rendered, title="Domain data", border_style="blue", expand=False),
        )


def delete_item(repository_path: pathlib.Path, item: dict):
    # Remove the on-disk file (if present) and drop any matching metadata entry.
    # Returns (ok, error_message).
    path = item["path"]
    if path.exists():
        try:
            remove_path(path)
        except OSError as error:
            return False, str(error)
    if item["tracked"] and item["resource_id"] is not None:
        metadata = load_metadata(repository_path)
        if item["resource_id"] in metadata:
            metadata.pop(item["resource_id"], None)
            save_metadata(repository_path, metadata)
    return True, None


def file_actions(repository_path: pathlib.Path, display_name: str, item: dict) -> None:
    render_metadata(display_name, item)

    options = []
    exists = item["path"].exists()
    if exists:
        options.append(("open", "Open in default viewer"))
        options.append(("export", "Export to the current directory"))
    options.append(("delete", "Delete this file"))
    options.append(("back", "Back to file list"))

    action = select_one(f"Action for {item['name']}", options)
    if action in (None, "back"):
        return

    if action == "open":
        # The resource is stored under its bare resource ID, so there is no
        # extension for the platform to associate an application with. The copy
        # carries the entry's name, which is what a download would have arrived
        # as, and that is what gets handed to the viewer.
        export_name = safe_entry_name(item)
        try:
            temp_directory = pathlib.Path(
                tempfile.mkdtemp(prefix="consortium_repository_"),
            )
            temp_path = temp_directory / export_name
            copy_resource(item["path"], temp_path, item["is_directory"])
        except OSError as error:
            console.print(
                f"[red]Could not copy {item['name']} out to open it: {error}[/red]",
            )
            return
        ok, error = open_in_viewer(temp_path)
        if ok:
            console.print(
                f"[green]Opened a copy of {item['name']} in the default "
                "viewer.[/green]",
            )
            # The viewer is launched asynchronously, so the copy is deliberately
            # left behind: removing it here would pull the file out from under
            # the application that was just handed it.
            console.print(f"[dim]The copy is left at {temp_path}[/dim]")
        else:
            console.print(f"[red]Could not open {item['name']}: {error}[/red]")
        return

    if action == "export":
        destination = pathlib.Path.cwd() / safe_entry_name(item)
        if destination.exists():
            confirmed = confirm(
                f"{destination} already exists. Overwrite it?",
                default=False,
            )
            if not confirmed:
                console.print("[yellow]Export cancelled.[/yellow]")
                return
            try:
                remove_path(destination)
            except OSError as error:
                console.print(f"[red]Could not replace {destination}: {error}[/red]")
                return
        try:
            copy_resource(item["path"], destination, item["is_directory"])
        except OSError as error:
            console.print(f"[red]Failed to export {item['name']}: {error}[/red]")
            return
        console.print(f"[green]Exported {item['name']} to {destination}[/green]")
        return

    if action == "delete":
        note = ""
        if item["tracked"] and item["resource_id"] is not None:
            note = " and remove its metadata entry"
        confirmed = confirm(
            f"Delete {item['name']}{note}? This cannot be undone.",
            default=False,
        )
        if not confirmed:
            console.print("[yellow]Delete cancelled.[/yellow]")
            return
        ok, error = delete_item(repository_path, item)
        if ok:
            console.print(f"[green]Deleted {item['name']}.[/green]")
        else:
            console.print(f"[red]Failed to delete {item['name']}: {error}[/red]")


def browse_files(key: str) -> None:
    repository_path = SERVER_DATA_DIRECTORY / key
    display_name = REPOSITORIES[key]
    while True:
        metadata = load_metadata(repository_path)
        tracked = collect_tracked(repository_path, metadata)
        untracked = collect_untracked(repository_path, tracked)
        items = tracked + untracked

        if not items:
            console.print(f"[dim]{display_name} has no files to browse.[/dim]")
            return

        name_width = min(40, max(12, max(len(item["name"]) for item in items)))
        options = [
            (index, file_label(item, name_width)) for index, item in enumerate(items)
        ]
        options.append(("back", "Back"))

        choice = select_one(
            f"{display_name}: select a file to inspect",
            options,
            max_visible=MENU_MAX_VISIBLE,
        )
        if choice in (None, "back"):
            return
        file_actions(repository_path, display_name, items[choice])


def render_tracked_table(display_name: str, tracked: list[dict]) -> Table:
    table = Table(
        title=f"{display_name}: tracked resources",
        title_style="bold",
        expand=False,
    )
    table.add_column("Name")
    table.add_column("File")
    table.add_column("Size", justify="right")
    table.add_column("Status")
    for item in tracked:
        status = (
            "[yellow]stale (skip)[/yellow]" if item["stale"] else "[red]clear[/red]"
        )
        table.add_row(
            item["name"],
            item["path"].name,
            format_size(item["size"]),
            status,
        )
    return table


def render_files_table(display_name: str, files: list[pathlib.Path]) -> Table:
    table = Table(
        title=f"{display_name}: on-disk entries",
        title_style="bold",
        box=None,
        padding=(0, 2, 0, 0),
        expand=False,
    )
    table.add_column("File")
    table.add_column("Type")
    for path in files:
        table.add_row(path.name, "directory" if path.is_dir() else "file")
    return table


def clear_repository(key: str) -> None:
    # Remove only the files referenced by non-stale metadata entries, then reset
    # the index. Untracked and stale files are left untouched.
    repository_path = SERVER_DATA_DIRECTORY / key
    display_name = REPOSITORIES[key]
    metadata = load_metadata(repository_path)
    tracked = collect_tracked(repository_path, metadata)

    console.print(render_tracked_table(display_name, tracked))
    live = [item for item in tracked if not item["stale"]]
    stale = [item for item in tracked if item["stale"]]
    if stale:
        console.print(
            f"  [yellow]{len(stale)} stale entr"
            f"{'y' if len(stale) == 1 else 'ies'} will be ignored.[/yellow]",
        )
    if not live:
        console.print(
            f"[yellow]{display_name} has no tracked files to clear.[/yellow]",
        )
        # The index may still hold stale entries; offer to reset it anyway.
        if not stale:
            return

    summary = Table(show_header=False, box=None, padding=(0, 2, 0, 0), expand=False)
    summary.add_row("Mode", "Clear (tracked files)")
    summary.add_row("Repository", display_name)
    summary.add_row("Files to remove", str(len(live)))
    summary.add_row("Metadata", "Reset to {}")
    console.print(Panel(summary, title="Review", border_style="cyan", expand=False))

    confirmed = confirm(
        "This permanently deletes the tracked files above and resets the index. "
        "Continue?",
        default=False,
    )
    if not confirmed:
        console.print("[yellow]Aborted. Nothing was removed.[/yellow]")
        return

    removed = 0
    for item in live:
        try:
            remove_path(item["path"])
            removed += 1
        except OSError as error:
            console.print(f"[red]Failed to remove {item['path']}: {error}[/red]")
    reset_metadata(repository_path)
    ensure_keep(repository_path)
    console.print(
        f"[green]Cleared {display_name}: removed {removed} file"
        f"{'' if removed == 1 else 's'} and reset the index.[/green]",
    )


def hard_reset_repository(key: str) -> None:
    # Remove every entry (tracked or not) and restore the default state of just
    # .gitkeep and an empty .repository.json.
    repository_path = SERVER_DATA_DIRECTORY / key
    display_name = REPOSITORIES[key]
    files = collect_all_files(repository_path)

    console.print(render_files_table(display_name, files))
    if not files:
        console.print(
            f"[dim]{display_name} is already at its default state.[/dim]",
        )

    summary = Table(show_header=False, box=None, padding=(0, 2, 0, 0), expand=False)
    summary.add_row("Mode", "Hard reset (all files)")
    summary.add_row("Repository", display_name)
    summary.add_row("Files to remove", str(len(files)))
    summary.add_row("Metadata", "Reset to {}")
    summary.add_row("Restored", ".gitkeep + empty .repository.json")
    console.print(Panel(summary, title="Review", border_style="cyan", expand=False))

    confirmed = confirm(
        "This permanently deletes every file (including untracked ones) and "
        "restores the default state. Continue?",
        default=False,
    )
    if not confirmed:
        console.print("[yellow]Aborted. Nothing was removed.[/yellow]")
        return

    removed = 0
    for path in files:
        try:
            remove_path(path)
            removed += 1
        except OSError as error:
            console.print(f"[red]Failed to remove {path}: {error}[/red]")
    reset_metadata(repository_path)
    ensure_keep(repository_path)
    console.print(
        f"[green]Hard reset {display_name}: removed {removed} file"
        f"{'' if removed == 1 else 's'} and restored defaults.[/green]",
    )


def manage_repository(key: str) -> None:
    repository_path = SERVER_DATA_DIRECTORY / key
    display_name = REPOSITORIES[key]
    while True:
        metadata = load_metadata(repository_path)
        tracked = collect_tracked(repository_path, metadata)
        untracked = collect_untracked(repository_path, tracked)
        counts = status_counts(tracked, untracked)
        console.print()
        render_status_line(display_name, counts)

        action = select_one(
            f"{display_name}: choose an action",
            [
                ("browse", "Browse files and metadata"),
                ("clear", "Clear (remove tracked files, reset index)"),
                ("hard", "Hard reset (remove all files, restore defaults)"),
                ("back", "Back to repositories"),
            ],
        )
        if action in (None, "back"):
            return
        if action == "browse":
            browse_files(key)
        elif action == "clear":
            clear_repository(key)
        elif action == "hard":
            hard_reset_repository(key)


def main():
    console.print(
        Panel.fit(
            "Manage Consortium resource repositories (assets, artifacts,\n"
            "payloads). Pick a repository to browse its files and metadata,\n"
            "open or delete individual files, or clear/hard reset the whole\n"
            "repository. All three share the same metadata schema; the per-entry\n"
            "'data' field is rendered generically.",
            title="Consortium Repository Manager",
            border_style="cyan",
        ),
    )

    while True:
        available = []
        for key, display in REPOSITORIES.items():
            repository_path = SERVER_DATA_DIRECTORY / key
            if not repository_path.is_dir():
                continue
            metadata = load_metadata(repository_path)
            tracked = collect_tracked(repository_path, metadata)
            untracked = collect_untracked(repository_path, tracked)
            counts = status_counts(tracked, untracked)
            label = (
                f"{display}  "
                f"({counts['live']} tracked, {counts['untracked']} untracked, "
                f"{format_size(counts['size'])})"
            )
            available.append((key, label))

        if not available:
            console.print(
                f"[red]No repositories found under {SERVER_DATA_DIRECTORY}.[/red]",
            )
            return

        options = list(available)
        options.append(("__exit__", "Exit"))
        choice = select_one("Select a repository to manage", options)
        if choice in (None, "__exit__"):
            break
        print_answer("Repository", REPOSITORIES[choice])
        manage_repository(choice)

    console.print("[green]Done.[/green]")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Repository manager aborted.[/yellow]")
