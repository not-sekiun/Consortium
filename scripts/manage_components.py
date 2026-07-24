import importlib
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile

import jsonschema
from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

SCRIPT_DIRECTORY = pathlib.Path(__file__).resolve().parent

console = Console()

# Inline (non fullscreen) menu widgets styled after Charm-like TUIs. These
# render in the normal terminal flow and erase themselves on exit, after which
# a compact "answer" line is printed so the transcript stays readable. Kept in
# sync with scripts/manage_repository.py so all of these scripts feel the same.
POINTER = "❯"  # heavy right-pointing angle
CHECKED = "[x]"
UNCHECKED = "[ ]"
HELP_SINGLE = "  (up/down to move, enter to select, ctrl-c to cancel)"
HELP_MULTI = "  (up/down to move, space to toggle, enter to confirm)"
HELP_CONFIRM = "  (left/right or y/n to change, enter to confirm)"
HELP_MANAGE = (
    "  (up/down to move, space to enable/disable, enter to view, esc to go back)"
)

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
        # Enabled/disabled/invalid states and the danger confirmation prompt.
        "enabled": "ansigreen bold",
        "disabled": "ansired bold",
        "danger": "ansired bold",
    },
)

# Resolve the project layout relative to this script so the tool works
# regardless of the current working directory. PROJECT_ROOT is also the import
# root: component entry-point modules resolve to dotted paths relative to it
# (e.g. consortium.components.listeners.consortium.http.listener_template),
# mirroring ComponentLoaderService.
PROJECT_ROOT = SCRIPT_DIRECTORY.parent
COMPONENTS_DIRECTORY = PROJECT_ROOT / "consortium" / "components"

# The upper-level directories under consortium/components that separate the
# component kinds. Each is walked recursively for manifest.json files, and each
# is an install target directory.
COMPONENT_TYPES = {
    "listeners": "Listeners",
    "agents": "Agents",
    "plugins": "Plugins",
    "event_hooks": "Event Hooks",
}

MANIFEST_FILENAME = "manifest.json"

# Directory entries never carried into an install. These are build/VCS
# artifacts that should not be pasted into the components tree.
INSTALL_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    "*.pyc",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
)

# Mirrors the schema every ComponentLoaderService subclass validates a manifest
# against (all four kinds share the same shape). Only manifests whose JSON
# parses and validates against this schema are treated as manageable
# components.
MANIFEST_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "entry_point": {"type": "string"},
        "enabled": {"type": "boolean"},
    },
    "required": ["entry_point", "enabled"],
    "additionalProperties": False,
}

# The class-level metadata attributes exposed by every component (defined on
# ComponentMetadata / ComponentMetadataModel). Used as a fallback when the
# framework model cannot be imported to enumerate them dynamically.
METADATA_FIELDS = (
    "label",
    "name",
    "description",
    "version",
    "compatible_framework_version",
    "authors",
    "component_dependencies",
)

MENU_MAX_VISIBLE = 15


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


def _clamp_offset(index: int, offset: int, visible: int) -> int:
    # Keep the highlighted row inside a scrolling window of `visible` rows.
    if index < offset:
        return index
    if index >= offset + visible:
        return index - visible + 1
    return offset


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
        index = state["index"]
        offset = _clamp_offset(index, state["offset"], visible)
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


def confirm(message: str, default: bool = True, danger: bool = False):
    # Returns True/False, or None if the user cancels. When danger is set the
    # question is rendered in bold red for destructive actions.
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

    question_style = "class:danger" if danger else "class:question"

    def get_text() -> FormattedText:
        if state["value"]:
            yes = ("class:selected", "[ Yes ]")
            no = ("class:option", "  No  ")
        else:
            yes = ("class:option", "  Yes  ")
            no = ("class:selected", "[ No ]")
        return FormattedText(
            [
                (question_style, f"? {message}  "),
                yes,
                ("", " "),
                no,
                ("", "\n"),
                ("class:help", HELP_CONFIRM),
            ],
        )

    return _run_menu(get_text, key_bindings, 2)


def get_metadata_fields() -> tuple[str, ...]:
    # Prefer the authoritative field list from the framework model so the info
    # view stays in sync with it, but fall back to the local constant if the
    # framework cannot be imported (e.g. run outside its environment).
    ensure_import_root()
    try:
        from consortium.framework._core.components import ComponentMetadataModel

        return tuple(ComponentMetadataModel.model_fields.keys())
    except Exception:
        return METADATA_FIELDS


_framework_bootstrapped = False


def ensure_import_root() -> None:
    # Make the project root importable so component entry-point modules resolve
    # to their dotted paths under the consortium package. Also pre-load the full
    # server module tree once: several framework modules import server_singletons
    # at module level (which in turn imports every service), so importing a
    # component cold triggers circular-import errors unless the tree is fully
    # cached first. Mirrors what the test conftests do.
    global _framework_bootstrapped
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    if not _framework_bootstrapped:
        _framework_bootstrapped = True
        try:
            importlib.import_module("consortium.server.server_singletons")
        except Exception:
            # If the tree cannot be pre-loaded, component imports may still fail
            # with circular-import errors; those surface per component in the
            # info view rather than crashing the manager.
            pass


def validate_manifest(manifest_path: pathlib.Path) -> tuple[dict | None, str | None]:
    # Read and schema-validate a manifest. Returns (manifest_json, None) on
    # success or (None, error_message) when the file is unreadable, not valid
    # JSON, or does not satisfy the manifest schema.
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest_json = json.load(handle)
    except OSError as error:
        return None, f"could not read manifest: {error}"
    except json.JSONDecodeError as error:
        return None, f"invalid JSON: {error}"
    try:
        jsonschema.validate(manifest_json, MANIFEST_JSON_SCHEMA)
    except jsonschema.ValidationError as error:
        return None, f"schema error: {error.message}"
    return manifest_json, None


