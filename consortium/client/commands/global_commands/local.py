import argparse
import asyncio
import os
import platform
import subprocess
from typing import Type

import prompt_toolkit

from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.filesystem_utils import (
    parse_system_environment_variables_in_filepaths,
)
from consortium.client.utils.standard_io_utils import (
    print_error,
    print_indented,
    print_info,
    print_plain,
)


class LocalCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="local",
            description="Run shell commands locally or open an interactive local shell.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    local -c ls -l  # Run the command "ls -l". Note that encapsulating the command in quotes is not necessary.
                    local -i -n  # Open an interactive shell without blocking on command execution.
                    local -c cd /path/to/directory  # Change to the directory /path/to/directory
                """,
            ),
        )
        parser.add_argument(
            "-n",
            "--non-blocking",
            help="Execute commands without checking their output to prevent blocking when starting new processes.",
            action="store_true",
        )
        parser.add_argument(
            "-i",
            "--interactive",
            help="Enter a local shell interactively.",
            action="store_true",
        )
        parser.add_argument(
            "-e",
            "--envparse",
            help="Flag to disable parsing of environment variables in filepaths when changing directory.",
            action="store_false",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            help="Command execution timeout. If a process does not return in time, it is killed. By default it is set to -1 to indicate no timeout.",
            default=None,
            type=int,
            nargs="?",
        )
        parser.add_argument(
            "-c",
            "--command",
            help="Command to execute. This should be the last positional argument passed to the command because all the characters after this will be interpreted as being literal parts of the command to be executed.",
            nargs="+",
        )
        super().__init__(parser)

    @staticmethod
    def _execute_command_in_shell(
        command: str,
        timeout: int | None,
        parse_system_environment_variables: bool,
        blocking: bool = True,
    ) -> None:
        if command.strip()[:2].lower() == "cd":
            directory = command.strip()[3:]
            # Interpret system environment variables for cd.
            if parse_system_environment_variables:
                directory = parse_system_environment_variables_in_filepaths(directory)
            try:
                os.chdir(directory)
                print_info(f"Changed to directory: {directory}")
            except FileNotFoundError:
                print_error(f"Path supplied does not exist: {directory}")
            except NotADirectoryError:
                print_error(
                    f"Path supplied is not a directory: {directory}",
                )
        else:
            if not blocking:
                print_info(f"Running command without blocking: {command}")
                subprocess.Popen(
                    command,
                    shell=True,
                )
                print_info(f"Ran command: {command}")
            else:
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        timeout=timeout,
                        capture_output=True,
                    )
                    print_plain(
                        (result.stdout + result.stderr).decode("utf-8"),
                    )
                except (KeyboardInterrupt, asyncio.CancelledError):
                    print_info(
                        "Caught KeyboardInterrupt, exiting out of process...",
                    )
                except subprocess.TimeoutExpired:
                    print_error("Command timed out.")

    async def _run_interactive_local_shell(
        self,
        blocking: bool,
        parse_system_environment_variables: bool,
        timeout: int | None,
    ) -> None:
        pass
        print_info('Type "exit" to exit out of interactive shell.')
        print_indented(
            f"Executing while blocking: {blocking}",
            print_func=print_info,
        )
        print_indented(
            f"Executing with system environment variable filepath parsing: {parse_system_environment_variables}",
            print_func=print_info,
        )
        if timeout is None:
            print_indented(
                f"Executing with subprocess timeout: {timeout} (Do not launch blocking processes with no timeout or the shell will block indefinitely)",
                print_func=print_info,
            )
        else:
            print_indented(
                f"Executing with subprocess timeout: {timeout}",
                print_func=print_info,
            )

        shell_session = prompt_toolkit.PromptSession()
        while True:
            try:
                current_dir = os.getcwd()
                # Emulating the native shell's prompt.
                if platform.system() == "Windows":
                    command = await shell_session.prompt_async(f"{current_dir}> ")
                else:
                    command = await shell_session.prompt_async(f"{current_dir}$ ")

                if command.lower() == "exit":
                    break
                else:
                    self._execute_command_in_shell(
                        command=command,
                        timeout=timeout,
                        parse_system_environment_variables=parse_system_environment_variables,
                        blocking=blocking,
                    )
            except (KeyboardInterrupt, asyncio.CancelledError):
                print_error(
                    'Caught KeyboardInterrupt (possibly from a running process). Use "exit" to exit out of the interactive shell.',
                )
            except subprocess.TimeoutExpired:
                print_error("Command timed out.")
        print_info("Exiting out of shell...")

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession,
        interpreter: Type[BaseInterpreter],
    ) -> ContinueReturnStatus:
        try:
            # The string can be tokenized without raising an exception because the
            # command is already being run.
            tokenized_string = interpreter.tokenize_string(
                interpreter_command.original_string,
            )
            aliased_string = interpreter_command.original_string

            alias_token = tokenized_string.tokens[0]
            while True:
                if alias_token in interpreter.command_aliases:
                    expanded_alias_tokenized_string = interpreter.tokenize_string(
                        interpreter.command_aliases[alias_token],
                    )
                    tokenized_string.tokens = (
                        expanded_alias_tokenized_string.tokens
                        + tokenized_string.tokens[1:]
                    )
                    aliased_string = aliased_string.replace(
                        alias_token,
                        interpreter.command_aliases[alias_token],
                        1,
                    )
                    alias_token = tokenized_string.tokens[0]
                else:
                    break

            for index, argument in enumerate(interpreter_command.arguments):
                if argument in ("-c", "--command"):
                    # Modify the arguments of interpreter command to interpret all
                    # characters after the -c/--command option into a single token to be
                    # interpreted without having to encapsulate the command in quotes.
                    if aliased_string.find("-c") != -1:
                        command = aliased_string.split("-c", 1)[1].strip()
                    elif aliased_string.find("--command") != -1:
                        command = aliased_string.split(
                            "--command",
                            1,
                        )[1].strip()

                    interpreter_command.arguments = interpreter_command.arguments[
                        : index + 1
                    ]
                    interpreter_command.arguments.append(command)

            parsed_args = self._parser.parse_args(interpreter_command.arguments)

            if parsed_args.interactive:
                await self._run_interactive_local_shell(
                    blocking=not parsed_args.non_blocking,
                    parse_system_environment_variables=parsed_args.envparse,
                    timeout=parsed_args.timeout,
                )
            else:
                self._execute_command_in_shell(
                    command=parsed_args.command[0],
                    blocking=not parsed_args.non_blocking,
                    timeout=parsed_args.timeout,
                    parse_system_environment_variables=parsed_args.envparse,
                )
        except SystemExit:
            pass

        return ContinueReturnStatus()
