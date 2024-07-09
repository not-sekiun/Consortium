import argparse


class ModuleHandler:
    def __init__(self):
        examples = """
Examples:

    shell -c whoami tasklist "taskkill /f /im discord.exe"
    shell -c "start notepad" -b  # Without the -b flag the process will hang until chrome.exe is closed
    shell -i -e  # -e disables environment variable parsing for changing directory, directories such as %APPDATA% will be taken literally and not be resolved
    shell -i -b  # all shell commands in interactive mode will be run blind

Note:
    shell will run commands in the default system shell.

"""
        self._parser = argparse.ArgumentParser(
            description="execute shell commands on the remote host",
            prog="shell",
            epilog=examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._parser.add_argument(
            "-b",
            "--blind",
            help="execute commands without checking output to prevent blocking when starting new processes",
            action="store_true",
        )
        self._group = self._parser.add_mutually_exclusive_group(required=True)
        self._group.add_argument(
            "-c",
            "--command",
            help="command to execute as a string",
            nargs="+",
        )
        self._group.add_argument(
            "-i",
            "--interactive",
            help="flag to toggle to interactive shell mode",
            action="store_true",
        )
        self._parser.add_argument(
            "-e",
            "--envparse",
            help="flag to DISABLE parsing of environment variables in paths when changing directory",
            action="store_false",
        )
        self._parser.add_argument(
            "-t",
            "--timeout",
            help="command execution timeout, defaults to 10 seconds. If a process does not return in time it is killed",
            default=10,
            type=int,
            nargs="?",
        )

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)
            if parsed_args.interactive:
                connection.send_json(
                    {"command": "shell", "args": {"interactive": "INIT_INTERACTIVE"}},
                )
                _, current_dir = connection.recv()
                print(
                    '[*] Type "exit" to exit out of interactive shell'
                    f"\n | [*] Executing blind : {parsed_args.blind}"
                    f"\n | [*] Executing with environment variable path parsing : {parsed_args.envparse}"
                    f"\n | [*] Executing with subprocess timeout : {parsed_args.timeout}",
                )
                while True:
                    command = input(f"{current_dir}> ").strip()
                    if command == "exit":
                        print("[*] Exiting shell...")
                        break
                    elif not command:
                        continue
                    else:
                        connection.send_json(
                            {
                                "command": "shell",
                                "args": {
                                    "execute": command,
                                    "blind": parsed_args.blind,
                                    "interactive": True,
                                    "env_parse": parsed_args.envparse,
                                    "timeout": parsed_args.timeout,
                                },
                            },
                        )
                        _, response = connection.recv()
                        print(response["message"])
                        current_dir = response["current_dir"]
            elif parsed_args.command:
                for command in parsed_args.command:
                    print(f"[*] Executing : {command}")
                    connection.send_json(
                        {
                            "command": "shell",
                            "args": {
                                "execute": command,
                                "blind": parsed_args.blind,
                                "interactive": False,
                                "env_parse": parsed_args.envparse,
                                "timeout": parsed_args.timeout,
                            },
                        },
                    )
                    _, response = connection.recv()
                    print(response["message"])
        except SystemExit:
            pass
