from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.agent_template_command_utils import (
    display_agent_template_info,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
)


class AgentTemplateInfoCommand(BaseConnectedCommand):
    name = "at-info"
    description = "Display information about an agent template by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          at-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help=(
                "Agent template ID of the agent template to display information for."
            ),
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await display_agent_template_info(
                rest_api=rest_api,
                agent_template_id=parsed_args.agent_template_id[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
