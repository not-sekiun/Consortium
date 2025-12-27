from argparse import ArgumentParser

from consortium.client.models.return_status_models import (
    InterpreterType,
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class AgentInteractCommand(BaseCommand):
    name = "interact"
    description = "Interact with an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          interact 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to interact with.",
            nargs=1,
            default=None,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent = await rest_api.get_agent_by_agent_id(
                parsed_args.agent_id[0],
            )
            print_success(
                f"Interacting with agent '{agent['name']}' ({agent['agent_id']})"
            )
            return ReturnStatus(
                type=ReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.INTERACT_AGENT_INTERPRETER,
                    "agent": agent,
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
