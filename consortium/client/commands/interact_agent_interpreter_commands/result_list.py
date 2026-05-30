from argparse import ArgumentParser

from consortium.client.commands.agents_interpreter_commands import (
    ResultListCommand as ResultListAgentsInterpreterCommand,
)
from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class ResultListCommand(ResultListAgentsInterpreterCommand):
    name = "r-list"
    description = (
        "List all results for the current agent, or for a specific agent by its ID"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          r-list  # If no filters are provided, list all results regardless of status.
          r-list --failure --error  # Filters can be combined; this lists all results with status FAILURE and ERROR.
          r-list 123e4567-e89b-12d3-a456-42661417400
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

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            if parsed_args.agent_id:
                agent = await rest_api.get_agent_by_agent_id(
                    agent_id=parsed_args.agent_id,
                )
            else:
                agent = context.interpreter_context.agent

            agent_results = await self._get_results_to_list(
                rest_api=rest_api,
                agent_id=agent["agent_id"],
                display_success=parsed_args.success,
                display_failure=parsed_args.failure,
                display_error=parsed_args.error,
            )
            self._list_results(
                agent_id=agent["agent_id"],
                agent_name=agent["name"],
                agent_results=agent_results,
            )
        except SystemExit:
            pass

        return ContinueSignal()