def discover_components() -> tuple[list[dict], list[dict]]:
    # Recursively walk each component-kind directory for manifest.json files.
    # Returns (valid, invalid): valid components carry their parsed manifest and
    # entry point; invalid ones carry only the reason they were skipped.
    valid = []
    invalid = []
    for type_key, type_label in COMPONENT_TYPES.items():
        type_directory = COMPONENTS_DIRECTORY / type_key
        if not type_directory.is_dir():
            continue
        for manifest_path in sorted(type_directory.rglob(MANIFEST_FILENAME)):
            folder = manifest_path.parent
            rel_name = folder.relative_to(type_directory).as_posix()
            manifest_json, error = validate_manifest(manifest_path)
            if error is not None:
                invalid.append(
                    {
                        "type_key": type_key,
                        "type_label": type_label,
                        "folder": folder,
                        "rel_name": rel_name,
                        "manifest_path": manifest_path,
                        "valid": False,
                        "error": error,
                    },
                )
                continue
            entry_point = manifest_json["entry_point"]
            module_str, _, symbol = entry_point.partition(":")
            valid.append(
                {
                    "type_key": type_key,
                    "type_label": type_label,
                    "folder": folder,
                    "rel_name": rel_name,
                    "manifest_path": manifest_path,
                    "manifest": manifest_json,
                    "entry_point": entry_point,
                    "module": module_str,
                    "symbol": symbol,
                    "enabled": bool(manifest_json["enabled"]),
                    "valid": True,
                },
            )
    return valid, invalid


def status_fragment(entry: dict) -> tuple[str, str]:
    # (style, text) describing an entry's state, coloured green/red.
    if not entry.get("valid", True):
        return ("class:disabled", "invalid")
    if entry["enabled"]:
        return ("class:enabled", "enabled")
    return ("class:disabled", "disabled")


def import_component_class(component: dict):
    # Resolve the entry-point module to its file, import it, and return the
    # entry-point symbol (the component class). Mirrors how
    # ComponentLoaderService locates and imports a component. Returns
    # (component_class, None) or (None, error_message).
    if not component["symbol"]:
        return None, (
            "manifest entry_point must be in the format 'module_path:SymbolName'"
        )
    ensure_import_root()
    component_file = pathlib.Path(component["folder"], *component["module"].split("."))
    component_file = component_file.parent / (component_file.name + ".py")
    if not component_file.exists():
        return None, f"entry-point module not found: {component_file}"
    module_path = ".".join(component_file.relative_to(PROJECT_ROOT).parts)[
        : -len(".py")
    ]
    try:
        if module_path in sys.modules:
            module = importlib.reload(sys.modules[module_path])
        else:
            module = importlib.import_module(module_path)
    except Exception as error:
        return None, f"failed to import component: {error}"
    try:
        return getattr(module, component["symbol"]), None
    except AttributeError:
        return None, (
            f"symbol '{component['symbol']}' not found in {component_file.name}"
        )


def format_metadata_value(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, (set, frozenset)):
        return ", ".join(str(item) for item in sorted(value, key=str)) or "-"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) or "-"
    text = str(value)
    return text if text != "" else "-"


def render_component_info(component: dict) -> None:
    # Show the manifest-derived facts first (always available), then import the
    # component and list its class-level metadata attributes.
    manifest_table = Table(
        show_header=False, box=None, padding=(0, 2, 0, 0), expand=False
    )
    manifest_table.add_row("Kind", component["type_label"])
    manifest_table.add_row("Name", component["rel_name"])
    manifest_table.add_row("Folder", str(component["folder"]))
    manifest_table.add_row("Entry point", component["entry_point"])
    manifest_table.add_row(
        "Enabled",
        "[green]yes[/green]" if component["enabled"] else "[red]no (disabled)[/red]",
    )
    console.print(
        Panel(
            manifest_table,
            title=f"{component['type_label']}: {component['rel_name']}",
            border_style="cyan",
            expand=False,
        ),
    )

    component_class, error = import_component_class(component)
    if error is not None:
        console.print(
            Panel(
                error,
                title="Component metadata",
                border_style="yellow",
                expand=False,
            ),
        )
        return

    metadata_table = Table(
        show_header=False, box=None, padding=(0, 2, 0, 0), expand=False
    )
    for field in get_metadata_fields():
        value = getattr(component_class, field, None)
        metadata_table.add_row(field, format_metadata_value(value))
    console.print(
        Panel(
            metadata_table,
            title=f"Component metadata ({component['symbol']})",
            border_style="blue",
            expand=False,
        ),
    )


