from argparse import ArgumentParser

from prompt_toolkit import HTML, PromptSession

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success, print_warning


class AgentDeleteCommand(BaseConnectedCommand):
    name = "delete"
    description = "Delete an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          delete 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to delete.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # If the agent does not exist, a RestAPIError is raised and caught by the
            # outer try-except block.
            agent = await rest_api.get_agent_by_agent_id(parsed_args.agent_id[0])

            # Deleting an active agent removes an agent that is still checking in, so
            # warn the operator and require an explicit confirmation before proceeding.
            if agent["status"] == "ACTIVE":
                print_warning(
                    f"Agent '{agent['name']}' ({agent['agent_id']}) is currently "
                    "ACTIVE.",
                )
                confirmation = await PromptSession().prompt_async(
                    HTML(
                        "Are you sure you want to delete this agent? It is still "
                        "checking in and deleting it will make it "
                        "<b><ansired>unmanageable</ansired></b> until it "
                        "re-registers (y/N): ",
                    )
                )
                if confirmation.lower() != "y":
                    return ContinueSignal()

            await rest_api.delete_agent_by_agent_id(
                agent_id=parsed_args.agent_id[0],
            )
            print_success(
                f"Deleted agent: '{agent['name']}' ({agent['agent_id']})",
            )
        except SystemExit:
            pass

        return ContinueSignal()
