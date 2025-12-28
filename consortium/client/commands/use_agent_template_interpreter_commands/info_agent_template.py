from argparse import ArgumentParser

from consortium.client.commands.generators_interpreter_commands.info_agent_template import (
    InfoAgentTemplateCommand as GeneratorsInterpreterInfoAgentTemplateCommand,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.formatter_utils import format_argparse_epilog


class InfoAgentTemplateCommand(GeneratorsInterpreterInfoAgentTemplateCommand):
    description = (
        "Display detailed information about a specific agent template or about the "
        "currently selected agent template being used."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info_agent_template  # Displays detailed information for the currently selected agent template being used if the agent template ID is not specified.
          info_agent_template 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help=(
                "The agent template ID of the agent template to display detailed "
                "information for. If not provided, detailed information for the "
                "currently selected agent template is displayed."
            ),
            nargs="?",
            default=None,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.client_session.rest_api
            if parsed_args.agent_template_id is not None:
                agent_template = await client_rest_api_connection.get_agent_template_by_agent_template_id(
                    agent_template_id=parsed_args.agent_template_id
                )
            else:
                agent_template = context.interpreter_context["agent_template"]
            self._display_agent_template_info(agent_template=agent_template)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
