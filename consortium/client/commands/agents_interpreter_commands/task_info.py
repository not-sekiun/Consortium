from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseCommand
from consortium.client.utils.formatter_utils import (
    format_agent_task_progress_status_string_with_color,
    format_agent_task_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
)
from consortium.client.utils.printer_utils import console


class TaskInfoCommand(BaseCommand[ConnectedContext]):
    name = "t-info"
    description = "Display information about an agent's task by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
            t-info 123e4567-e89b-12d3-a456-42661417400
            t-info 123e4567-e89b-12d3-a456-42661417400 --limit 20  # Show last 20 progress entries (tail)
            t-info 123e4567-e89b-12d3-a456-42661417400 --offset 0 --limit 5  # Show first 5 progress entries
            t-info 123e4567-e89b-12d3-a456-42661417400 --offset -5 --limit 10  # Show 10 entries starting from 5th from end
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "task_id",
            help="ID of the task to display information for.",
            type=str,
        )
        parser.add_argument(
            "-l",
            "--limit",
            help=(
                "Maximum number of progress log entries to return. "
                "When specified without --offset, returns the last N entries (tail). "
                "Must be a positive integer. Default is 10."
            ),
            type=int,
            default=None,
        )
        parser.add_argument(
            "-o",
            "--offset",
            help=(
                "Starting position in the progress log. Positive values start from "
                "the beginning, negative values offset from the end. "
                "If not specified, returns the tail (last N entries based on limit)."
            ),
            type=int,
            default=None,
        )

    # This method is separated out because it is also used by the watch command
    @staticmethod
    def build_task_tables(task: dict) -> tuple[Table, Table]:
        task_info_table = Table(title="Task Information", highlight=True)
        task_info_table.add_column("Information")
        task_info_table.add_column("Data")
        task_info_table.add_row("Task ID", task["task_id"])
        task_info_table.add_row("Command", task["command"])
        task_info_table.add_row(
            "Arguments",
            format_dict_as_multi_line_key_value_string(input_dict=task["arguments"]),
        )
        task_info_table.add_row(
            "Status", format_agent_task_status_string_with_color(task["status"])
        )
        task_info_table.add_row(
            "Current Progress",
            f"{task['current_progress']['message']} "
            f"({task['current_progress']['percent_complete']}% complete)"
            if task["current_progress"]
            else "N/A",
        )
        task_info_table.add_row(
            "Datetime Created",
            format_datetime_as_human_readable_str(
                datetime_str=task["datetime_created"], include_elapsed_time=True
            ),
        )
        task_info_table.add_row(
            "Datetime Started",
            format_datetime_as_human_readable_str(
                datetime_str=task["datetime_started"], include_elapsed_time=True
            )
            if task["datetime_started"] is not None
            else "N/A",
        )

        progress_log = task["progress_log"]
        total_count = progress_log["total_count"]
        entries = progress_log["entries"]
        task_progress_log_table = Table(
            title=(
                f"Task Progress Log Information (showing {len(entries)} of {total_count} entries)"
            ),
            highlight=True,
        )
        task_progress_log_table.add_column("#", justify="right")
        task_progress_log_table.add_column("Status")
        task_progress_log_table.add_column("Message")
        task_progress_log_table.add_column("% Done")
        task_progress_log_table.add_column("Datetime Reported")
        for progress in entries:
            task_progress_log_table.add_row(
                str(progress["sequence"]),
                format_agent_task_progress_status_string_with_color(
                    status_str=progress["status"]
                ),
                progress["message"],
                f"{progress['percent_complete']}%",
                format_datetime_as_human_readable_str(
                    datetime_str=progress["datetime_reported"],
                    include_elapsed_time=True,
                ),
            )

        return task_info_table, task_progress_log_table

    @staticmethod
    async def _display_task_info(
        rest_api: RestAPI,
        task_id: str,
        progress_limit: int | None = None,
        progress_offset: int | None = None,
    ) -> None:
        task = await rest_api.get_agent_task_by_task_id(
            task_id=task_id,
            progress_limit=progress_limit,
            progress_offset=progress_offset,
        )

        task_info_table, task_progress_log_table = TaskInfoCommand.build_task_tables(
            task
        )

        console.print(task_info_table, "")
        console.print(task_progress_log_table, "")

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_task_info(
                rest_api=rest_api,
                task_id=parsed_args.task_id,
                progress_limit=parsed_args.limit,
                progress_offset=parsed_args.offset,
            )
        except SystemExit:
            pass

        return ContinueSignal()