def set_enabled(component: dict, enabled: bool) -> tuple[bool, str | None]:
    # Flip the manifest's enabled flag in place, preserving the rest of the
    # manifest. Returns (ok, error_message).
    manifest = dict(component["manifest"])
    manifest["enabled"] = enabled
    try:
        component["manifest_path"].write_text(
            json.dumps(manifest, indent=4) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        return False, str(error)
    component["manifest"] = manifest
    component["enabled"] = enabled
    return True, None


def manage_menu(components: list[dict], max_visible: int = MENU_MAX_VISIBLE):
    # Interactive list where space toggles a component's enabled flag (persisted
    # to its manifest immediately) and enter opens the information view for the
    # highlighted component. Returns the highlighted index on enter, or None if
    # the user backs out.
    total = len(components)
    visible = min(max_visible, total)
    name_width = min(40, max(12, max(len(c["rel_name"]) for c in components)))
    state = {"index": 0, "offset": 0, "error": None}
    key_bindings = KeyBindings()

    @key_bindings.add("up")
    @key_bindings.add("k")
    @key_bindings.add("c-p")
    def _(event) -> None:
        state["index"] = (state["index"] - 1) % total
        state["error"] = None

    @key_bindings.add("down")
    @key_bindings.add("j")
    @key_bindings.add("c-n")
    def _(event) -> None:
        state["index"] = (state["index"] + 1) % total
        state["error"] = None

    @key_bindings.add("space")
    def _(event) -> None:
        component = components[state["index"]]
        ok, error = set_enabled(component, not component["enabled"])
        state["error"] = (
            None if ok else f"could not update {component['rel_name']}: {error}"
        )

    @key_bindings.add("enter")
    def _(event) -> None:
        event.app.exit(result=state["index"])

    @key_bindings.add("c-c")
    @key_bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=None)

    def get_text() -> FormattedText:
        index = state["index"]
        offset = _clamp_offset(index, state["offset"], visible)
        state["offset"] = offset

        fragments = [("class:question", "? Manage components\n")]
        for position in range(offset, min(offset + visible, total)):
            component = components[position]
            selected = position == index
            row_style = "class:selected" if selected else "class:option"
            fragments.append(
                ("class:pointer", f"{POINTER} ") if selected else ("", "  "),
            )
            enabled = component["enabled"]
            fragments.append(
                (
                    "class:enabled" if enabled else "class:disabled",
                    f"{CHECKED if enabled else UNCHECKED} ",
                ),
            )
            fragments.append((row_style, f"{component['type_label'].ljust(11)}  "))
            name = component["rel_name"]
            if len(name) > name_width:
                name = name[: name_width - 1] + "…"
            fragments.append((row_style, f"{name.ljust(name_width)}  "))
            fragments.append(status_fragment(component))
            fragments.append(("", "\n"))
        if state["error"]:
            fragments.append(("class:danger", f"  {state['error']}"))
        elif visible < total:
            fragments.append(
                ("class:help", f"{HELP_MANAGE}  ({index + 1}/{total})"),
            )
        else:
            fragments.append(("class:help", HELP_MANAGE))
        return FormattedText(fragments)

    return _run_menu(get_text, key_bindings, visible + 2)


def component_picker(
    message: str,
    entries: list[dict],
    max_visible: int = MENU_MAX_VISIBLE,
):
    # Single-select list showing each component's kind, name and coloured
    # status. Returns the chosen index, or None if the user cancels.
    total = len(entries)
    visible = min(max_visible, total)
    name_width = min(40, max(12, max(len(e["rel_name"]) for e in entries)))
    state = {"index": 0, "offset": 0}
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
        event.app.exit(result=state["index"])

    @key_bindings.add("c-c")
    @key_bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=None)

    def get_text() -> FormattedText:
        index = state["index"]
        offset = _clamp_offset(index, state["offset"], visible)
        state["offset"] = offset

        fragments = [("class:question", f"? {message}\n")]
        for position in range(offset, min(offset + visible, total)):
            entry = entries[position]
            selected = position == index
            row_style = "class:selected" if selected else "class:option"
            fragments.append(
                ("class:pointer", f"{POINTER} ") if selected else ("", "  "),
            )
            fragments.append((row_style, f"{entry['type_label'].ljust(11)}  "))
            name = entry["rel_name"]
            if len(name) > name_width:
                name = name[: name_width - 1] + "…"
            fragments.append((row_style, f"{name.ljust(name_width)}  "))
            fragments.append(status_fragment(entry))
            fragments.append(("", "\n"))
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


def manage_flow() -> None:
    valid, invalid = discover_components()
    if invalid:
        render_invalid(invalid)
    if not valid:
        console.print(
            f"[yellow]No valid components found under {COMPONENTS_DIRECTORY}.[/yellow]",
        )
        return
    while True:
        choice = manage_menu(valid)
        if choice is None:
            return
        console.print()
        render_component_info(valid[choice])
        console.print()


def render_invalid(invalid: list[dict]) -> None:
    if not invalid:
        return
    table = Table(
        title="Skipped manifests (invalid JSON / schema)",
        title_style="bold yellow",
        box=None,
        padding=(0, 2, 0, 0),
        expand=False,
    )
    table.add_column("Kind")
    table.add_column("Name")
    table.add_column("Reason")
    for entry in invalid:
        table.add_row(entry["type_label"], entry["rel_name"], entry["error"])
    console.print(table)


def uninstall_flow() -> None:
    valid, invalid = discover_components()
    entries = valid + invalid
    if not entries:
        console.print(
            f"[yellow]No components found under {COMPONENTS_DIRECTORY}.[/yellow]",
        )
        return

    console.print()
    choice = component_picker("Select a component to uninstall", entries)
    if choice is None:
        return
    entry = entries[choice]
    print_answer("Uninstall", f"{entry['type_label']}: {entry['rel_name']}")

    console.print(
        Panel(
            f"This permanently deletes the entire folder:\n\n"
            f"  [bold]{entry['folder']}[/bold]\n\n"
            "This cannot be undone.",
            title="Uninstall",
            border_style="red",
            expand=False,
        ),
    )
    confirmed = confirm(
        f"Delete {entry['type_label']} component '{entry['rel_name']}'?",
        default=False,
        danger=True,
    )
    if not confirmed:
        console.print("[yellow]Uninstall cancelled. Nothing was removed.[/yellow]")
        return
    try:
        shutil.rmtree(entry["folder"])
    except OSError as error:
        console.print(f"[red]Failed to uninstall {entry['rel_name']}: {error}[/red]")
        return
    console.print(f"[green]Uninstalled {entry['rel_name']}.[/green]")


