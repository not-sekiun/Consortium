import textwrap
from argparse import ArgumentParser
from typing import Any

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
    format_dict_as_single_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
)
from consortium.client.utils.printer_utils import console, print_info


class TaskListCommand(BaseCommand):
    name = "t-list"
    description = "List all tasks, or a specific agent's tasks by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          t-list  # If no filters are provided, list all tasks across all agents regardless of status.
          t-list --running --completed  # Filters can be combined; this lists all tasks with status RUNNING and COMPLETED.
          t-list 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent to list tasks for. If not provided, all tasks across "
                "all agents will be listed."
            ),
            type=str,
            nargs="?",
        )
        parser.add_argument(
            "-q",
            "--queued",
            help="List only tasks with status QUEUED.",
            action="store_true",
        )
        parser.add_argument(
            "-r",
            "--running",
            help="List only tasks with status RUNNING.",
            action="store_true",
        )
        parser.add_argument(
            "-c",
            "--completed",
            help="List only tasks with status COMPLETED.",
            action="store_true",
        )

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
    ) -> None:
        table = Table(title=f"Tasks For '{agent_name}' ({agent_id})", highlight=True)
        table.add_column("Task ID")
        table.add_column("Command")
        table.add_column("Arguments")
        table.add_column("Status")
        table.add_column("Datetime Started")
        for agent_task in agent_tasks:
            table.add_row(
                agent_task["task_id"],
                str(agent_task["command"]),
                format_dict_as_single_line_key_value_string(
                    input_dict=agent_task["arguments"],
                ),
                format_agent_task_status_string_with_color(
                    status_str=agent_task["status"],
                ),
                format_datetime_as_human_readable_str(
                    datetime_str=agent_task["datetime_started"]
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

            if parsed_args.agent_id is None:
                all_agents = await rest_api.get_all_agents()
                agents_with_no_tasks = []
                for agent in all_agents:
                    agent_tasks = await self._get_tasks_to_list(
                        rest_api=rest_api,
                        agent_id=agent["agent_id"],
                        display_queued=parsed_args.queued,
                        display_running=parsed_args.running,
                        display_completed=parsed_args.completed,
                    )
                    if not agent_tasks:
                        agents_with_no_tasks.append(
                            f"'{agent['name']}' ({agent['agent_id']})"
                        )
                    else:
                        self._list_tasks(
                            agent_id=agent["agent_id"],
                            agent_name=agent["name"],
                            agent_tasks=agent_tasks,
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
                agent = await rest_api.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id
                )
                agent_tasks = await self._get_tasks_to_list(
                    rest_api=rest_api,
                    agent_id=agent["agent_id"],
                    display_queued=parsed_args.queued,
                    display_running=parsed_args.running,
                    display_completed=parsed_args.completed,
                )
                self._list_tasks(
                    agent_id=agent["agent_id"],
                    agent_name=agent["name"],
                    agent_tasks=agent_tasks,
                )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
