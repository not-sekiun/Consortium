from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
)
from consortium.client.utils.listener_template_command_utils import (
    display_listener_template_info,
)


class ListenerTemplateInfoCommand(BaseCommand[ConnectedContext]):
    name = "lt-info"
    description = "Display information about a listener template by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          lt-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help=(
                "Listener template ID of the listener template to display information "
                "for."
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

            await display_listener_template_info(
                rest_api=rest_api,
                listener_template_id=parsed_args.listener_template_id[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
