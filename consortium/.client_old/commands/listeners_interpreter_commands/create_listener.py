import argparse

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
    SwitchToCreateListenerInterpreterReturnStatus,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter

client_sessions_service = client_singletons.client_sessions_service


class CreateListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Create a listener.",
            prog="create_listener",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Example:
                    create_listener 123e4567-e89b-12d3-a456-42661417400  # Create a listener using the listener template with listener template ID 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser.add_argument(
            "listener_template_id",
            help="Listener template ID of the listener to create.",
            nargs=1,
        )
        super().__init__(parser)

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus | SwitchToCreateListenerInterpreterReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )

            listener_template = (
                await client_session.get_listener_template_by_listener_template_id(
                    parsed_args.listener_template_id[0],
                )
            )
            return SwitchToCreateListenerInterpreterReturnStatus(
                listener_template_id=listener_template["listener_template_id"],
            )
        except SystemExit:
            pass

        return ContinueReturnStatus()
