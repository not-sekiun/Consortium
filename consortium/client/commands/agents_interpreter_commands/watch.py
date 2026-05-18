import asyncio
from argparse import ArgumentParser

from rich.console import Group
from rich.live import Live

from consortium.client.client_rest_api import RestAPI
from consortium.client.commands.agents_interpreter_commands.task_info import (
    TaskInfoCommand,
)
from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import console, print_info, print_warning


class WatchCommand(BaseCommand):
    name = "watch"
    description = "Continuously watch a task until it completes"
    epilog = format_argparse_epilog(
        """
        Examples:
            watch 123e4567-e89b-12d3-a456-42661417400
            watch 123e4567-e89b-12d3-a456-42661417400 --interval 5
            watch 123e4567-e89b-12d3-a456-42661417400 --limit 20  # Show last 20 progress entries (tail)
            watch 123e4567-e89b-12d3-a456-42661417400 --offset 0 --limit 5  # Show first 5 progress entries
            watch 123e4567-e89b-12d3-a456-42661417400 --offset -5 --limit 10  # Show 10 entries starting from 5th from end
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "task_id",
            help="ID of the task to watch.",
            type=str,
        )
        parser.add_argument(
            "--interval",
            "-i",
            help="Polling interval in seconds (defaults to 1 second).",
            type=float,
            default=1.0,
        )
        parser.add_argument(
            "-l",
            "--limit",
            help=(
                "Maximum number of progress log entries to return. "
                "When specified without --offset, returns the last N entries (tail). "
                "Must be a positive integer (defaults to 10 entries)."
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

    @staticmethod
    async def _fetch_and_build_display(
        rest_api: RestAPI,
        task_id: str,
        progress_limit: int | None = None,
        progress_offset: int | None = None,
    ) -> tuple[Group, str]:
        task = await rest_api.get_agent_task_by_task_id(
            task_id=task_id,
            progress_limit=progress_limit,
            progress_offset=progress_offset,
        )

        task_info_table, task_progress_log_table = TaskInfoCommand.build_task_tables(
            task=task
        )
        display = Group(task_info_table, "", task_progress_log_table, "")

        return display, task["status"]

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            task_id = parsed_args.task_id
            interval = parsed_args.interval
            progress_limit = parsed_args.limit
            progress_offset = parsed_args.offset

            if progress_limit and progress_limit > 100:
                print_warning(
                    f"Displaying {progress_limit} log entries (> 100) may cause "
                    f"[bold red]performance issues[/] during live updates for the server and client."
                )
                response = input("Continue anyway? [y/N]: ").strip().lower()
                if response not in ("y", "yes"):
                    print_info("Watch cancelled.")
                    return ContinueSignal()
            else:
                # Ensure progress_limit has a default value even if not explicitly set
                progress_limit = progress_limit or 10

            if interval <= 0:
                print_warning(
                    "Polling interval must be a positive number. Using 1 second."
                )
                interval = 1.0
            elif interval < 0.5:
                print_warning(
                    "Polling interval's that are too low (< 0.5s) may cause "
                    "performance issues."
                )

            try:
                # Initial fetch
                display, status = await self._fetch_and_build_display(
                    rest_api=rest_api,
                    task_id=task_id,
                    progress_limit=progress_limit,
                    progress_offset=progress_offset,
                )

                if status == "COMPLETED":
                    print_info("Task is already completed. Displaying final status:\n")
                    console.print(display)
                else:
                    print_info(f"Watching task: {task_id}")
                    print_info(f"Polling interval: {interval} seconds")
                    print_info("Press CTRL-C at any time to stop watching\n")

                    with Live(
                        display, console=console, refresh_per_second=1 / interval
                    ) as live:
                        while True:
                            if status == "COMPLETED":
                                print_info("Task completed. Stopping watch.")
                                break

                            await asyncio.sleep(interval)

                            display, status = await self._fetch_and_build_display(
                                rest_api=rest_api,
                                task_id=task_id,
                                progress_limit=progress_limit,
                                progress_offset=progress_offset,
                            )
                            live.update(display)
            except (KeyboardInterrupt, asyncio.CancelledError):
                print_info("Watch stopped by user.")

        except SystemExit:
            pass

        return ContinueSignal()