def _safe_extract(dest: pathlib.Path, members) -> bool:
    # Reject archive members with absolute paths or parent traversal so an
    # extract can never write outside dest. Returns False if any member is
    # unsafe.
    dest = dest.resolve()
    for name in members:
        target = (dest / name).resolve()
        if not str(target).startswith(str(dest)):
            return False
    return True


def fetch_from_local(session: PromptSession):
    # Returns (source_root, None) on success (no temp dir to clean up), or None.
    raw = prompt_text(
        session,
        "Path to the local component directory: ",
        required=True,
    )
    source = pathlib.Path(raw).expanduser()
    if not source.is_dir():
        console.print(f"[red]Not a directory: {source}[/red]")
        return None
    return source.resolve(), None


def fetch_from_git(session: PromptSession):
    # Clone a repository shallowly into a temp directory. Returns (clone_dir,
    # temp_dir) or None. The temp dir must be cleaned up by the caller.
    url = prompt_text(session, "Git repository URL: ", required=True)
    branch = prompt_text(session, "Branch/tag (blank for default): ")
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="consortium_install_"))
    clone_dir = temp_dir / "repo"
    command = ["git", "clone", "--depth", "1"]
    if branch:
        command += ["--branch", branch]
    command += [url, str(clone_dir)]
    console.print(f"[dim]Cloning {url}...[/dim]")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        console.print("[red]git is not available on this system.[/red]")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None
    if result.returncode != 0:
        console.print(f"[red]git clone failed:[/red]\n{result.stderr.strip()}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None
    return clone_dir, temp_dir


def fetch_from_http_archive(session: PromptSession):
    # Download a .zip/.tar archive over HTTP(S) and extract it into a temp
    # directory. Returns (extracted_dir, temp_dir) or None. The temp dir must be
    # cleaned up by the caller.
    url = prompt_text(
        session,
        "URL of the component archive (.zip/.tar/.tar.gz): ",
        required=True,
    )
    temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="consortium_install_"))
    archive_path = temp_dir / "archive"
    extract_dir = temp_dir / "extracted"
    extract_dir.mkdir()
    console.print(f"[dim]Downloading {url}...[/dim]")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "consortium"})
        with (
            urllib.request.urlopen(request) as response,
            archive_path.open(  # noqa: S310
                "wb"
            ) as handle,
        ):
            shutil.copyfileobj(response, handle)
    except (urllib.error.URLError, ValueError, OSError) as error:
        console.print(f"[red]Download failed: {error}[/red]")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    try:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as archive:
                if not _safe_extract(extract_dir, archive.namelist()):
                    raise ValueError("archive contains unsafe paths")
                archive.extractall(extract_dir)
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as archive:
                names = archive.getnames()
                if not _safe_extract(extract_dir, names):
                    raise ValueError("archive contains unsafe paths")
                archive.extractall(extract_dir)
        else:
            console.print("[red]Unsupported archive format (need zip or tar).[/red]")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    except (tarfile.TarError, zipfile.BadZipFile, ValueError, OSError) as error:
        console.print(f"[red]Extraction failed: {error}[/red]")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None
    return extract_dir, temp_dir


def find_component_projects(root: pathlib.Path) -> list[pathlib.Path]:
    # A component project is any directory containing a manifest.json. Return
    # them sorted, including root itself if it holds one.
    projects = []
    if (root / MANIFEST_FILENAME).is_file():
        projects.append(root)
    for manifest_path in sorted(root.rglob(MANIFEST_FILENAME)):
        if manifest_path.parent != root:
            projects.append(manifest_path.parent)
    return projects


