import argparse
from typing import Union

import consortium_old.utils.standard_io.print_status as print_status
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.interpreter_exit_signal import (
    InterpreterExitSignal,
)
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class ListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="use a specific listener",
            prog="use_listener",
        )
        parser.add_argument(
            "listener_template_id",
            type=int,
            help="the listener template id of the associated listener to use",
            nargs=1,
        )
        super().__init__(parser)

    async def run_command(
        self,
        remote_server: ClientREST,
        _client: "Client",
        _client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        interpreter: Union["ListenersInterpreter", "UseListenerInterpreter"],
    ) -> Union[None, InterpreterExitSignal]:
        try:
            parsed_args = self._parser.parse_args(
                parsed_consortium_command.command_args,
            )

            # TODO: fix this really shitty method of checking for types without circular import 🤡🤡🤡
            # checking if we are running in the context of a UseListenerInterpreter since that interpreter can also use this command to swap between listener templates without going back to the listener interpreter
            if "UseListenerInterpreter" in str(type(interpreter)):
                # listener_template_id is guaranteed to be in here
                if interpreter.listener_template_id == parsed_args.listener_template_id:
                    print_status.print_error("Already using that listener")
                    return
                # if we bypass this codeblock we can emit an InterpreterExitSignal to swap differnet UseListenerInterpreters

            response = await remote_server.get_listener_template_by_id(
                parsed_args.listener_template_id[0],
            )
            print_status.print_info(
                f"Using listener: {parsed_args.listener_template_id}...",
            )
            return InterpreterExitSignal(
                switch_interpreter=True,
                new_interpreter_str="uselistener",
                new_listener_template_id=parsed_args.listener_template_id,
            )
        except SystemExit:
            pass
        except Exception:
            print_status.print_error(
                f"Invalid listener: {parsed_args.listener_template_id}",
            )
