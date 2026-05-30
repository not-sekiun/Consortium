from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.listener_template_command_utils import (
    display_listener_template_info,
)


class ListenerTemplateInfoCommand(BaseCommand[ConnectedContext]):
    name = "lt-info"
    description = (
        "Display information about the current listener template, or a specific "
        "listener template by its ID."
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
                "ID of the listener template to display information for (defaults to "
                "the current listener template if not specified)."
            ),
            nargs="?",
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # Retrieve information about the current listener template from the server
            # rather than using the cached info because a new agent profile may have
            # been loaded or removed, causing the registered compatible agent types
            # information to be stale
            await display_listener_template_info(
                rest_api=rest_api,
                listener_template_id=parsed_args.listener_template_id
                if parsed_args.listener_template_id is not None
                else context.interpreter_context.listener_template[
                    "listener_template_id"
                ],
            )
        except SystemExit:
            pass

        return ContinueSignal()
