import json
import pathlib
import shutil

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
KEEP_FILENAME = ".keep"
PROTECTED_FILENAMES = {METADATA_FILENAME, KEEP_FILENAME}

# Repositories share the exact same metadata schema; only the per-entry "data"
# field carries domain-specific metadata, which this tool does not touch.
REPOSITORIES = {
    "assets": "Assets",
    "artifacts": "Artifacts",
    "payloads": "Payloads",
}


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


def select_one(message: str, options: list[tuple], default_index: int = 0):
    # options: list of (value, label). Returns the chosen value, or None if the
    # user cancels.
    state = {"index": default_index}
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

    @key_bindings.add("enter")
    def _(event) -> None:
        event.app.exit(result=options[state["index"]][0])

    @key_bindings.add("c-c")
    @key_bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=None)

    def get_text() -> FormattedText:
        fragments = [("class:question", f"? {message}\n")]
        for index, (_value, label) in enumerate(options):
            if index == state["index"]:
                fragments.append(("class:pointer", f"{POINTER} "))
                fragments.append(("class:selected", f"{label}\n"))
            else:
                fragments.append(("", "  "))
                fragments.append(("class:option", f"{label}\n"))
        fragments.append(("class:help", HELP_SINGLE))
        return FormattedText(fragments)

    return _run_menu(get_text, key_bindings, len(options) + 2)


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
    # Human-readable byte count for the summary tables. Falls back to a dash
    # when the metadata does not carry a usable size.
    if not isinstance(num_bytes, (int, float)):
        return "-"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def load_metadata(repository_path: pathlib.Path) -> dict:
    # Read the metadata index explicitly. A missing or unreadable index is
    # treated as empty so the tool can still hard clear a broken repository.
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


def resolve_entry_path(
    repository_path: pathlib.Path,
    resource_id: str,
    entry: dict,
) -> pathlib.Path:
    # On-disk resources are stored as "<resource_id><extension>". Directory
    # resources have no extension.
    extension = entry.get("extension") or ""
    return repository_path / f"{resource_id}{extension}"


def collect_tracked(repository_path: pathlib.Path, metadata: dict) -> list[dict]:
    # Build the list of resources to clear straight from the metadata index.
    # Entries whose backing file is missing are flagged stale and skipped.
    tracked = []
    for resource_id, entry in metadata.items():
        if not isinstance(entry, dict):
            # Malformed entry: nothing sensible to delete, so ignore it.
            continue
        path = resolve_entry_path(repository_path, resource_id, entry)
        tracked.append(
            {
                "name": entry.get("name", resource_id),
                "path": path,
                "size": entry.get("size"),
                "is_directory": bool(entry.get("is_directory")),
                "stale": not path.exists(),
            },
        )
    return tracked


def collect_all_files(repository_path: pathlib.Path) -> list[pathlib.Path]:
    # Every on-disk entry except the protected metadata index and placeholder.
    # Used by hard clear so untracked resources are removed as well.
    return sorted(
        (
            child
            for child in repository_path.iterdir()
            if child.name not in PROTECTED_FILENAMES
        ),
        key=lambda child: child.name,
    )


def reset_metadata(repository_path: pathlib.Path) -> None:
    (repository_path / METADATA_FILENAME).write_text("{}\n", encoding="utf-8")


def ensure_keep(repository_path: pathlib.Path) -> None:
    keep_path = repository_path / KEEP_FILENAME
    if not keep_path.exists():
        keep_path.write_text("", encoding="utf-8")


