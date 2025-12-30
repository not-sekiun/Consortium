from copy import deepcopy
from typing import TYPE_CHECKING, Any

from prompt_toolkit import HTML
from prompt_toolkit.completion import NestedCompleter

from consortium.client.commands.core_commands import GeneratorsCommand
from consortium.client.commands.use_agent_template_interpreter_commands import (
    USE_AGENT_TEMPLATE_INTERPRETER_COMMANDS,
)
from consortium.client.interpreters.generators_interpreter import (
    COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS,
    GeneratorsInterpreter,
)
from consortium.client.utils.data_structure_utils import (
    extract_nested_completer_dict_from_nested_completer,
)

if TYPE_CHECKING:
    from consortium.client.client_session import ClientSession


class UseAgentTemplateInterpreter(GeneratorsInterpreter):
    def __init__(
        self,
        client_session: ClientSession,
        agent_template: dict[str, Any],
    ):
        # Add a "value" key to the options to store the current value of the
        # option.
        for option in agent_template["options"].values():
            # While technically not necessary since setting current_value overwrites the
            # value in that key, it's good practice to make a deep copy of the
            # default_value key.
            option["value"] = deepcopy(option["default_value"])
        super().__init__(
            prompt=HTML(
                f"<b>Consortium (<ansigreen>Generators</ansigreen>: "
                f"<ansigreen>'{agent_template['name']}' "
                f"({agent_template['agent_template_id']})</ansigreen>)\n> </b>",
            ),
            commands=(
                [
                    command
                    for command in COMBINED_GENERATORS_INTERPRETER_CORE_COMMANDS
                    if command.name not in ("info_agent_template", "use_agent_template")
                ]
                + USE_AGENT_TEMPLATE_INTERPRETER_COMMANDS
                # Add back in the generators command since it's removed in the
                # GENERATORS_INTERPRETER_COMMANDS command list. This allows us to
                # switch out of the context of this specific agent template.
                + [GeneratorsCommand()]
            ),
            client_session=client_session,
            context={
                "agent_template": agent_template,
            },
        )

    async def _initialize_autocomplete(
        self,
        all_agent_generators: list[dict[str, Any]],
        all_agent_templates: list[dict[str, Any]],
    ) -> None:
        nested_completer_dict = extract_nested_completer_dict_from_nested_completer(
            self.prompt_session.completer,
        )
        agent_template = self.context["agent_template"]
        for key, value in {
            command: dict.fromkeys(agent_template["options"])
            for command in [
                "opt-info",
                "set",
                "reset",
                "unset",
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
        await super()._initialize_autocomplete(
            all_agent_generators=all_agent_generators,
            all_agent_templates=all_agent_templates,
        )

    # When switching into the UseAgentTemplateInterpreter, we don't want to list all
    # agent generators and agent templates, this was done in the parent generators
    # interpreter once when the user entered it.
    @staticmethod
    def _list_all_agent_generators_and_agent_templates(
        all_agent_generators: list[dict[str, Any]],
        all_agent_templates: list[dict[str, Any]],
    ) -> None:
        pass
