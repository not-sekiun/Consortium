import argparse

from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import InterpreterCommand
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import print_error, print_success


class GlobalCommand(BaseCommand):
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

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession | None,
        interpreter: BaseInterpreter,
    ) -> None:
        try:
            parsed_args = self._parser.parse_args(interpreter_command.arguments)

            for filepath in parsed_args.filepaths:
                try:
                    with open(filepath, "r") as file:
                        resource_commands = file.read().split("\n")
                        resource_commands.remove("")

                    for resource_command in resource_commands:
                        if (
                            not resource_command.strip()
                        ):  # Skip empty lines and whitespace.
                            pass
                        elif resource_command.startswith("#"):  # Skip comments.
                            pass
                        else:
                            client_database.resource_file_commands.append(
                                resource_command,
                            )
                    print_success(
                        f"Successfully loaded resource file, running commands...",
                    )
                except FileNotFoundError as e:
                    print_error(
                        f"Resource filepath {filepath} does not exist: {e}",
                    )
                except PermissionError as e:
                    print_error(
                        f"Resource filepath {filepath} could not be opened due to insufficient permissions: {e}",
                    )
        except SystemExit:
            pass
