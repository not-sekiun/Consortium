import argparse

from custom_exceptions.invalid_peer_response_error import InvalidPeerResponseError
from custom_exceptions.peer_connection_errored_out_error import (
    PeerConnectionErroredOutError,
    e,
)
from custom_exceptions.peer_timed_out_error import PeerTimedOutError


class ModuleHandler:
    def __init__(self):
        examples = """
Examples:

    ping
    ping -c 10  # ping 10 times

"""
        self._parser = argparse.ArgumentParser(
            description="ping agent",
            prog="ping",
            epilog=examples,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self._parser.add_argument(
            "-c",
            "--count",
            help="number of pings to send",
            type=int,
            nargs="?",
        )

    def run_module(self, command, input_args, connection):
        try:
            parsed_args = self._parser.parse_args(input_args)

            if parsed_args.count:
                count = parsed_args.count
            else:
                count = 1

            for _ in range(count):
                try:
                    connection.send_json({"command": "ping", "args": None})
                    print("[*] Sent ping")
                    _, response = connection.recv()
                    print(response)
                except (
                    InvalidPeerResponseError,
                    PeerConnectionErroredOutError,
                    PeerTimedOutError,
                ) as e:
                    print(f"[-] Agent is dead, malformed response received : {e}")
        except SystemExit:
            pass
