import argparse

from pydantic import TypeAdapter
from rich.table import Table

import consortium.client.client_config as client_config
from consortium.client.models.alias_model import Alias
from consortium.client.models.context_models import AnyContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import (
    console,
    print_error,
    print_info,
    print_success,
)


class AliasCommand(BaseCommand[AnyContext]):
    name = "alias"
    description = "Manage command aliases"
    epilog = format_argparse_epilog(
        """
        Examples:
          alias list
          alias set my_alias "command arg1 arg2"
          alias set -g my_alias "command arg1 arg2"  # set a global alias
          alias unset my_alias

        Notes:
          Standard aliases (without -g) only expand at the first token and will not
          expand anywhere else. This is the default behavior.

          A global alias will expand as a token anywhere.
        """,
    )

    @staticmethod
    def _write_aliases_to_alias_file(aliases: dict[str, Alias]) -> None:
        with open(client_config.CONSORTIUM_ALIASES_JSON_FILE_PATH, "w") as file:
            ta = TypeAdapter(dict[str, Alias])
            file.write(ta.dump_json(aliases, indent=4).decode("utf-8"))

    @staticmethod
    def _handle_list_sub_command(aliases: dict[str, Alias]) -> InterpreterSignal:
        table = Table()
        table.add_column("Alias")
        table.add_column("Command")
        table.add_column("Global")

        for alias_name, alias in aliases.items():
            table.add_row(alias_name, alias.command, str(alias.is_global))

        console.print(table)

        return ContinueSignal()

    def _handle_set_sub_command(
        self, parsed_args, aliases: dict[str, Alias]
    ) -> InterpreterSignal:
        alias = parsed_args.alias[0]
        command = parsed_args.command[0]
        is_global = parsed_args.is_global

        if alias in aliases:
            response = (
                input(f"Alias '{alias}' already exists. Overwrite? [y/N]: ")
                .strip()
                .lower()
            )
            if response != "y":
                print_info(f"Did not overwrite alias '{alias}'")
                return ContinueSignal()

        aliases[alias] = Alias(command=command, is_global=is_global)
        self._write_aliases_to_alias_file(aliases)
        print_success(
            f"Added alias '{alias}' to command '{command}' (global={is_global})"
        )
        return ContinueSignal()

    def _handle_unset_sub_command(
        self, parsed_args, aliases: dict[str, Alias]
    ) -> InterpreterSignal:
        alias = parsed_args.alias[0]

        if alias not in aliases:
            print_error(f"Alias '{alias}' not found")
            return ContinueSignal()

        del aliases[alias]
        self._write_aliases_to_alias_file(aliases)
        print_success(f"Unset alias '{alias}'")
        return ContinueSignal()

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        subparsers.add_parser("list", help="List all currently set aliases.")

        # set sub-command
        parser_set = subparsers.add_parser("set", help="Set an alias.")
        parser_set.add_argument(
            "alias",
            help="The alias to set.",
            type=str,
            nargs=1,
        )
        parser_set.add_argument(
            "command",
            help="The command to alias to.",
            type=str,
            nargs=1,
        )
        parser_set.add_argument(
            "-g",
            "--global",
            # `global` is a reserved keyword in python, we cant access this arg via
            # parsed_args.global, so we set dest to is_global and access it via
            # parsed_args.is_global
            dest="is_global",
            help="Configure whether the current alias being set is a global alias (defaults to False).",
            action="store_true",
        )

        # unset sub-command
        parser_unset = subparsers.add_parser("unset", help="Unset an alias.")
        parser_unset.add_argument(
            "alias",
            nargs=1,
            help="The alias to unset.",
            type=str,
        )

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            if parsed_args.sub_command == "list":
                return self._handle_list_sub_command(
                    context.interpreter_context.aliases
                )
            elif parsed_args.sub_command == "set":
                return self._handle_set_sub_command(
                    parsed_args, context.interpreter_context.aliases
                )
            elif parsed_args.sub_command == "unset":
                return self._handle_unset_sub_command(
                    parsed_args, context.interpreter_context.aliases
                )
            else:
                raise AssertionError(
                    f"Unknown alias sub-command {parsed_args.sub_command}"
                )
        except SystemExit:
            pass

        return ContinueSignal()
