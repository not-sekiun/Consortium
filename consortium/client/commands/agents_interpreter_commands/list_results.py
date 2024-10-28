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
            nargs=1,
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

    @staticmethod
    async def _list_results_from_agent_id(
        client_rest_api_connection: "ClientRESTAPIConnection",
        display_result_status_success: bool,
        display_result_status_fail: bool,
        agent_id: str,
    ) -> None:
        agent_results = []
        # If no result state is specified, list all results. If any one of the
        # result states is specified, only list those results.
        if not display_result_status_success and not display_result_status_fail:
            agent_results += (
                await client_rest_api_connection.get_all_agent_results_by_agent_id(
                    agent_id=agent_id,
                )
            )
        if display_result_status_success:
            agent_results += await client_rest_api_connection.get_all_successful_agent_results_by_agent_id(
                agent_id=agent_id,
            )
        if display_result_status_fail:
            agent_results += await client_rest_api_connection.get_all_failed_agent_results_by_agent_id(
                agent_id=agent_id,
            )

        agent_tasks = await client_rest_api_connection.get_all_agent_tasks_by_agent_id(
            agent_id=agent_id,
        )
        agent_tasks_dict = {
            agent_task["task_id"]: agent_task for agent_task in agent_tasks
        }

        table = Table(title="Agent Results")
        table.add_column("Result ID")
        table.add_column("Task ID")
        table.add_column("Command")
        table.add_column("Success")
        for agent_result in agent_results:
            table.add_row(
                agent_result["result_id"],
                agent_result["task_id"],
                agent_tasks_dict[agent_result["task_id"]]["command"],
                format_agent_result_state_string_with_color(
                    agent_result_state_string=str(agent_result["success"]),
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
            await self._list_results_from_agent_id(
                client_rest_api_connection=client_rest_api_connection,
                display_result_status_success=parsed_args.success,
                display_result_status_fail=parsed_args.fail,
                agent_id=parsed_args.agent_id[0],
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
