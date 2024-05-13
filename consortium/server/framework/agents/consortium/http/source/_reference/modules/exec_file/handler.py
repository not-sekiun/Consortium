import argparse

from custom_exceptions.internal_peer_error_error import InternalPeerErrorError


class ModuleHandler:
    def __init__(self):
        self._examples = """
Examples:

    exec_file file1 -e  # -e disables environment variable parsing for changing directory, directories such as %APPDATA% will be taken literally and not be resolved
    exec_file file1 file2 file3
    exec_file file1 "file 2" C:\\Path\\to\\file3
    exec_file "C:\\Path with\\spaces in it to\\file 3"


Note:
    There is no way for this module to definitively determine if the file it attempted to open actually executed

"""
        self._parser = argparse.ArgumentParser(
            description="Execute a file on the remote host",
            prog="exec",
            epilog=self._examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._parser.add_argument(
            "-e",
            "--envparse",
            help="flag to DISABLE parsing of environment variables in paths when executing files",
            action="store_false",
        )
        self._parser.add_argument(
            "filepaths",
            help="filepaths of files to execute, multiple files can be specified if separated with spaces",
            nargs="+",
        )

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)
            for filepath in parsed_args.filepaths:
                connection.send_json(
                    {
                        "command": "exec_file",
                        "args": {
                            "filepath": filepath,
                            "env_parse": parsed_args.envparse,
                        },
                    },
                )
                _, response = connection.recv()
                print(response)
        except SystemExit:
            pass
