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
    abbreviate_string,
    format_agent_task_status_string_with_color,
    format_argparse_epilog,
    format_dict_as_single_line_key_value_string,
)
from consortium.client.utils.printer_utils import CONSOLE


class TasksListCommand(BaseCommand):
    name = "tasks_list"
    description = (
        "List all agent tasks or a particular agent's tasks if its agent ID is "
        "provided."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          tasks_list  # If the agent ID is not specified, all tasks will be listed.
          tasks_list 123e4567-e89b-12d3-a456-42661417400  -q  # List only tasks with a status of  'QUEUED' for a specific agent.
          tasks_list --running --completed  # List only tasks with a status of 'RUNNING' and 'COMPLETED' across all agents.
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "The agent ID of the agent to list tasks for. If not provided, all "
                "tasks across all agents will be listed."
            ),
            type=str,
            nargs="?",
        )
        parser.add_argument(
            "-q",
            "--queued",
            help="List only tasks with a status of 'QUEUED'.",
            action="store_true",
        )
        parser.add_argument(
            "-r",
            "--running",
            help="List only tasks with a status of 'RUNNING'",
            action="store_true",
        )
        parser.add_argument(
            "-c",
            "--completed",
            help="List only tasks with a status of 'COMPLETED'",
            action="store_true",
        )

    @staticmethod
    async def _list_tasks_from_agent_id(
        client_rest_api_connection: ClientRESTAPIConnection,
        agent_id: str,
        agent_name: str,
        display_queued: bool,
        display_running: bool,
        display_completed: bool,
    ) -> None:
        agent_tasks = []
        if not display_queued and not display_running and not display_completed:
            agent_tasks += (
                await client_rest_api_connection.get_all_agent_tasks_by_agent_id(
                    agent_id=agent_id,
                )
            )
        if display_queued:
            agent_tasks += (
                await client_rest_api_connection.get_all_queued_tasks_by_agent_id(
                    agent_id=agent_id,
                )
            )
        if display_running:
            agent_tasks += await client_rest_api_connection.get_all_running_agent_tasks_by_agent_id(
                agent_id=agent_id,
            )
        if display_completed:
            agent_tasks += (
                await client_rest_api_connection.get_all_completed_tasks_by_agent_id(
                    agent_id=agent_id,
                )
            )

        table = Table(title=f"Tasks For '{agent_name}' ({agent_id})", highlight=True)
        table.add_column("Task ID")
        table.add_column("Command")
        table.add_column("Arguments")
        table.add_column("Status")
        table.add_column("Datetime Started")
        for agent_task in agent_tasks:
            table.add_row(
                abbreviate_string(string=agent_task["task_id"]),
                str(agent_task["command"]),
                format_dict_as_single_line_key_value_string(
                    input_dict=agent_task["arguments"],
                ),
                format_agent_task_status_string_with_color(
                    status_str=agent_task["status"],
                ),
                str(agent_task["datetime_started"]),
            )
        CONSOLE.print(table, "")

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            if parsed_args.agent_id is None:
                all_agents = await client_rest_api_connection.get_all_agents()
                for agent in all_agents:
                    await self._list_tasks_from_agent_id(
                        client_rest_api_connection=client_rest_api_connection,
                        agent_id=agent["agent_id"],
                        agent_name=agent["name"],
                        display_queued=parsed_args.queued,
                        display_running=parsed_args.running,
                        display_completed=parsed_args.completed,
                    )
            else:
                agent = await client_rest_api_connection.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id
                )
                await self._list_tasks_from_agent_id(
                    client_rest_api_connection=client_rest_api_connection,
                    agent_id=agent["agent_id"],
                    agent_name=agent["name"],
                    display_queued=parsed_args.queued,
                    display_running=parsed_args.running,
                    display_completed=parsed_args.completed,
                )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
