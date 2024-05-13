import argparse


class ModuleHandler:
    def __init__(self):
        examples = """
Examples:

    python -i
    python --reset
    python -e "import os;print(os.listdir(os.getcwd()))" "import platform;print(platform.platform())"
    python -f script1.py path/to/script2.py  # Warning, user input and loop breaking are NOT handled here, make sure your script terminates at some point or the agent WILL HANG

Note:
    The in memory python interpreter will share its namespace and variables across ALL invocations of the command. To reset all variables and clear the namespace use "-r/--reset"

"""
        self._parser = argparse.ArgumentParser(
            description="interact with an in memory python interpreter on the remote host",
            prog="python",
            epilog=examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._group = self._parser.add_mutually_exclusive_group()
        self._group.add_argument(
            "-i",
            "--interactive",
            help="start the python interpreter interactively",
            action="store_true",
        )
        self._group.add_argument(
            "-r",
            "--reset",
            help="reset the python interpreter",
            action="store_true",
        )
        self._group.add_argument(
            "-e",
            "--expressions",
            help="run a set of python expressions as strings",
            nargs="+",
        )
        self._group.add_argument(
            "-f",
            "--files",
            help="run an entire python script (Warning, user input and loop breaking are NOT handled here, make sure your script terminates at some point or the agent WILL HANG",
            nargs="+",
        )

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)
            if parsed_args.interactive:
                print("[*] Starting interactive interpreter...")
                print("[*] Use exit() to exit")
                while True:
                    execute = input(">>> ")
                    if execute == "exit()":
                        print("[*] Exiting...")
                        break
                    connection.send_json(
                        {
                            "command": "python",
                            "args": {
                                "interactive": execute,
                                "reset": None,
                                "single": None,
                                "file": None,
                            },
                        },
                    )
                    _, response = connection.recv()
                    print(response, end="")
            elif parsed_args.reset:
                connection.send_json(
                    {
                        "command": "python",
                        "args": {
                            "interactive": None,
                            "reset": parsed_args.reset,
                            "expressions": None,
                            "files": None,
                        },
                    },
                )
                _, response = connection.recv()
                print(response)
            elif parsed_args.expressions:
                connection.send_json(
                    {
                        "command": "python",
                        "args": {
                            "interactive": None,
                            "reset": None,
                            "expressions": parsed_args.expressions,
                            "files": None,
                        },
                    },
                )
                _, response = connection.recv()
                print(
                    "[*] Response (Code was executed in the order they were specified in the argument) :",
                )
                print(response)
            elif parsed_args.files:
                source_codes = []
                for filename in parsed_args.files:
                    try:
                        with open(filename, "r") as f:
                            source_codes.append(f.read())
                            print(f"[+] Loaded file : {filename}")
                    except Exception as e:
                        print(f"[-] Could not load file {filename}. Error : {e}")
                connection.send_json(
                    {
                        "command": "python",
                        "args": {
                            "interactive": None,
                            "reset": None,
                            "expressions": None,
                            "files": source_codes,
                        },
                    },
                )
                _, response = connection.recv()
                print(
                    "[*] Response (Files were executed in the order they were loaded) :",
                )
                print(response)
        except SystemExit:
            pass
