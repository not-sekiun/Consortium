from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    ListTasksCommand as ListTasksAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ListTasksCommand(ListTasksAgentsInterpreterCommand):
    name = "list_tasks"
    description = (
        "List an agents tasks along with their essential information for a "
        "specified agent or for the currently selected agent being interacted with."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_tasks  # List all tasks for the currently selected agent being interacted with.
          list_tasks -q
          list_tasks --running
          list_tasks 123e4567-e89b-12d3-a456-42661417400  # List all tasks for a specific agent.
        """,
    )
    group = "Task and Result Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "The agent ID of the agent to list tasks for. If not provided, the "
                "agent ID of the currently selected agent being interacted with will be "
                "used."
            ),
            type=str,
            nargs="?",
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
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id
                else command_context.environment["agent"]["agent_id"],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