def remove_path(path: pathlib.Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def render_tracked_table(display_name: str, tracked: list[dict]) -> Table:
    table = Table(
        title=f"{display_name}: tracked resources",
        title_style="bold",
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
    )
    table.add_column("File")
    table.add_column("Type")
    for path in files:
        table.add_row(
            path.name,
            "directory" if path.is_dir() else "file",
        )
    return table


def clear_normal(repository_path: pathlib.Path, tracked: list[dict]) -> int:
    # Remove only the files referenced by non-stale metadata entries, then reset
    # the index. Untracked and stale files are left untouched.
    removed = 0
    for item in tracked:
        if item["stale"]:
            continue
        try:
            remove_path(item["path"])
            removed += 1
        except OSError as error:
            console.print(f"[red]Failed to remove {item['path']}: {error}[/red]")
    reset_metadata(repository_path)
    ensure_keep(repository_path)
    return removed


def clear_hard(repository_path: pathlib.Path, files: list[pathlib.Path]) -> int:
    # Remove every entry (tracked or not) and restore the default state of just
    # .keep and an empty .repository.json.
    removed = 0
    for path in files:
        try:
            remove_path(path)
            removed += 1
        except OSError as error:
            console.print(f"[red]Failed to remove {path}: {error}[/red]")
    reset_metadata(repository_path)
    ensure_keep(repository_path)
    return removed


def main():
    console.print(
        Panel.fit(
            "Clear Consortium resource repositories (assets, artifacts,\n"
            "payloads). Normal clear removes the files listed in each\n"
            "repository's .repository.json and resets it to an empty index.\n"
            "Hard clear additionally removes untracked files, restoring the\n"
            "default state of only .keep and an empty .repository.json.",
            title="Consortium Repository Cleaner",
            border_style="cyan",
        ),
    )

    mode = select_one(
        "Clear mode",
        [
            ("normal", "Normal clear (tracked files from metadata)"),
            ("hard", "Hard clear (all files, including untracked)"),
        ],
    )
    if mode is None:
        console.print("[yellow]Aborted.[/yellow]")
        return
    hard = mode == "hard"
    print_answer("Clear mode", "Hard clear" if hard else "Normal clear")

    available = [
        (key, display)
        for key, display in REPOSITORIES.items()
        if (SERVER_DATA_DIRECTORY / key).is_dir()
    ]
    if not available:
        console.print(
            f"[red]No repositories found under {SERVER_DATA_DIRECTORY}.[/red]",
        )
        return

    selected = select_many(
        "Select repositories to clear",
        available,
        preselect_all=True,
    )
    if selected is None:
        console.print("[yellow]Aborted.[/yellow]")
        return
    if not selected:
        console.print("[yellow]No repositories selected. Nothing to do.[/yellow]")
        return
    print_answer(
        "Repositories",
        ", ".join(REPOSITORIES[key] for key in selected),
    )

    # Gather what each selected repository would clear so the user reviews the
    # full plan before anything is deleted.
    plans = []
    total_to_remove = 0
    for key in selected:
        repository_path = SERVER_DATA_DIRECTORY / key
        display_name = REPOSITORIES[key]
        metadata = load_metadata(repository_path)
        tracked = collect_tracked(repository_path, metadata)

        if hard:
            files = collect_all_files(repository_path)
            console.print(render_files_table(display_name, files))
            if not files:
                console.print(f"  [dim]{display_name} is already empty.[/dim]")
            total_to_remove += len(files)
            plans.append({"key": key, "hard": True, "files": files})
        else:
            console.print(render_tracked_table(display_name, tracked))
            live = [item for item in tracked if not item["stale"]]
            stale = [item for item in tracked if item["stale"]]
            if not tracked:
                console.print(f"  [dim]{display_name} has no tracked resources.[/dim]")
            if stale:
                console.print(
                    f"  [yellow]{len(stale)} stale entr"
                    f"{'y' if len(stale) == 1 else 'ies'} will be ignored.[/yellow]",
                )
            total_to_remove += len(live)
            plans.append({"key": key, "hard": False, "tracked": tracked})
        console.print()

    if total_to_remove == 0 and not hard:
        console.print("[yellow]Nothing to clear.[/yellow]")
        return

    summary = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    summary.add_row("Mode", "Hard clear" if hard else "Normal clear")
    summary.add_row(
        "Repositories",
        ", ".join(REPOSITORIES[key] for key in selected),
    )
    summary.add_row("Files to remove", str(total_to_remove))
    if hard:
        summary.add_row("Metadata", "Reset to {}")
        summary.add_row("Restored", ".keep + empty .repository.json")
    else:
        summary.add_row("Metadata", "Reset to {}")
    console.print(Panel(summary, title="Review", border_style="cyan", expand=False))

    confirmed = confirm(
        "This permanently deletes the files above. Continue?",
        default=False,
    )
    if not confirmed:
        console.print("[yellow]Aborted. Nothing was removed.[/yellow]")
        return

    for plan in plans:
        repository_path = SERVER_DATA_DIRECTORY / plan["key"]
        display_name = REPOSITORIES[plan["key"]]
        if plan["hard"]:
            removed = clear_hard(repository_path, plan["files"])
        else:
            removed = clear_normal(repository_path, plan["tracked"])
        console.print(
            f"[green]Cleared {display_name}: removed {removed} file"
            f"{'' if removed == 1 else 's'}.[/green]",
        )

    console.print(
        Panel.fit(
            "Repositories cleared. Selected .repository.json indexes were\n"
            "reset to an empty object and .keep placeholders were preserved.",
            title="Done",
            border_style="green",
        ),
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Repository clear aborted.[/yellow]")
