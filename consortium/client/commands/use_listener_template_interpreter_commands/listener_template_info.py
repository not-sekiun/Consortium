from argparse import ArgumentParser

from consortium.client.commands.listeners_interpreter_commands.listener_template_info import (
    ListenerTemplateInfoCommand as ListenersInterpreterListenerTemplateInfoCommand,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ListenerTemplateInfoCommand(ListenersInterpreterListenerTemplateInfoCommand):
    name = "lt-info"
    description = (
        "Display information about the current listener template, or a specific "
        "listener template by its listener template ID."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          lt-info  # Displays detailed information for the currently selected listener template being used if the listener template ID is not specified.
          lt-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Template Management Commands"

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

    async def run(self, context: Context) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            if parsed_args.listener_template_id is not None:
                listener_template = (
                    await rest_api.get_listener_template_by_listener_template_id(
                        listener_template_id=parsed_args.listener_template_id
                    )
                )
            else:
                listener_template = context.environment["listener_template"]
            self._display_listener_template_info(listener_template=listener_template)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
