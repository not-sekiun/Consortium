from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import (
    format_agent_task_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
)
from consortium.client.utils.printer_utils import console


class TaskInfoCommand(BaseCommand):
    name = "t-info"
    description = "Display information about an agent's task by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
            t-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "task_id",
            help="ID of the task to display information for.",
            type=str,
        )

    @staticmethod
    async def _display_task_info(
        rest_api: RestAPI,
        task_id: str,
    ) -> None:
        task = await rest_api.get_agent_task_by_task_id(
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
        table.add_row(
            "Datetime Started",
            format_datetime_as_human_readable_str(
                datetime_str=task["datetime_started"], include_elapsed_time=True
            ),
        )

        console.print(table, "")

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_task_info(
                rest_api=rest_api,
                task_id=parsed_args.task_id,
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
