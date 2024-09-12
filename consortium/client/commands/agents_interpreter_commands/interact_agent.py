from argparse import ArgumentParser

import consortium.client.client_singletons as client_singletons
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_success

client_connections_service = client_singletons.client_connections_service


class InteractAgentCommand(BaseCommand):
    name = "interact_agent"
    description = "Choose a specific agent to interact with."
    epilog = format_argparse_epilog(
        """
        Examples:
          interact_agent 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to interact with.",
            nargs=1,
            default=None,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]
            try:
                agent = await client_connection.get_agent_by_agent_id(
                    parsed_args.agent_id[0],
                )
            except ValueError as exc:
                print_error(str(exc))
                return ReturnStatus(type=ClientReturnStatusType.CONTINUE)

            print_success(
                f"Interacting with agent {agent["name"]} ({agent["agent_id"]}).",
            )

            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.INTERACT_AGENT_INTERPRETER,
                    "agent": agent,
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
