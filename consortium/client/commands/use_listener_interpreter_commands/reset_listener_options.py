import argparse

import consortium_old.utils.standard_io.print_status as print_status
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class UseListenerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="reset a specific listener's options or reset all options to their server default",
            prog="reset_listener_options",
        )
        parser.add_argument(
            "option_name",
            help="the name of the option to reset. if no option name is provided all options are reset",
            nargs="?",
            default=None,
        )
        super().__init__(parser)

    async def run_command(
        self,
        remote_server: ClientREST,
        _client: "Client",
        _client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        interpreter: "UseListenerInterpreter",
    ) -> None:
        try:
            parsed_args = self._parser.parse_args()
            response = await remote_server.get_listener_template_options(
                interpreter.listener_template_id,
            )
            print(response)
            if parsed_args.option_name:
                if parsed_args.option_name in response:
                    pass
                else:
                    print_status.print_error(
                        f"Invalid option name: {parsed_args.option_name}",
                    )
            else:
                print_status.print_success(f"Reset all options")
                interpreter.listener_template_options = response[
                    "listener_template_options"
                ]
        except SystemExit:
            pass
