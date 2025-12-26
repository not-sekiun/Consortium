from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    ResultListCommand as ResultListAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ResultListCommand(ResultListAgentsInterpreterCommand):
    name = "r-ls"
    description = (
        "List all results for the current agent, or for a specific agent by its agent "
        "ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          r-ls  # If no filters are provided, list all results regardless of status.
          r-ls --failure --error  # Filters can be combined; this lists all results with status FAILURE and ERROR.
          r-ls 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent to list results for (defaults to the current agent "
                "if not provided)."
            ),
            type=str,
            nargs="?",
        )
        parser.add_argument(
            "-s",
            "--success",
            help="List only results with status SUCCESS.",
            action="store_true",
        )
        parser.add_argument(
            "-f",
            "--failure",
            help="List only results with status FAILURE.",
            action="store_true",
        )
        parser.add_argument(
            "-e",
            "--error",
            help="List only results with status ERROR.",
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

            await self._list_results_from_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                agent_id=agent["agent_id"],
                agent_name=agent["name"],
                display_success=parsed_args.success,
                display_failure=parsed_args.failure,
                display_error=parsed_args.error,
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
