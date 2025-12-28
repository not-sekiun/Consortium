from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import (
    format_agent_result_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class ResultListCommand(BaseCommand):
    name = "r-list"
    description = "List all results, or a specific agent's results by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          r-list  # If no filters are provided, list all results across all agent regardless of status.
          r-list --failure --error  # Filters can be combined; this lists all results with status FAILURE and ERROR.
          r-list 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Tasks and Results Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "ID of the agent to list results for. If not provided, all results "
                "across all agents will be listed."
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

    @staticmethod
    async def _list_results(
        rest_api: RestAPI,
        agent_id: str,
        agent_name: str,
        display_success: bool,
        display_failure: bool,
        display_error: bool,
    ) -> None:
        agent_results = []
        # If no result status is specified, list all results. If any one of the
        # result states is specified, only list those results.
        if not display_success and not display_failure and not display_error:
            agent_results = await rest_api.get_all_agent_results_by_agent_id(
                agent_id=agent_id,
            )
        else:
            if display_success:
                agent_results.extend(
                    await rest_api.get_all_successful_agent_results_by_agent_id(
                        agent_id=agent_id,
                    )
                )
            if display_failure:
                agent_results.extend(
                    await rest_api.get_all_failed_agent_results_by_agent_id(
                        agent_id=agent_id,
                    )
                )
            if display_error:
                agent_results.extend(
                    await rest_api.get_all_errored_agent_results_by_agent_id(
                        agent_id=agent_id,
                    )
                )

        table = Table(title=f"Results For '{agent_name}' ({agent_id})", highlight=True)
        table.add_column("Result ID")
        table.add_column("Task ID", style="bold yellow", highlight=False, max_width=9)
        table.add_column("Command")
        table.add_column("Status")
        table.add_column("Datetime Finished")
        table.add_column("Elapsed Time")
        for agent_result in agent_results:
            table.add_row(
                agent_result["result_id"],
                agent_result["task_id"],
                agent_result["command"],
                format_agent_result_status_string_with_color(
                    status_str=str(agent_result["status"]),
                ),
                format_datetime_as_human_readable_str(
                    datetime_str=agent_result["datetime_finished"]
                ),
                f"{agent_result['elapsed_seconds']:.2f}s",
            )
        console.print(table, "")

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            if parsed_args.agent_id is None:
                all_agents = await rest_api.get_all_agents()
                for agent in all_agents:
                    await self._list_results(
                        rest_api=rest_api,
                        agent_id=agent["agent_id"],
                        agent_name=agent["name"],
                        display_success=parsed_args.success,
                        display_failure=parsed_args.failure,
                        display_error=parsed_args.error,
                    )
            else:
                agent = await rest_api.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id,
                )
                await self._list_results(
                    rest_api=rest_api,
                    agent_id=agent["agent_id"],
                    agent_name=agent["name"],
                    display_success=parsed_args.success,
                    display_failure=parsed_args.failure,
                    display_error=parsed_args.error,
                )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
