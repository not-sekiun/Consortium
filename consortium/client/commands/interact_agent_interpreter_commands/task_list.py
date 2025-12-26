from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    TaskListCommand as TaskListAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class TaskListCommand(TaskListAgentsInterpreterCommand):
    name = "t-ls"
    description = (
        "List all tasks for the current agent, or for a specific agent by its agent ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          t-ls  # If no filters are provided, list all tasks for the current agent being interacted with regardless of status.
          t-ls --running --completed  # Filters can be combined; this lists all tasks with status RUNNING and COMPLETED.
          t-ls 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent to list tasks for (defaults to the current agent if "
                "not provided)."
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

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]

            if parsed_args.agent_id:
                agent = await client_rest_api_connection.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id,
                )
            else:
                agent = command_context.environment["agent"]

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