def collect_collisions(
    source_project: pathlib.Path,
    target: pathlib.Path,
) -> list[pathlib.Path]:
    # An install must never overwrite anything. Deny if the target project
    # directory already exists at all (even empty), or if any file/dir the paste
    # would create already exists. Returns the list of conflicting paths.
    conflicts = []
    if target.exists() or target.is_symlink():
        conflicts.append(target)
    for source_path in source_project.rglob("*"):
        destination = target / source_path.relative_to(source_project)
        if destination.exists() or destination.is_symlink():
            conflicts.append(destination)
    # Preserve order while removing duplicates.
    seen = set()
    unique = []
    for path in conflicts:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def install_flow() -> None:
    type_key = select_one(
        "Install into which component folder?",
        list(COMPONENT_TYPES.items()),
    )
    if type_key is None:
        return
    type_label = COMPONENT_TYPES[type_key]
    print_answer("Target folder", type_label)

    source_kind = select_one(
        "Where should the component come from?",
        [
            ("local", "Local directory"),
            ("git", "Git repository (clone)"),
            ("http", "HTTP hosting (archive)"),
        ],
    )
    if source_kind is None:
        return

    session = PromptSession()
    temp_dir = None
    try:
        if source_kind == "local":
            fetched = fetch_from_local(session)
        elif source_kind == "git":
            fetched = fetch_from_git(session)
        else:
            fetched = fetch_from_http_archive(session)
        if fetched is None:
            return
        source_root, temp_dir = fetched

        projects = find_component_projects(source_root)
        if not projects:
            console.print(
                "[red]No manifest.json found in the source; nothing to install.[/red]",
            )
            return
        if len(projects) == 1:
            source_project = projects[0]
        else:
            index = select_one(
                "Multiple components found; choose one to install",
                [
                    (position, project.relative_to(source_root).as_posix() or ".")
                    for position, project in enumerate(projects)
                ],
                max_visible=MENU_MAX_VISIBLE,
            )
            if index is None:
                return
            source_project = projects[index]

        # Schema-validate the manifest before installing; installing a broken
        # component is allowed only if the operator explicitly opts in.
        _, manifest_error = validate_manifest(source_project / MANIFEST_FILENAME)
        if manifest_error is not None:
            console.print(
                f"[yellow]The component's manifest is invalid: "
                f"{manifest_error}[/yellow]",
            )
            proceed = confirm("Install it anyway?", default=False)
            if not proceed:
                console.print("[yellow]Install cancelled.[/yellow]")
                return

        default_name = source_project.name
        dest_name = prompt_text(
            session,
            "Destination folder name: ",
            default=default_name,
            required=True,
        )
        target = COMPONENTS_DIRECTORY / type_key / dest_name

        conflicts = collect_collisions(source_project, target)
        if conflicts:
            listing = "\n".join(f"  {path}" for path in conflicts[:20])
            if len(conflicts) > 20:
                listing += f"\n  ... and {len(conflicts) - 20} more"
            console.print(
                Panel(
                    "Installation denied to avoid overwriting existing files.\n"
                    "The following path(s) already exist:\n\n" + listing,
                    title="Collision detected",
                    border_style="red",
                    expand=False,
                ),
            )
            return

        summary = Table(show_header=False, box=None, padding=(0, 2, 0, 0), expand=False)
        summary.add_row("Kind", type_label)
        summary.add_row("Source", str(source_project))
        summary.add_row("Destination", str(target))
        console.print(
            Panel(summary, title="Review install", border_style="cyan", expand=False),
        )
        confirmed = confirm(f"Install into {target}?", default=True)
        if not confirmed:
            console.print("[yellow]Install cancelled. Nothing was written.[/yellow]")
            return

        try:
            shutil.copytree(source_project, target, ignore=INSTALL_IGNORE)
        except (OSError, shutil.Error) as error:
            console.print(f"[red]Install failed: {error}[/red]")
            return
        console.print(
            Panel.fit(
                f"Installed [bold]{dest_name}[/bold] into {type_label}.\n"
                f"Location: {target}",
                title="Done",
                border_style="green",
            ),
        )
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Component scaffolding (the "Create" action)
#
# This section was previously a standalone create_component_project.py script; it
# is merged in here so the manager owns the whole component lifecycle and has no
# external script dependency. It reuses the manager's shared menu widgets
# (select_one, confirm, print_answer) and only defines what is unique to
# scaffolding: the per-type metadata, the file templates, and the prompt flow.
# --------------------------------------------------------------------------- #

# Metadata for each scaffoldable component type: the on-disk directory under
# consortium/components/, the manifest entry point, a dashed singular used for
# the optional pyproject project name, and a human-readable display name. This is
# keyed by the scaffolder's own type keys and is distinct from COMPONENT_TYPES
# above (which is keyed by the components/ subdirectory name for discovery).
SCAFFOLD_COMPONENT_TYPES = {
    "plugin": {
        "directory": "plugins",
        "segment": "plugins",
        "entry_point": "plugin:Plugin",
        "singular": "plugin",
        "display": "Plugin",
    },
    "event_hook": {
        "directory": "event_hooks",
        "segment": "event_hooks",
        "entry_point": "event_hook:EventHook",
        "singular": "event-hook",
        "display": "Event Hook",
    },
    "listener": {
        "directory": "listeners",
        "segment": "listeners",
        "entry_point": "listener_template:ListenerTemplate",
        "singular": "listener",
        "display": "Listener Profile",
    },
    "agent": {
        "directory": "agents",
        "segment": "agents",
        "entry_point": "agent_template:AgentTemplate",
        "singular": "agent",
        "display": "Agent Profile",
    },
}

# Templates use %%TOKEN%% placeholders instead of str.format so that the braces
# in the generated Python (sets, dicts, f-strings) do not need escaping.

PLUGIN_TEMPLATE = """from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    # Stable, globally unique reverse-DNS identifier for this plugin.
    label = "%%LABEL%%"
    # Human-readable display name.
    name = "%%NAME%%"
    description = "%%DESCRIPTION%%"
    version = "%%VERSION%%"
    # PEP 440 specifier for the framework versions this plugin supports.
    compatible_framework_version = "%%COMPAT%%"
    authors = %%AUTHORS%%
    # Start automatically when the server starts.
    autostart = %%AUTOSTART%%

    # One-time setup before the main loop runs.
    async def on_started(self) -> None: ...

    # Main body: loop here and block on self.stop_event to exit cleanly.
    async def on_running(self) -> None: ...

    # Cleanup after the plugin stops.
    async def on_stopped(self) -> None: ...

    # Called when on_running returns without being stopped.
    async def on_completed(self) -> None: ...

    # Called when the plugin is cancelled.
    async def on_cancelled(self) -> None: ...

    # Called when a PluginRuntimeError propagates out of the lifecycle.
    async def on_errored(self, error) -> None: ...
"""

EVENT_HOOK_TEMPLATE = """from consortium.framework.event_hooks import BaseEventHook, EventType


class EventHook(BaseEventHook):
    label = "%%LABEL%%"
    name = "%%NAME%%"
    description = "%%DESCRIPTION%%"
    version = "%%VERSION%%"
    compatible_framework_version = "%%COMPAT%%"
    authors = %%AUTHORS%%
    # Only events whose type is in this set trigger on_triggered().
    event_types = %%EVENT_TYPES%%

    # One-time setup before any events are handled.
    async def on_setup(self) -> None: ...

    # Called for each subscribed event.
    async def on_triggered(self, event) -> None: ...

    # Cleanup when the server shuts down.
    async def on_teardown(self) -> None: ...
"""

