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
    format_agent_result_status_string_with_color,
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import CONSOLE


class ResultsListCommand(BaseCommand):
    name = "results_list"
    description = (
        "List all agent results or a particular agent's results if its agent ID is "
        "provided."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          results_list 123e4567-e89b-12d3-a456-42661417400  # If the result status is not specified, all results will be listed.
          results_list 123e4567-e89b-12d3-a456-42661417400  -s
          results_list 123e4567-e89b-12d3-a456-42661417400  --failure
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to list results for. If not provided, all "
            "results across all agents will be listed.",
            type=str,
            nargs="?",
        )
        parser.add_argument(
            "-s",
            "--success",
            help="List only results with a status of SUCCESS.",
            action="store_true",
        )
        parser.add_argument(
            "-f",
            "--failure",
            help="List only results with a status of 'FAILURE'.",
            action="store_true",
        )
        parser.add_argument(
            "-e",
            "--error",
            help="List only results with a status of 'ERROR'.",
            action="store_true",
        )

    @staticmethod
    async def _list_results_from_agent_id(
        client_rest_api_connection: ClientRESTAPIConnection,
        agent_id: str,
        agent_name: str,
        display_success: bool,
        display_failure: bool,
        display_error: bool,
    ) -> None:
        agent_results = []
        # If no result status is specified, list all results. If any one of the
        # result states is specified, only list those results.
        if not display_success and not display_failure:
            agent_results += (
                await client_rest_api_connection.get_all_agent_results_by_agent_id(
                    agent_id=agent_id,
                )
            )
        if display_success:
            agent_results += await client_rest_api_connection.get_all_successful_agent_results_by_agent_id(
                agent_id=agent_id,
            )
        if display_failure:
            agent_results += await client_rest_api_connection.get_all_failed_agent_results_by_agent_id(
                agent_id=agent_id,
            )
        if display_error:
            agent_results += await client_rest_api_connection.get_all_errored_agent_results_by_agent_id(
                agent_id=agent_id,
            )

        table = Table(title=f"Results For '{agent_name}' ({agent_id})", highlight=True)
        table.add_column("Result ID")
        table.add_column("Task ID")
        table.add_column("Command")
        table.add_column("Status")
        table.add_column("Datetime Finished")
        table.add_column("Elapsed Time")
        for agent_result in agent_results:
            table.add_row(
                abbreviate_string(string=agent_result["result_id"]),
                abbreviate_string(string=agent_result["task_id"]),
                agent_result["command"],
                format_agent_result_status_string_with_color(
                    status_str=str(agent_result["status"]),
                ),
                str(agent_result["datetime_finished"]),
                f"{agent_result['elapsed_seconds']:.2f}s",
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
                    await self._list_results_from_agent_id(
                        client_rest_api_connection=client_rest_api_connection,
                        agent_id=agent["agent_id"],
                        agent_name=agent["name"],
                        display_success=parsed_args.success,
                        display_failure=parsed_args.failure,
                        display_error=parsed_args.error,
                    )
            else:
                agent = await client_rest_api_connection.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id,
                )
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
