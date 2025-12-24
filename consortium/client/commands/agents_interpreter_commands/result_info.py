from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api_connection import ClientRESTAPIConnection
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import (
    format_agent_result_status_string_with_color,
    format_argparse_epilog,
    format_dict_as_multi_line_key_value_string,
)
from consortium.client.utils.printer_utils import CONSOLE


class ResultInfoCommand(BaseCommand):
    name = "result_info"
    description = "Display detailed information about a specific agent result."
    epilog = format_argparse_epilog(
        """
        Examples:
            result_info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "result_id",
            help="The result ID of the result to display detailed information for.",
            type=str,
        )

    @staticmethod
    async def _display_result_info_from_agent_id(
        client_rest_api_connection: ClientRESTAPIConnection,
        result_id: str,
    ) -> None:
        result = await client_rest_api_connection.get_agent_result_by_result_id(
            result_id=result_id,
        )

        table = Table(title="Result Information", highlight=True)
        table.add_column("Information")
        table.add_column("Data")
        table.add_row("Result ID", str(result["result_id"]))
        table.add_row("Task ID", str(result["task_id"]))
        table.add_row("Command", str(result["command"]))
        table.add_row(
            "Arguments",
            format_dict_as_multi_line_key_value_string(input_dict=result["arguments"]),
        )
        table.add_row(
            "Status",
            format_agent_result_status_string_with_color(
                status_str=str(result["status"])
            ),
        )
        table.add_row("Message", str(result["message"]))
        table.add_row("Datetime Started", str(result["datetime_finished"]))
        table.add_row("Datetime Finished", str(result["datetime_finished"]))
        table.add_row("Elapsed Time", f"{result['elapsed_seconds']:.2f}s")
        CONSOLE.print(table)

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            await self._display_result_info_from_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                result_id=parsed_args.result_id,
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
