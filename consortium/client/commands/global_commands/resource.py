import argparse

from consortium.client.client_exceptions import (
    IncompleteDoubleQuoteError,
    IncompleteEscapeError,
    IncompleteSingleQuoteError,
    ResourceFileAccessError,
    ResourceFileParseError,
)
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import InterpreterCommand
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_success
from consortium.client.objects.command_objects import ContinueReturnStatus


class ResourceCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="resource",
            description="Run resource files to automate running commands in the client.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    resource /path/to/file  # Run the commands in the resource file.
                    resource file1 relative/path/to/file2 /absolute/path/to/file3  # Run the commands in the resource files successively.
                """,
            ),
        )
        parser.add_argument("filepaths", nargs=1)
        super().__init__(parser)

    @staticmethod
    def _get_interpreter_commands_from_resource_file(
        interpreter: BaseInterpreter,
        filepath: str,
    ) -> list[InterpreterCommand]:
        interpreter_commands = []

        try:
            with open(filepath, "r") as file:
                # Each line is counted as a separate command.
                resource_commands = [
                    command for command in file.read().split("\n") if command
                ]
        except (FileNotFoundError, PermissionError) as e:
            raise ResourceFileAccessError(
                f'Failed to access resource file "{filepath}" because of the following error: {e}',
            )

        try:
            for resource_command in resource_commands:
                # Skip empty lines and comments in the resource file.
                if not resource_command.strip() or resource_command.startswith("#"):
                    pass
                else:
                    interpreter_command = (
                        interpreter.parse_tokenized_string_to_interpreter_command(
                            interpreter.resolve_token_aliases(
                                interpreter.tokenize_string(resource_command),
                            ),
                        )
                    )
                    interpreter_commands.append(interpreter_command)
            return interpreter_commands
        except (IncompleteDoubleQuoteError, IncompleteSingleQuoteError, IncompleteEscapeError):
            raise ResourceFileParseError(
                f'Failed to parse resource file "{filepath}" because it contained a command that was not properly formatted.',
            )

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None,
        interpreter: BaseInterpreter,
    ) -> ContinueReturnStatus:
        try:
            parsed_args = self._parser.parse_args(interpreter_command.arguments)

            for filepath in parsed_args.filepaths:
                try:
                    interpreter_commands = self._get_interpreter_commands_from_resource_file(
                        interpreter,
                        filepath,
                    )
                    print_success(
                        f"Successfully loaded resource file: {filepath}",

                    )
                    for interpreter_command in interpreter_commands:
                        interpreter.resource_interpreter_commands.put(interpreter_command)
                except (ResourceFileAccessError, ResourceFileParseError) as exc:
                    print_error(str(exc))
        except SystemExit:
            pass

        return ContinueReturnStatus()
