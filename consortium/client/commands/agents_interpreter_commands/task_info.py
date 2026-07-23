from argparse import ArgumentParser

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.agent_task_command_utils import (
    create_task_info_and_task_events_tables,
)
from consortium.client.utils.argparse_utils import positive_int
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import console


class TaskInfoCommand(BaseConnectedCommand):
    name = "t-info"
    description = "Display information about an agent's task by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
            t-info 123e4567-e89b-12d3-a456-42661417400
            t-info 123e4567-e89b-12d3-a456-42661417400 --limit 20  # Show last 20 task events (tail)
            t-info 123e4567-e89b-12d3-a456-42661417400 --offset 0 --limit 5  # Show first 5 task events
            t-info 123e4567-e89b-12d3-a456-42661417400 --offset -5 --limit 10  # Show 10 task events starting from 5th from end
            t-info 123e4567-e89b-12d3-a456-42661417400 --raw  # Print task events as plain unformatted text (useful for copy-paste)
            t-info 123e4567-e89b-12d3-a456-42661417400 --raw --limit 50  # Print last 50 task events as plain text
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
                "Maximum number of task events to return. "
                "When specified without --offset, returns the last N entries (tail). "
                "Must be a positive integer. Default is 10."
            ),
            type=positive_int,
            default=None,
        )
        parser.add_argument(
            "-o",
            "--offset",
            help=(
                "Starting position in the task event log. Positive values start from "
                "the beginning, negative values offset from the end. "
                "If not specified, returns the tail (last N entries based on limit)."
            ),
            type=int,
            default=None,
        )
        parser.add_argument(
            "-r",
            "--raw",
            help=(
                "Print task events as plain unformatted text instead of a table. "
                "Each event message is printed on its own line. "
                "Useful for tasks that produce output intended to be copied or piped. "
                "The task info table and events summary are still displayed."
            ),
            action="store_true",
        )

    @staticmethod
    async def _display_task_info(
        rest_api: RestAPI,
        task_id: str,
        limit: int | None = None,
        offset: int | None = None,
        raw: bool = False,
    ) -> None:
        task = await rest_api.get_agent_task_by_task_id(
            task_id=task_id,
            limit=limit,
            offset=offset,
        )

        task_info_table, task_events_table = create_task_info_and_task_events_tables(
            task=task
        )

        console.print(task_info_table, "")

        if raw:
            event_log = task["event_log"]
            entries = event_log["entries"]
            total_count = event_log["total_count"]
            print(f"Task Events (showing {len(entries)} of {total_count} entries)\n")
            for entry in entries:
                print(entry["message"])
            print()
        else:
            console.print(task_events_table, "")

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
                limit=parsed_args.limit,
                offset=parsed_args.offset,
                raw=parsed_args.raw,
            )
        except SystemExit:
            pass

        return ContinueSignal()
