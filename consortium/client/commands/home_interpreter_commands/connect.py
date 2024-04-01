import argparse
import json
from typing import Union

import consortium_old.utils.standard_io.print_status as print_status
import jsonschema
from consortium_old.core.client.client_database import ClientDatabase
from consortium_old.core.client.client_rest import ClientREST
from consortium_old.core.client.interpreters.disconnected_interpreter import (  # TODO: Truthfully I do not know why this import is not circular. Investigate later on and see if I can change the type hinting to not use string literals
    DisconnectedInterpreter,
)
from consortium_old.core.client.objects.interpreter_exit_signal import (
    InterpreterExitSignal,
)
from consortium_old.core.client.objects.parsed_consortium_command import (
    ParsedConsortiumCommand,
)

from consortium.client.commands.base_command import BaseCommand


class HomeCommand(BaseCommand):
    def __init__(self):
        # TODO: Add the ability to specify the value of specific keys from the config.json file through argument parameters
        parser = argparse.ArgumentParser(
            description="connect to a server",
            prog="connect",
        )
        parser.add_argument(
            "-c",
            "--config",
            help="config filepath to load server config data from. by default data is loaded from local/server/config.json",
            default="local/client/config.json",
        )
        super().__init__(parser)

    async def run_command(
        self,
        _remote_server: ClientREST,
        client: "Client",
        client_database: ClientDatabase,
        parsed_consortium_command: ParsedConsortiumCommand,
        interpreter: Union[
            "HomeInterpreter",
            "DisconnectedInterpreter",
            "ListenersInterpreter",
            "GeneratorInterpreter",
            "AgentsInterpreter",
        ],  # TODO: Gradually fill this out with more interpreters
    ) -> Union[None, InterpreterExitSignal]:
        try:
            parsed_args = self._parser.parse_args(
                parsed_consortium_command.command_args,
            )
            client_config_json_schema = {
                "type": "object",
                "properties": {
                    "remote_host": {"type": "string"},
                    "remote_port": {"type": "number"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["remote_host", "remote_port", "username", "password"],
            }
            try:
                with open(parsed_args.config, "r") as f:
                    config_data = json.loads(f.read())
                jsonschema.validate(config_data, client_config_json_schema)
            except FileNotFoundError as e:
                print(f"The config filepath supplied does not exist: {e}")
                return
            except PermissionError as e:
                print(f"Insufficient permissions to read the config file: {e}")
                return
            except json.decoder.JSONDecodeError:
                print("The config file does not contain valid JSON data")
                return
            except jsonschema.ValidationError as e:
                print(
                    f"The config file's JSON data is not of a valid server config format: {e}",
                )
                return

            success, new_remote_server = await client.connect_to_server(
                config_data["remote_host"],
                config_data["remote_port"],
                config_data["username"],
                config_data["password"],
            )
            if success:
                client_database.register_remote_server(new_remote_server)
                print_status.print_success(
                    f'Authenticated as user {config_data["username"]} to {config_data["remote_host"]}:{config_data["remote_port"]}',
                )
                if isinstance(
                    interpreter,
                    DisconnectedInterpreter,
                ):  # if we ran this command in the disconnected interpreter we automatically switch to the home interpreter
                    print_status.print_info(
                        "Valid server connection acquired, automatically switching back to home interpreter...",
                    )
                    return InterpreterExitSignal(
                        exit_client=False,
                        switch_interpreter=True,
                        new_interpreter_str="home",
                        switch_server=True,
                        new_server_id=new_remote_server.server_id,
                    )
            else:
                print_status.print_error("Connection failed")
        except SystemExit:
            pass
