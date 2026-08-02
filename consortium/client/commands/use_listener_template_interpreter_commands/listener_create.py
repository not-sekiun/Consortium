from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class ListenerCreateCommand(BaseConnectedCommand):
    name = "create"
    description = "Create a listener from the current listener template and start it (use --no-start to skip starting)"
    epilog = format_argparse_epilog(
        """
        Examples:
          create
          create --no-start
          create -n "My listener"
          create -n "My listener" -d "Catches the long haul implants"
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-n",
            "--name",
            help=(
                "Name to give the created listener (defaults to a randomly generated "
                "one)."
            ),
            nargs="?",
        )
        parser.add_argument(
            "-d",
            "--description",
            help="Description to give the created listener.",
            nargs="?",
            default="",
        )
        parser.add_argument(
            "--no-start",
            help="Create the listener without starting it.",
            action="store_true",
            default=False,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            listener_template_id = context.interpreter_context.listener_template[
                "listener_template_id"
            ]
            listener_template_options = context.interpreter_context.listener_template[
                "options"
            ]

            listener_template_option_values = {}
            for option_name, option in listener_template_options.items():
                listener_template_option_values[option_name] = option["value"]
            # The name and description are sent separately from the option values: they
            # are the created listener's display metadata rather than listener template
            # options, so a listener template that declares its own option called `name`
            # or `description` still sets that option through `set` as normal. A name of
            # `None` means none was given, leaving the server to generate one.
            listener = await rest_api.create_listener_through_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
                listener_template_option_values=listener_template_option_values,
                name=parsed_args.name,
                description=parsed_args.description,
            )
            if parsed_args.no_start:
                print_success(
                    f"Created listener: '{listener['name']}' ({listener['listener_id']})",
                )
            else:
                _ = await rest_api.start_listener_by_listener_id(
                    listener_id=listener["listener_id"],
                )
                print_success(
                    f"Created and started listener: '{listener['name']}' ({listener['listener_id']})",
                )
        except SystemExit:
            pass

        return ContinueSignal()
