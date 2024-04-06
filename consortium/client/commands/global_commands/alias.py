import argparse
import json
from typing import Type

from rich.console import Console
from rich.table import Table

from consortium.client.client_config import CONSORTIUM_COMMAND_ALIASES_JSON_FILE_PATH
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import (
    print_error,
    print_plain,
    print_success,
)


class AliasCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Create, delete, edit and view command aliases.",
            prog="alias",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    alias -s  # Display all current aliases.
                    alias -r !  # Remove the alias "!".
                    alias c=clear e=exit  # Create an alias "c" for the command "clear" and "e" for the command "exit".
                """,
            ),
        )
        parser.add_argument(
            "alias_to_command_mappings",
            nargs="*",
            help="alias of the command",
        )
        parser.add_argument(
            "-s",
            "--show",
            action="store_true",
            help="show all current aliases",
        )
        parser.add_argument("-r", "--remove", help="remove an alias", nargs="+")
        parser.add_argument(
            "-c",
            "--clear",
            help="clear all aliases",
            action="store_true",
        )
        parser.add_argument(
            "-R",
            "--reset",
            help="reset command aliases to their default settings",
            action="store_true",
        )
        super().__init__(parser)

    @staticmethod
    def _print_alias_table(interpreter: BaseInterpreter) -> None:
        table = Table(title="Command Aliases")
        table.add_column("Alias")
        table.add_column("Command")

        alias_entries = [
            [alias, command] for alias, command in interpreter.command_aliases.items()
        ]
        for alias, command in alias_entries:
            table.add_row(alias, command)

        Console().print(table)

    @staticmethod
    def _remove_alias(interpreter: BaseInterpreter, aliases: list[str]) -> None:
        for alias_to_remove in aliases:
            if alias_to_remove in interpreter.command_aliases:
                print_success(
                    f"Removed alias: {alias_to_remove}={interpreter.command_aliases[alias_to_remove]}",
                )
                del interpreter.command_aliases[alias_to_remove]
            else:
                print_error(f'Alias "{alias_to_remove}" does not exist, cannot remove.')

    @staticmethod
    def _reset_aliases(interpreter: BaseInterpreter) -> None:
        interpreter.command_aliases = {"!": "local -c", "?": "help"}
        print_success("Reset command aliases to the default settings.")

    @staticmethod
    def _clear_aliases(interpreter: BaseInterpreter) -> None:
        interpreter.command_aliases = {}
        print_success("Cleared all command aliases.")

    # An alias to command mapping can take any of the following forms of alias=command,
    # alias="command with spaces", or
    # alias="command with spaces and \"escaped\" quotes". Each individual argparse
    # argument in the parsed_args object is  treated as an alias to command mapping
    @staticmethod
    def _add_alias(
        interpreter: BaseInterpreter,
        alias_to_command_mappings: list[str],
    ) -> None:
        for alias_to_command_mapping in alias_to_command_mappings:
            alias, command = alias_to_command_mapping.split("=", 1)

            if not alias or not command:
                print_error(
                    f"Alias or command cannot be empty. Skipping: {alias_to_command_mapping}",
                )
                continue

            if (
                alias in interpreter.command_aliases
                and interpreter.command_aliases[alias] == command
            ):
                print_error(f"Alias {alias_to_command_mapping} already exists.")
            elif (
                alias in interpreter.command_aliases
                and interpreter.command_aliases[alias] != command
            ):
                print_success(
                    f'Remapped alias "{alias}": {alias_to_command_mapping}',
                )
                interpreter.command_aliases[alias] = command
            elif (
                alias not in interpreter.command_aliases
                and command not in interpreter.command_aliases.values()
            ):
                print_success(
                    f"Added new alias: {alias_to_command_mapping}",
                )
                interpreter.command_aliases[alias] = command
            else:
                print_error(
                    f"Alias {alias_to_command_mapping} already exists.",
                )

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> ContinueReturnStatus:
        try:
            parsed_args = self._parser.parse_args(
                interpreter_command.arguments,
            )

            if parsed_args.show:
                self._print_alias_table(interpreter)
            elif parsed_args.remove:
                self._remove_alias(interpreter, parsed_args.remove)
            elif parsed_args.alias_to_command_mappings:
                self._add_alias(interpreter, parsed_args.alias_to_command_mappings)
            elif parsed_args.reset:
                self._reset_aliases(interpreter)
            elif parsed_args.clear:
                self._clear_aliases(interpreter)
            # "*" nargs for alias_to_command_mappings is to allow for the absence of
            # such mapping for other functionality to be possible. As such if the
            # alias to command mappings are not present, then the help menu will be
            # displayed manually.
            else:
                print_plain(self.summary)

            # Save the command aliases to disk.
            with open(CONSORTIUM_COMMAND_ALIASES_JSON_FILE_PATH, "w") as file:
                json.dump(
                    obj=interpreter.command_aliases,
                    fp=file,
                    indent=4,
                )
        except SystemExit:
            pass

        return ContinueReturnStatus()
