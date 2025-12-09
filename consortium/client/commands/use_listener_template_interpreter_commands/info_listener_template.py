from argparse import ArgumentParser

from consortium.client.commands.listeners_interpreter_commands.info_listener_template import (
    InfoListenerTemplateCommand as ListenersInterpreterInfoListenerTemplateCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class InfoListenerTemplateCommand(ListenersInterpreterInfoListenerTemplateCommand):
    description = (
        "Display detailed information about a specific listener template or about the "
        "currently selected listener template being used."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          info_listener_template  # Displays detailed information for the currently selected listener template being used if the listener template ID is not specified.
          info_listener_template 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help=(
                "The listener template ID of the listener template to display detailed "
                "information for. If not provided, detailed information for the "
                "currently selected listener template is displayed."
            ),
            nargs="?",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            if parsed_args.listener_template_id is None:
                listener_template = command_context.environment["listener_template"]
            else:
                listener_template = await client_rest_api_connection.get_listener_template_by_listener_template_id(
                    parsed_args.listener_template_id,
                )
            self._display_listener_template_info(listener_template=listener_template)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
