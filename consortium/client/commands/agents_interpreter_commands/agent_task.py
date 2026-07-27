import asyncio
import textwrap
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from typing import Any

from rich.console import Group
from rich.live import Live
from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.agent_task_command_utils import (
    create_task_info_and_task_events_tables,
)
from consortium.client.utils.argparse_utils import positive_int
from consortium.client.utils.formatter_utils import (
    format_agent_task_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_single_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
)
from consortium.client.utils.printer_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)


class TaskCommand(BaseConnectedCommand):
    name = "task"
    description = "Manage agent tasks through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          task list
          task info 123e4567-e89b-12d3-a456-42661417400
          task watch 123e4567-e89b-12d3-a456-42661417400
          task delete 123e4567-e89b-12d3-a456-42661417400

        Notes:
          Every sub-command carries its own help, for example:
            task info --help
        """,
    )
    group = "Agent Management Commands"
    autocompletes = {
        "list": Autocomplete.AGENT_ID,
        "info": Autocomplete.AGENT_TASK_ID,
        "watch": Autocomplete.AGENT_TASK_ID,
        "delete": Autocomplete.AGENT_TASK_ID,
    }
    # Help and examples for `task list`, declared as class attributes so that the
    # interact agent interpreter's variant of this command can scope them to the agent
    # being interacted with without having to redeclare every sub-parser.
    list_help = "List all tasks, or a specific agent's tasks by its ID."
    list_agent_id_help = (
        "ID of the agent to list tasks for. If not provided, all tasks across all "
        "agents will be listed."
    )
    list_epilog = format_argparse_epilog(
        """
        Examples:
          task list  # If no filters are provided, list all tasks across all agents regardless of status.
          task list --running --completed  # Filters can be combined; this lists all tasks with status RUNNING and COMPLETED.
          task list 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        parser_list = subparsers.add_parser(
            "list",
            help=self.list_help,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.list_epilog,
        )
        parser_list.add_argument(
            "agent_id",
            help=self.list_agent_id_help,
            type=str,
            nargs="?",
        )
        parser_list.add_argument(
            "-q",
            "--queued",
            help="List only tasks with status QUEUED.",
            action="store_true",
        )
        parser_list.add_argument(
            "-r",
            "--running",
            help="List only tasks with status RUNNING.",
            action="store_true",
        )
        parser_list.add_argument(
            "-c",
            "--completed",
            help="List only tasks with status COMPLETED.",
            action="store_true",
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help="Display information about an agent's task by its ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  task info 123e4567-e89b-12d3-a456-42661417400
                  task info 123e4567-e89b-12d3-a456-42661417400 --limit 20  # Show last 20 task events (tail)
                  task info 123e4567-e89b-12d3-a456-42661417400 --offset 0 --limit 5  # Show first 5 task events
                  task info 123e4567-e89b-12d3-a456-42661417400 --offset -5 --limit 10  # Show 10 task events starting from 5th from end
                  task info 123e4567-e89b-12d3-a456-42661417400 --raw  # Print task events as plain unformatted text (useful for copy-paste)
                  task info 123e4567-e89b-12d3-a456-42661417400 --raw --limit 50  # Print last 50 task events as plain text
                """,
            ),
        )
        parser_info.add_argument(
            "task_id",
            help="ID of the task to display information for.",
            type=str,
        )
        parser_info.add_argument(
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
        parser_info.add_argument(
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
        parser_info.add_argument(
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

        # watch sub-command
        parser_watch = subparsers.add_parser(
            "watch",
            help="Continuously watch a task until it completes.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  task watch 123e4567-e89b-12d3-a456-42661417400
                  task watch 123e4567-e89b-12d3-a456-42661417400 --interval 5
                  task watch 123e4567-e89b-12d3-a456-42661417400 --limit 20  # Show last 20 task events (tail)
                  task watch 123e4567-e89b-12d3-a456-42661417400 --offset 0 --limit 5  # Show first 5 task events
                  task watch 123e4567-e89b-12d3-a456-42661417400 --offset -5 --limit 10  # Show 10 task events starting from 5th from end
                """,
            ),
        )
        parser_watch.add_argument(
            "task_id",
            help="ID of the task to watch.",
            type=str,
        )
        parser_watch.add_argument(
            "--interval",
            "-i",
            help="Polling interval in seconds (defaults to 1 second).",
            type=float,
            default=1.0,
        )
        parser_watch.add_argument(
            "-l",
            "--limit",
            help=(
                "Maximum number of task events to return. "
                "When specified without --offset, returns the last N entries (tail). "
                "Must be a positive integer (defaults to 10 entries)."
            ),
            type=positive_int,
            default=None,
        )
        parser_watch.add_argument(
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

        # delete sub-command
        parser_delete = subparsers.add_parser(
            "delete",
            help="Delete a queued task by its ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  task delete 123e4567-e89b-12d3-a456-42661417400

                Notes:
                  Only tasks that are still QUEUED can be deleted. Once an agent has
                  picked a task up there is nothing left to remove from its queue.
                """,
            ),
        )
        parser_delete.add_argument(
            "task_id",
            help="ID of the queued task to delete.",
            type=str,
        )

    @staticmethod
    async def _compute_agent_commands_to_required_arguments_map(
        agent: dict[str, Any],
    ) -> dict[str, list[str]]:
        return {
            agent_capability["name"]: [
                option_name
                for option_name, option in agent_capability["options"].items()
                if option.get("required", False)
            ]
            for agent_capability in agent["agent_type"]["agent_capabilities"].values()
        }

    @staticmethod
    async def _get_tasks_to_list(
        rest_api: RestAPI,
        agent_id: str,
        display_queued: bool,
        display_running: bool,
        display_completed: bool,
    ) -> list[dict[str, Any]]:
        agent_tasks = []
        if not display_queued and not display_running and not display_completed:
            agent_tasks = await rest_api.get_all_agent_tasks_by_agent_id(
                agent_id=agent_id,
            )
        else:
            if display_queued:
                agent_tasks.extend(
                    await rest_api.get_all_queued_tasks_by_agent_id(
                        agent_id=agent_id,
                    )
                )
            if display_running:
                agent_tasks.extend(
                    await rest_api.get_all_running_agent_tasks_by_agent_id(
                        agent_id=agent_id,
                    )
                )
            if display_completed:
                agent_tasks.extend(
                    await rest_api.get_all_completed_tasks_by_agent_id(
                        agent_id=agent_id,
                    )
                )
        return agent_tasks

    @staticmethod
    def _list_tasks(
        agent_id: str,
        agent_name: str,
        agent_tasks: list[dict[str, Any]],
        commands_to_required_arguments_map: dict[str, list[str]],
    ) -> None:
        table = Table(title=f"Tasks For '{agent_name}' ({agent_id})", highlight=True)
        table.add_column("Task ID")
        table.add_column("Command")
        table.add_column("Required Arguments")
        table.add_column("Status")
        table.add_column("Datetime Started")
        for agent_task in agent_tasks:
            table.add_row(
                agent_task["task_id"],
                str(agent_task["command"]),
                format_dict_as_single_line_key_value_string(
                    input_dict={
                        name: value
                        for name, value in agent_task["arguments"].items()
                        if name
                        in commands_to_required_arguments_map.get(
                            agent_task["command"], []
                        )
                    }
                ),
                format_agent_task_status_string_with_color(
                    status_str=agent_task["status"]["state"],
                ),
                format_datetime_as_human_readable_str(
                    datetime_str=agent_task["datetime_started"]
                ),
            )
        console.print(table, "")

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

    @staticmethod
    async def _fetch_and_build_display(
        rest_api: RestAPI,
        task_id: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[Group, str]:
        task = await rest_api.get_agent_task_by_task_id(
            task_id=task_id,
            limit=limit,
            offset=offset,
        )

        task_info_table, task_events_table = create_task_info_and_task_events_tables(
            task=task
        )
        display = Group(task_info_table, "", task_events_table, "")

        return display, task["status"]["state"]

    @classmethod
    async def _handle_list_sub_command(
        cls,
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        if parsed_args.agent_id is None:
            all_agents = await rest_api.get_all_agents()
            agents_with_no_tasks = []
            for agent in all_agents:
                agent_tasks = await cls._get_tasks_to_list(
                    rest_api=rest_api,
                    agent_id=agent["agent_id"],
                    display_queued=parsed_args.queued,
                    display_running=parsed_args.running,
                    display_completed=parsed_args.completed,
                )
                commands_to_required_arguments_map = (
                    await cls._compute_agent_commands_to_required_arguments_map(
                        agent=agent,
                    )
                )
                if not agent_tasks:
                    agents_with_no_tasks.append(
                        f"'{agent['name']}' ({agent['agent_id']})"
                    )
                else:
                    cls._list_tasks(
                        agent_id=agent["agent_id"],
                        agent_name=agent["name"],
                        agent_tasks=agent_tasks,
                        commands_to_required_arguments_map=commands_to_required_arguments_map,
                    )
            if agents_with_no_tasks:
                print_info(
                    "No tasks found for the following agents with the specified "
                    "filters:\n"
                    + textwrap.indent(
                        format_list_as_multi_line_bulleted_string(
                            input_list=agents_with_no_tasks
                        ),
                        "    ",
                    )
                )
            if not all_agents:
                print_info("No tasks to list. No agents found.")
        else:
            agent = await rest_api.get_agent_by_agent_id(agent_id=parsed_args.agent_id)
            commands_to_required_arguments_map = (
                await cls._compute_agent_commands_to_required_arguments_map(
                    agent=agent,
                )
            )
            agent_tasks = await cls._get_tasks_to_list(
                rest_api=rest_api,
                agent_id=agent["agent_id"],
                display_queued=parsed_args.queued,
                display_running=parsed_args.running,
                display_completed=parsed_args.completed,
            )
            cls._list_tasks(
                agent_id=agent["agent_id"],
                agent_name=agent["name"],
                agent_tasks=agent_tasks,
                commands_to_required_arguments_map=commands_to_required_arguments_map,
            )

        return ContinueSignal()

    @classmethod
    async def _handle_info_sub_command(
        cls,
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        await cls._display_task_info(
            rest_api=context.client_session.rest_api,
            task_id=parsed_args.task_id,
            limit=parsed_args.limit,
            offset=parsed_args.offset,
            raw=parsed_args.raw,
        )

        return ContinueSignal()

    @classmethod
    async def _handle_watch_sub_command(
        cls,
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api
        task_id = parsed_args.task_id
        interval = parsed_args.interval
        limit = parsed_args.limit
        offset = parsed_args.offset

        if limit and limit > 100:
            print_warning(
                f"Displaying {limit} log entries (> 100) may cause "
                f"[bold red]performance issues[/] during live updates for the server and client."
            )
            response = input("Continue anyway? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                print_info("Watch cancelled.")
                return ContinueSignal()
        else:
            # Ensure limit has a default value even if not explicitly set
            limit = limit or 10

        if interval <= 0:
            print_warning("Polling interval must be a positive number. Using 1 second.")
            interval = 1.0
        elif interval < 0.5:
            print_warning(
                "Polling interval's that are too low (< 0.5s) may cause "
                "performance issues."
            )

        try:
            # Initial fetch
            display, status = await cls._fetch_and_build_display(
                rest_api=rest_api,
                task_id=task_id,
                limit=limit,
                offset=offset,
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

                        display, status = await cls._fetch_and_build_display(
                            rest_api=rest_api,
                            task_id=task_id,
                            limit=limit,
                            offset=offset,
                        )
                        live.update(display)
        except KeyboardInterrupt, asyncio.CancelledError:
            print_info("Watch stopped by user.")

        return ContinueSignal()

    @classmethod
    async def _handle_delete_sub_command(
        cls,
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api
        task_id = parsed_args.task_id

        # Fetched first so that a task that does not exist at all is reported as such by
        # the REST API rather than as an agent that could not be found for it.
        task = await rest_api.get_agent_task_by_task_id(task_id=task_id)
        state = task["status"]["state"]
        if state != "QUEUED":
            print_error(
                f"Only tasks that are still QUEUED can be deleted. Task '{task_id}' "
                f"has status {state}.",
            )
            return ContinueSignal()

        await rest_api.delete_queued_agent_task_by_task_id(
            task_id=task_id,
        )
        print_success(f"Deleted queued task '{task_id}'")
        return ContinueSignal()

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            match parsed_args.sub_command:
                case "list":
                    return await self._handle_list_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "info":
                    return await self._handle_info_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "watch":
                    return await self._handle_watch_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "delete":
                    return await self._handle_delete_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case _:
                    raise AssertionError(
                        f"Unknown task sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()
