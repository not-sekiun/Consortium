from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    TaskListCommand as TaskListAgentsInterpreterCommand,
)
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import Context
from consortium.client.utils.formatter_utils import format_argparse_epilog


class TaskListCommand(TaskListAgentsInterpreterCommand):
    name = "t-list"
    description = (
        "List all tasks for the current agent, or for a specific agent by its agent ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          t-list  # If no filters are provided, list all tasks for the current agent being interacted with regardless of status.
          t-list --running --completed  # Filters can be combined; this lists all tasks with status RUNNING and COMPLETED.
          t-list 123e4567-e89b-12d3-a456-42661417400
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

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            if parsed_args.agent_id:
                agent = await rest_api.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id,
                )
            else:
                agent = context.environment["agent"]

            await self._list_tasks_from_agent_id(
                rest_api=rest_api,
                agent_id=agent["agent_id"],
                agent_name=agent["name"],
                display_queued=parsed_args.queued,
                display_running=parsed_args.running,
                display_completed=parsed_args.completed,
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