LISTENER_TYPE_TEMPLATE = """from consortium.framework.listeners import BaseListenerType


class ListenerType(BaseListenerType):
    # Transport family name agents connect through. Referenced by agent
    # profiles via compatible_listener_types.
    name = "%%TYPE_NAME%%"
"""

LISTENER_TEMPLATE_TEMPLATE = """from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import SingleValueOption

from .listener import Listener
from .listener_type import ListenerType


class ListenerTemplate(BaseListenerTemplate):
    label = "%%LABEL%%"
    name = "%%NAME%%"
    description = "%%DESCRIPTION%%"
    version = "%%VERSION%%"
    compatible_framework_version = "%%COMPAT%%"
    authors = %%AUTHORS%%

    # The class to instantiate and the transport family it belongs to.
    listener = Listener
    listener_type = ListenerType

    # Parameters an operator supplies when creating a listener instance.
    options = {
        SingleValueOption(
            name="local_host",
            description="IP address to bind to.",
            required=True,
            default_value="0.0.0.0",
            value_type=str,
        ),
        SingleValueOption(
            name="local_port",
            description="Port to listen on.",
            required=True,
            default_value=4444,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=65535,
        ),
        SingleValueOption(
            name="name",
            description="Display name for this listener instance.",
            required=True,
            default_value="",
            value_type=str,
        ),
    }

    # Used when no explicit name is passed to create_listener().
    def resolve_listener_name(self, parameters: dict) -> str:
        return parameters["name"]

    # The returned string becomes self.endpoint on the listener instance.
    def resolve_listener_endpoint(self, parameters: dict) -> str:
        return f"tcp://{parameters['local_host']}:{parameters['local_port']}"
"""

LISTENER_IMPL_TEMPLATE = """from consortium.framework.listeners import BaseListener


class Listener(BaseListener):

    # Validate config (self.parameters) and prepare resources before serving.
    async def on_started(self) -> None:
        self.logger.info("Ready.")

    # Serve until stop_event is set; implement the agent-listener protocol here.
    async def on_running(self) -> None:
        await self.stop_event.wait()

    # Release resources after the listener stops.
    async def on_stopped(self) -> None:
        self.logger.info("Stopped.")

    # Release resources if the listener is cancelled.
    async def on_cancelled(self) -> None: ...
"""

AGENT_TYPE_TEMPLATE = """from consortium.framework.agents import (
    BaseAgentType,
    request_response_capability,
)
from consortium.framework.options import SingleValueOption

# A single command the generated agent can execute. request_response_capability
# builds a simple send-task then await-result capability.
shell_capability = request_response_capability(
    name="shell",
    description="Execute a shell command on the agent.",
    authors=%%AUTHORS%%,
    options={
        SingleValueOption(
            name="command",
            description="Shell command to execute.",
            required=True,
            value_type=str,
        ),
    },
)


class AgentType(BaseAgentType):
    # Type identifier used during agent registration.
    name = "%%TYPE_NAME%%"
    agent_capabilities = {
        shell_capability,
    }
"""

AGENT_GENERATOR_TEMPLATE = """from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)


# One discrete stage of the build pipeline. build() is the only override point;
# the lifecycle hooks are final on build steps.
class BuildScript(BaseAgentGeneratorBuildStep):
    name = "Build Script"
    description = "Write the configured agent payload."

    async def build(self, parameters: dict) -> None:
        # Store build artifacts via self.agent_templates_payload_service.
        await self.agent_templates_payload_service.create_payload_file(
            build_parameters=parameters,
            content="# generated agent payload\\n",
            name="agent.py",
        )


class AgentGenerator(BaseAgentGenerator):
    # Steps run in order. Do not override on_running (it is final and drives the
    # pipeline). Override on_started for pre-build validation instead.
    agent_generator_build_steps = [BuildScript]
"""

AGENT_TEMPLATE_TEMPLATE = """from consortium.framework.agents import BaseAgentTemplate
from consortium.framework.options import SingleValueOption

from .agent_generator import AgentGenerator
from .agent_type import AgentType


class AgentTemplate(BaseAgentTemplate):
    label = "%%LABEL%%"
    name = "%%NAME%%"
    description = "%%DESCRIPTION%%"
    version = "%%VERSION%%"
    compatible_framework_version = "%%COMPAT%%"
    authors = %%AUTHORS%%

    # The pipeline that builds the payload and the capabilities it exposes.
    agent_generator = AgentGenerator
    agent_type = AgentType
    # Listener type names this agent can connect through.
    compatible_listener_types = {"tcp_json"}

    options = {
        SingleValueOption(
            name="remote_host",
            description="Listener host address.",
            required=False,
            default_value="127.0.0.1",
            value_type=str,
        ),
        SingleValueOption(
            name="remote_port",
            description="Listener port.",
            required=False,
            default_value=4444,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=65535,
        ),
        SingleValueOption(
            name="name",
            description="Display name for the generator run.",
            required=False,
            default_value="",
            value_type=str,
        ),
    }

    def resolve_agent_generator_name(self, parameters: dict) -> str:
        return parameters["name"]
"""

PYPROJECT_TEMPLATE = """[project]
name = "%%PROJECT_NAME%%"
dependencies = [%%DEPENDENCIES%%]
"""

README_TEMPLATE = """# %%NAME%%

%%DESCRIPTION%%

- **Type:** %%TYPE_DISPLAY%%
- **Label:** `%%LABEL%%`
- **Version:** %%VERSION%%

## Next steps

1. Edit the generated module file(s) to implement your logic.
2. Ensure `manifest.json` has `"enabled": true`.
3. Start your Consortium server; the component is auto-discovered from its
   `manifest.json`.
"""


