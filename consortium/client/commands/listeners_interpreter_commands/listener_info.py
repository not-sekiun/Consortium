from argparse import ArgumentParser

from rich.table import Table

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
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
    format_listener_state_string_with_color,
)
from consortium.client.utils.printer_utils import console


class ListenerInfoCommand(BaseCommand):
    name = "info"
    description = "Display information about a listener by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_id",
            help="ID of the listener to display information for.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            listener = await rest_api.get_listener_by_listener_id(
                parsed_args.listener_id[0],
            )
            table = Table(title="Listener Information", highlight=True)
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Listener ID",
                listener["listener_id"],
            )
            table.add_row("Name", listener["name"])
            table.add_row("Description", listener["description"])
            table.add_row("Endpoint", listener["endpoint"])
            table.add_row(
                "Listener Type",
                listener["listener_type"]["name"],
            )
            # Imprecise wording for this row but improves UX by hiding technical
            # implementation details
            table.add_row(
                "Compatible Agent Types",
                format_list_as_multi_line_bulleted_string(
                    input_list=listener["listener_type"][
                        "registered_compatible_agent_types"
                    ]
                ),
            )
            table.add_row(
                "Status",
                format_listener_state_string_with_color(listener["status"]["state"])
                + (
                    "(" + listener["status"]["error"]["message"] + ")"
                    if listener["status"]["error"]
                    else ""
                ),
            )
            table.add_row(
                "Parameters",
                format_dict_as_multi_line_key_value_string(
                    input_dict=listener["parameters"]
                ),
            )
            table.add_row(
                "Datetime Created",
                format_datetime_as_human_readable_str(
                    datetime_str=listener["datetime_created"], include_elapsed_time=True
                ),
            )
            table.add_row(
                "Connected Agents",
                format_list_as_multi_line_bulleted_string(
                    input_list=[
                        f"'{agent['name']}' ({agent['agent_id']})"
                        for agent in listener["connected_agents"]
                    ],
                ),
            )
            table.add_row(
                "Creating Listener Template",
                f"'{listener['creating_listener_template']['name']}' "
                f"({listener['creating_listener_template']['listener_template_id']})",
            )
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
