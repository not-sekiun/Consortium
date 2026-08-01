from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchUseAgentTemplateInterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class AgentTemplateUseCommand(BaseConnectedCommand):
    name = "use"
    description = "Use an agent template to create a new agent generator by switching to its context"
    epilog = format_argparse_epilog(
        """
        Examples:
          use 123e4567-e89b-12d3-a456-426614174000
        """,
    )
    group = "Agent Template Management Commands"
    autocompletes = Autocomplete.AGENT_TEMPLATE_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help="Agent template ID of the agent template to use.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent_template = await rest_api.get_agent_template_by_agent_template_id(
                agent_template_id=parsed_args.agent_template_id[0],
            )
            print_info(
                f"Using agent template: '{agent_template['name']}' "
                f"({agent_template['agent_template_id']})",
            )
            return SwitchUseAgentTemplateInterpreterSignal(
                agent_template=agent_template,
            )
        except SystemExit:
            pass

        return ContinueSignal()