def select_many(message: str, options: list[tuple]):
    # options: list of (value, label). Returns a list of checked values in the
    # order they appear, or None if the user cancels.
    state = {"index": 0, "checked": set()}
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
            checked = value in state["checked"]
            mark_style = "class:checked" if checked else "class:unchecked"
            mark = CHECKED if checked else UNCHECKED
            label_style = (
                "class:selected" if index == state["index"] else "class:option"
            )
            fragments.append((pointer_style, f"{pointer} "))
            fragments.append((mark_style, f"{mark} "))
            fragments.append((label_style, f"{label}\n"))
        fragments.append(("class:help", HELP_MULTI))
        return FormattedText(fragments)

    return _run_menu(get_text, key_bindings, len(options) + 2)


def to_snake_case(string: str) -> str:
    return string.replace("-", "_").replace(" ", "_").lower()


def render(template: str, **tokens: str) -> str:
    output = template
    for key, value in tokens.items():
        output = output.replace(f"%%{key}%%", value)
    return output


def format_authors(raw: str) -> str:
    names = [name.strip() for name in raw.split(",") if name.strip()]
    if not names:
        return "set()"
    return "{" + ", ".join(f'"{name}"' for name in names) + "}"


def format_event_types(selected: list[str]) -> str:
    if not selected:
        return "set()"
    lines = ["{"]
    for name in selected:
        lines.append(f"        EventType.{name},")
    lines.append("    }")
    return "\n".join(lines)


def format_dependencies(raw: str) -> str:
    deps = [dep.strip() for dep in raw.split(",") if dep.strip()]
    if not deps:
        return ""
    return "\n" + "".join(f'    "{dep}",\n' for dep in deps)


def load_event_type_choices():
    # Import the real enum so the multiselect stays in sync with the framework.
    # Falls back to None so the flow still runs outside the project.
    ensure_import_root()
    try:
        from consortium.framework.event_hooks import EventType

        return [(member.name, member.name) for member in EventType]
    except Exception:
        return None


def prompt_text(
    session: PromptSession,
    message: str,
    *,
    default: str = "",
    required: bool = False,
) -> str:
    prompt_fragments = [("class:qmark", "? "), ("class:qtext", message)]
    while True:
        value = session.prompt(
            prompt_fragments,
            default=default,
            style=MENU_STYLE,
        ).strip()
        if required and not value:
            console.print("[red]This value cannot be empty.[/red]")
            continue
        return value


def build_component_files(component_type: str, context: dict) -> dict[str, str]:
    info = SCAFFOLD_COMPONENT_TYPES[component_type]

    manifest = json.dumps(
        {"entry_point": info["entry_point"], "enabled": True},
        indent=4,
    )
    readme = render(
        README_TEMPLATE,
        NAME=context["name"],
        DESCRIPTION=context["description"],
        TYPE_DISPLAY=info["display"],
        LABEL=context["label"],
        VERSION=context["version"],
    )

    files = {
        "__init__.py": "",
        "manifest.json": manifest + "\n",
        "README.md": readme,
    }

    if component_type == "plugin":
        files["plugin.py"] = render(
            PLUGIN_TEMPLATE,
            LABEL=context["label"],
            NAME=context["name"],
            DESCRIPTION=context["description"],
            VERSION=context["version"],
            COMPAT=context["compat"],
            AUTHORS=context["authors"],
            AUTOSTART=context["autostart"],
        )
    elif component_type == "event_hook":
        files["event_hook.py"] = render(
            EVENT_HOOK_TEMPLATE,
            LABEL=context["label"],
            NAME=context["name"],
            DESCRIPTION=context["description"],
            VERSION=context["version"],
            COMPAT=context["compat"],
            AUTHORS=context["authors"],
            EVENT_TYPES=context["event_types"],
        )
    elif component_type == "listener":
        files["listener_type.py"] = render(
            LISTENER_TYPE_TEMPLATE,
            TYPE_NAME=context["type_name"],
        )
        files["listener_template.py"] = render(
            LISTENER_TEMPLATE_TEMPLATE,
            LABEL=context["label"],
            NAME=context["name"],
            DESCRIPTION=context["description"],
            VERSION=context["version"],
            COMPAT=context["compat"],
            AUTHORS=context["authors"],
        )
        files["listener.py"] = LISTENER_IMPL_TEMPLATE
    elif component_type == "agent":
        files["agent_type.py"] = render(
            AGENT_TYPE_TEMPLATE,
            AUTHORS=context["authors"],
            TYPE_NAME=context["type_name"],
        )
        files["agent_generator.py"] = AGENT_GENERATOR_TEMPLATE
        files["agent_template.py"] = render(
            AGENT_TEMPLATE_TEMPLATE,
            LABEL=context["label"],
            NAME=context["name"],
            DESCRIPTION=context["description"],
            VERSION=context["version"],
            COMPAT=context["compat"],
            AUTHORS=context["authors"],
        )

    if context.get("pyproject") is not None:
        files["pyproject.toml"] = context["pyproject"]

    return files


