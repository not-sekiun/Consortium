from copy import deepcopy
from typing import TYPE_CHECKING, Any

from prompt_toolkit import HTML

from consortium.client.commands.core_commands import ListenersCommand
from consortium.client.commands.use_listener_template_interpreter_commands import (
    USE_LISTENER_TEMPLATE_INTERPRETER_COMMANDS,
)
from consortium.client.interpreters.listeners_interpreter import (
    COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS,
    ListenersInterpreter,
)
from consortium.client.models.interpreter_context_models import (
    UseListenerTemplateInterpreterContext,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class UseListenerTemplateInterpreter(ListenersInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        interpreter_context: UseListenerTemplateInterpreterContext,
    ):
        listener_template = interpreter_context.listener_template
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
                f"({listener_template['listener_template_id']})</ansiblue>)\n> </b>",
            ),
            commands=(
                [
                    command
                    for command in COMBINED_LISTENERS_INTERPRETER_CORE_COMMANDS
                    if command.name not in ("lt-info", "use")
                ]
                + USE_LISTENER_TEMPLATE_INTERPRETER_COMMANDS
                # Add back in the listeners command since it's removed in the
                # LISTENERS_INTERPRETER_COMMANDS command list. This allows us to switch
                # out of the context of this specific listener template.
                + [ListenersCommand()]
            ),
            client_session=client_session,
            interpreter_context=interpreter_context,
        )

    async def _initialize_autocomplete(
        self,
        all_listeners: list[dict[str, Any]],
        all_listener_templates: list[dict[str, Any]],
    ) -> None:
        listener_template = self.interpreter_context.listener_template

        completions_dict = self.completer.get_completions_dict()

        options_completion = dict.fromkeys(listener_template["options"])
        for command in ["opt-info", "set", "reset", "unset"]:
            completions_dict[command] = options_completion

        self.completer.set_completions_dict(completions_dict)

        # We run the parent method after we have updated the autocomplete with this
        # interpreter's commands to ensure that when it is called, the autocomplete
        # updating will account for these new commands when autocompleting the help
        # command.
        await super()._initialize_autocomplete(
            all_listeners=all_listeners,
            all_listener_templates=all_listener_templates,
        )

    # When switching into the UseListenerTemplateInterpreter, we don't want to list all
    # listeners and listener templates, this was done in the parent listener
    # interpreter once when the user entered it.
    @staticmethod
    def _list_all_listeners_and_listener_templates(
        all_listeners: list[dict[str, Any]],
        all_listener_templates: list[dict[str, Any]],
    ) -> None:
        pass
