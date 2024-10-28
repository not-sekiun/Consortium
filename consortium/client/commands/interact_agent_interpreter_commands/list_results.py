from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    ListResultsCommand as ListResultsAgentsInterpreterCommand,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import CommandContext, ReturnStatus
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ListResultsCommand(ListResultsAgentsInterpreterCommand):
    name = "list_results"
    description = (
        "List an agents results along with their essential information for a "
        "specified agent or for the currently selected agent being interacted with."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_results  # List all results for the currently selected agent being interacted with.
          list_results -s
          list_results --fail
          list_results 123e4567-e89b-12d3-a456-42661417400  # List all results for a specific agent.
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "The agent ID of the agent to list tasks for. If not provided, the "
                "agent ID of the currently selected agent being interacted with will "
                "be used."
            ),
            type=str,
            nargs="?",
        )
        parser.add_argument(
            "-s",
            "--success",
            help="List only results that have a state of SUCCESS.",
            action="store_true",
        )
        parser.add_argument(
            "-f",
            "--fail",
            help="List only results that have a state of FAIL.",
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
            await self._list_results_from_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                display_result_status_success=parsed_args.success,
                display_result_status_fail=parsed_args.fail,
                agent_id=parsed_args.agent_id
                if parsed_args.agent_id
                else command_context.environment["agent"]["agent_id"],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
