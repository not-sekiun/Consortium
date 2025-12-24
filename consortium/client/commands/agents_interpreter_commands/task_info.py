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
    format_agent_task_status_string_with_color,
    format_argparse_epilog,
    format_dict_as_multi_line_key_value_string,
)
from consortium.client.utils.printer_utils import CONSOLE


class TaskInfoCommand(BaseCommand):
    name = "task_info"
    description = "Display detailed information about a specific agent task."
    epilog = format_argparse_epilog(
        """
        Examples:
            task_info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "task_id",
            help="The task ID of the task to display detailed information for.",
            type=str,
        )

    @staticmethod
    async def _display_task_info_from_agent_id_and_task_id(
        client_rest_api_connection: ClientRESTAPIConnection,
        task_id: str,
    ) -> None:
        task = await client_rest_api_connection.get_agent_task_by_task_id(
            task_id=task_id,
        )

        table = Table(title="Task Information", highlight=True)
        table.add_column("Information")
        table.add_column("Data")
        table.add_row("Task ID", task["task_id"])
        table.add_row("Command", task["command"])
        table.add_row(
            "Arguments",
            format_dict_as_multi_line_key_value_string(input_dict=task["arguments"]),
        )
        table.add_row(
            "Status", format_agent_task_status_string_with_color(task["status"])
        )
        table.add_row("Datetime Started", task["datetime_started"])

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
            await self._display_task_info_from_agent_id_and_task_id(
                client_rest_api_connection=client_rest_api_connection,
                task_id=parsed_args.task_id,
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
