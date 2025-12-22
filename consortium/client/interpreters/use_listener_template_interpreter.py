from copy import deepcopy
from typing import TYPE_CHECKING, Any

from prompt_toolkit import HTML
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands import ListenersCommand
from consortium.client.commands.use_listener_template_interpreter_commands import (
    USE_LISTENER_TEMPLATE_INTERPRETER_COMMANDS,
)
from consortium.client.interpreters.listeners_interpreter import (
    COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS,
    ListenersInterpreter,
)
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class UseListenerTemplateInterpreter(ListenersInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        listener_template: dict[str, Any],
    ):
        # Add a "value" key to the options to store the current value of the
        # option.
        for option in listener_template["options"].values():
            # While technically not necessary since setting current_value overwrites the
            # value in that key, it's good practice to make a deep copy of the
            # default_value key.
            option["value"] = deepcopy(option["default_value"])
        super().__init__(
            prompt=HTML(
                f"<b>Consortium (<ansiblue>Listeners</ansiblue>: "
                f"<ansiblue>{listener_template['name']} "
                f"({listener_template['listener_template_id']})</ansiblue>) > </b>",
            ),
            commands=(
                [
                    command
                    for command in COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS
                    if command.name
                    not in ("info_listener_template", "use_listener_template")
                ]
                + USE_LISTENER_TEMPLATE_INTERPRETER_COMMANDS
                # Add back in the listeners command since it's removed in the
                # LISTENERS_INTERPRETER_COMMANDS command list. This allows us to switch
                # out of the context of this specific listener template.
                + [ListenersCommand()]
            ),
            client_session=client_session,
            additional_environment_variables={
                "listener_template": listener_template,
            },
        )

    async def _update_autocomplete(self) -> None:
        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        listener_template = self.environment["listener_template"]
        for key, value in {
            command: dict.fromkeys(listener_template["options"])
            for command in [
                "info_listener_template_option",
                "set_listener_template_option",
                "reset_listener_template_option",
                "unset_listener_template_option",
            ]
        }.items():
            nested_completer_dict[key] = value
        self.prompt_session.completer = NestedCompleter.from_nested_dict(
            nested_completer_dict,
        )

        # We run the parent method after we have updated the autocomplete with this
        # interpreter's commands to ensure that when it is called, the autocomplete
        # updating will account for these new commands when autocompleting the help
        # command.
        await super()._update_autocomplete()