def create_flow() -> None:
    # Scaffold a new component under consortium/components/. Refuses to write when
    # the destination directory already exists (including an empty one).
    session = PromptSession()

    console.print(
        Panel.fit(
            "Scaffold a new Consortium component: a plugin, agent profile,\n"
            "listener profile, or event hook. Answer the prompts to generate a\n"
            "commented starting point under consortium/components/.",
            title="Consortium Component Scaffolder",
            border_style="cyan",
        ),
    )

    component_type = select_one(
        "Component type",
        [(key, info["display"]) for key, info in SCAFFOLD_COMPONENT_TYPES.items()],
    )
    if component_type is None:
        console.print("[yellow]Aborted.[/yellow]")
        return

    info = SCAFFOLD_COMPONENT_TYPES[component_type]
    print_answer("Component type", info["display"])

    # Human-readable name drives the directory, module name, and label.
    while True:
        name = prompt_text(
            session,
            f"{info['display']} name (human-readable, e.g. 'Agent Report'): ",
            required=True,
        )
        snake_name = to_snake_case(name)
        # Resolve against COMPONENTS_DIRECTORY (absolute) so scaffolding works
        # regardless of the current working directory, like the rest of the tool.
        project_directory = COMPONENTS_DIRECTORY / info["directory"] / snake_name
        if project_directory.exists():
            console.print(
                f"[red]'{project_directory}' already exists. "
                "Choose a different name.[/red]",
            )
            continue
        break

    namespace = prompt_text(
        session,
        "Label namespace (reverse-DNS prefix): ",
        default="consortium",
        required=True,
    )
    default_label = f"{namespace}.{info['segment']}.{snake_name}"
    label = prompt_text(
        session,
        "Label (unique identifier): ",
        default=default_label,
        required=True,
    )

    description = prompt_text(session, "Description: ")
    version = prompt_text(session, "Version: ", default="0.1.0", required=True)
    compat = prompt_text(
        session,
        "Compatible framework version: ",
        default=">=0.1.0",
        required=True,
    )
    authors_raw = prompt_text(session, "Authors (comma-separated): ")

    context = {
        "name": name,
        "label": label,
        "description": description,
        "version": version,
        "compat": compat,
        "authors": format_authors(authors_raw),
        "type_name": snake_name,
    }

    # Type-specific prompts.
    if component_type == "plugin":
        autostart = confirm(
            "Start this plugin automatically when the server starts?",
            default=False,
        )
        if autostart is None:
            console.print("[yellow]Aborted. Nothing was written.[/yellow]")
            return
        context["autostart"] = "True" if autostart else "False"
        print_answer("Autostart", "Yes" if autostart else "No")

    if component_type == "event_hook":
        choices = load_event_type_choices()
        if choices is not None:
            selected = select_many(
                "Select the events this hook subscribes to",
                choices,
            )
            if selected is None:
                console.print("[yellow]Aborted. Nothing was written.[/yellow]")
                return
        else:
            raw = prompt_text(
                session,
                "Event types (comma-separated, e.g. AGENT_REGISTERED): ",
            )
            selected = [item.strip() for item in raw.split(",") if item.strip()]
        context["event_types"] = format_event_types(selected)
        print_answer("Event types", ", ".join(selected) if selected else "none")

    # Optional pyproject.toml for third-party dependencies.
    add_pyproject = confirm(
        "Add a pyproject.toml to declare third-party dependencies?",
        default=False,
    )
    if add_pyproject is None:
        console.print("[yellow]Aborted. Nothing was written.[/yellow]")
        return
    print_answer("Add pyproject.toml", "Yes" if add_pyproject else "No")
    if add_pyproject:
        deps_raw = prompt_text(
            session,
            "Dependencies (comma-separated, blank for none): ",
        )
        project_name = f"consortium.{snake_name.replace('_', '-')}-{info['singular']}"
        context["pyproject"] = render(
            PYPROJECT_TEMPLATE,
            PROJECT_NAME=project_name,
            DEPENDENCIES=format_dependencies(deps_raw),
        )

    files = build_component_files(component_type, context)

    # Summary and final confirmation.
    summary = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    summary.add_row("Type", info["display"])
    summary.add_row("Name", name)
    summary.add_row("Label", label)
    summary.add_row("Version", version)
    summary.add_row("Directory", str(project_directory))
    summary.add_row("Files", ", ".join(sorted(files)))
    console.print(Panel(summary, title="Review", border_style="cyan", expand=False))

    confirmed = confirm(
        f"Create this {info['display']} at {project_directory}?",
        default=True,
    )
    if not confirmed:
        console.print("[yellow]Aborted. Nothing was written.[/yellow]")
        return

    project_directory.mkdir(parents=True)
    for filename, content in files.items():
        (project_directory / filename).write_text(content)

    console.print(
        Panel.fit(
            f"Created {info['display']} at [bold]{project_directory}[/bold]\n\n"
            "Next steps:\n"
            f"  1. Edit the module file(s) in {project_directory}\n"
            "  2. Start your Consortium server; the component is auto-discovered\n"
            "     from its manifest.json.",
            title="Done",
            border_style="green",
        ),
    )


def main() -> None:
    console.print(
        Panel.fit(
            "Manage Consortium components: listeners, agents, plugins, and event\n"
            "hooks under consortium/components/. Create new components, enable/\n"
            "disable and inspect existing ones, install from a local directory,\n"
            "git repository, or HTTP archive, and uninstall.",
            title="Consortium Component Manager",
            border_style="cyan",
        ),
    )

    if not COMPONENTS_DIRECTORY.is_dir():
        console.print(
            f"[red]Components directory not found: {COMPONENTS_DIRECTORY}[/red]",
        )
        return

    actions = {
        "create": create_flow,
        "manage": manage_flow,
        "install": install_flow,
        "uninstall": uninstall_flow,
    }

    while True:
        console.print()
        choice = select_one(
            "What would you like to do?",
            [
                ("create", "Create a new component"),
                ("manage", "Manage components (enable/disable, view info)"),
                ("install", "Install a component (local / git / HTTP archive)"),
                ("uninstall", "Uninstall a component (delete)"),
                ("__exit__", "Exit"),
            ],
        )
        if choice in (None, "__exit__"):
            break
        try:
            actions[choice]()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Cancelled. Back to the main menu.[/yellow]")

    console.print("[green]Done.[/green]")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Component manager aborted.[/yellow]")
