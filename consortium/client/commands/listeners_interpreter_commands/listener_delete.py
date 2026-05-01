import textwrap
from argparse import ArgumentParser

from prompt_toolkit import HTML, PromptSession

from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_list_as_multi_line_bulleted_string,
)
from consortium.client.utils.printer_utils import print_success, print_warning


class ListenerDeleteCommand(BaseCommand):
    name = "delete"
    description = "Delete a non-running listener by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          delete 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener to delete.",
            nargs=1,
        )

    async def run(self, context: Context) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # If listener does not exist, a RESTAPIError is raised and caught by the
            # outer try-except block
            listener = await rest_api.get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )

            if (
                listener["connected_agents"]
                and listener["status"]["state"] != "RUNNING"
            ):  # You can't delete a running listener
                print_warning(
                    f"Listener '{listener['name']}' ({listener['listener_id']}) has the following connected agents:",
                )
                print(
                    textwrap.indent(
                        format_list_as_multi_line_bulleted_string(
                            [
                                f"'{agent['name']}' ({agent['agent_id']})"
                                for agent in listener["connected_agents"]
                            ],
                        ),
                        "    ",
                    )
                    + "\n"
                )
                confirmation = await PromptSession().prompt_async(
                    HTML(
                        "Are you sure you want to delete this listener? This will cause "
                        "those agents to be <b><ansired>permanently "
                        "unreachable</ansired></b> (y/N): ",
                    )
                )
                if confirmation.lower() != "y":
                    return ContinueSignal()

            _ = await rest_api.delete_listener_by_listener_id(
                listener_id=parsed_args.listener_id[0],
            )
            print_success(
                f"Deleted listener: '{listener['name']}' ({listener['listener_id']})",
            )
        except SystemExit:
            pass

        return ContinueSignal()
