from argparse import ArgumentParser

from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.agent_template_command_utils import (
    display_agent_template_info,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentTemplateInfoCommand(BaseCommand):
    name = "at-info"
    description = (
        "Display information about the current agent template, or a specific "
        "agent template by its ID."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          at-info  # Displays detailed information for the currently selected agent template being used if the agent template ID is not specified.
          at-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help=(
                "ID of the agent template to display information for (defaults to the "
                "current agent template if not specified)."
            ),
            nargs="?",
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # Retrieve information about the current agent template from the server
            # rather than using the cached info because options may have changed
            await display_agent_template_info(
                rest_api=rest_api,
                agent_template_id=parsed_args.agent_template_id
                if parsed_args.agent_template_id
                else context.interpreter_context["agent_template"]["agent_template_id"],
            )
        except SystemExit:
            pass

        return ContinueSignal()
