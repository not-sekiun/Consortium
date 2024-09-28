from argparse import ArgumentParser

from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import (
    format_agent_result_state_string_with_color,
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import CONSOLE


class ListResultsCommand(BaseCommand):
    name = "list_results"
    description = (
        "List an agents results along with their essential information for a "
        "specified agent."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_results 123e4567-e89b-12d3-a456-42661417400  # If the result state is not specified, all results will be listed.
          list_results 123e4567-e89b-12d3-a456-42661417400  -s
          list_results 123e4567-e89b-12d3-a456-42661417400  --fail
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to list tasks for.",
            type=str,
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
            client_connection = command_context.environment["client_connection"]

            if parsed_args.success:
                agent_results = await client_connection.get_all_successful_agent_results_by_agent_id(
                    agent_id=parsed_args.agent_id,
                )
            elif parsed_args.fail:
                agent_results = (
                    await client_connection.get_all_failed_agent_results_by_agent_id(
                        agent_id=parsed_args.agent_id,
                    )
                )
            else:
                agent_results = (
                    await client_connection.get_all_agent_results_by_agent_id(
                        agent_id=parsed_args.agent_id,
                    )
                )

            # TODO: Add more columns to the table.
            table = Table(title="Agent Results")
            table.add_column("Task ID")
            table.add_column("Result ID")
            table.add_column("Status")
            for agent_result in agent_results:
                table.add_row(
                    agent_result["task_id"],
                    agent_result["result_id"],
                    format_agent_result_state_string_with_color(
                        agent_result_state_string=agent_result["success"],
                    ),
                )
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
