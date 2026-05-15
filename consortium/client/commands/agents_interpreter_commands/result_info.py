from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_agent_result_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
)
from consortium.client.utils.printer_utils import console


class ResultInfoCommand(BaseCommand):
    name = "r-info"
    description = "Display information about an agent's result by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
            r-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "result_id",
            help="ID of the result to display information for.",
            type=str,
        )

    @staticmethod
    async def _display_result_info(
        rest_api: RestAPI,
        result_id: str,
    ) -> None:
        result = await rest_api.get_agent_result_by_result_id(
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
        table.add_row(
            "Datetime Started",
            format_datetime_as_human_readable_str(
                datetime_str=result["datetime_started"]
            ),
        )
        table.add_row(
            "Datetime Finished",
            format_datetime_as_human_readable_str(
                datetime_str=result["datetime_finished"], include_elapsed_time=True
            ),
        )
        table.add_row("Elapsed Time", f"{result['elapsed_seconds']:.2f}s")
        console.print(table, "")

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_result_info(
                rest_api=rest_api,
                result_id=parsed_args.result_id,
            )
        except SystemExit:
            pass

        return ContinueSignal()
