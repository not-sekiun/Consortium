import json
import pathlib

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

console = Console()

# Inline (non fullscreen) menu widgets styled after Charm-like TUIs. These
# render in the normal terminal flow and erase themselves on exit, after which
# a compact "answer" line is printed so the transcript stays readable.
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

# Metadata for each component type: the on-disk directory under
# consortium/components/, the manifest entry point, a dashed singular used for
# the optional pyproject project name, and a human-readable display name.
COMPONENT_TYPES = {
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
        self.agent_templates_payload_service.create_payload_file(
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
    # Falls back to None so the script still runs outside the project.
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
    info = COMPONENT_TYPES[component_type]

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


def main():
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
        [(key, info["display"]) for key, info in COMPONENT_TYPES.items()],
    )
    if component_type is None:
        console.print("[yellow]Aborted.[/yellow]")
        return

    info = COMPONENT_TYPES[component_type]
    print_answer("Component type", info["display"])

    # Human-readable name drives the directory, module name, and label.
    while True:
        name = prompt_text(
            session,
            f"{info['display']} name (human-readable, e.g. 'Agent Report'): ",
            required=True,
        )
        snake_name = to_snake_case(name)
        project_directory = pathlib.Path(
            "consortium",
            "components",
            info["directory"],
            snake_name,
        )
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


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Component creation aborted.[/yellow]")
