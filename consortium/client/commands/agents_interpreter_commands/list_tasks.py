from argparse import ArgumentParser

from rich.table import Table

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import (
    format_agent_task_state_string_with_color,
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import CONSOLE


class ListTasksCommand(BaseCommand):
    name = "list_tasks"
    description = (
        "List an agents tasks along with their essential information for a "
        "specified agent."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_tasks 123e4567-e89b-12d3-a456-42661417400  # If the task state is not specified, all tasks will be listed.
          list_tasks 123e4567-e89b-12d3-a456-42661417400  -q
          list_tasks 123e4567-e89b-12d3-a456-42661417400  --running
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to list tasks for.",
            type=str,
            nargs=1,
        )
        parser.add_argument(
            "-q",
            "--queued",
            help="List only tasks that have a state of QUEUED.",
            action="store_true",
        )
        parser.add_argument(
            "-r",
            "--running",
            help="List only tasks that have a state of RUNNING.",
            action="store_true",
        )
        parser.add_argument(
            "-c",
            "--completed",
            help="List only tasks that have a state of COMPLETED.",
            action="store_true",
        )

    @staticmethod
    async def _list_tasks_from_agent_id(
        client_rest_api_connection: "ClientRESTAPIConnection",
        display_task_status_queued: bool,
        display_task_status_running: bool,
        display_task_status_completed: bool,
        agent_id: str,
    ) -> None:
        agent_tasks = []
        if (
            not display_task_status_queued
            and not display_task_status_running
            and not display_task_status_completed
        ):
            agent_tasks += (
                await client_rest_api_connection.get_all_agent_tasks_by_agent_id(
                    agent_id=agent_id,
                )
            )
        if display_task_status_queued:
            agent_tasks += (
                await client_rest_api_connection.get_all_queued_agent_tasks_by_agent_id(
                    agent_id=agent_id,
                )
            )
        if display_task_status_running:
            agent_tasks += await client_rest_api_connection.get_all_running_agent_tasks_by_agent_id(
                agent_id=agent_id,
            )
        if display_task_status_completed:
            agent_tasks += await client_rest_api_connection.get_all_completed_agent_tasks_by_agent_id(
                agent_id=agent_id,
            )

        table = Table(title="Agent Tasks")
        table.add_column("Task ID")
        table.add_column("Command")
        table.add_column("Arguments")
        table.add_column("Status")
        for agent_task in agent_tasks:
            table.add_row(
                agent_task["task_id"],
                agent_task["command"],
                ", ".join(
                    [
                        f"{key}={value!r}"
                        for key, value in agent_task["arguments"].items()
                    ],
                ),
                format_agent_task_state_string_with_color(
                    state_str=agent_task["state"],
                ),
            )
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
            await self._list_tasks_from_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                display_task_status_queued=parsed_args.queued,
                display_task_status_running=parsed_args.running,
                display_task_status_completed=parsed_args.completed,
                agent_id=parsed_args.agent_id[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
