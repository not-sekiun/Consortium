import argparse

from mkdocs.commands.serve import serve

import consortium.client.start_client as start_client
import consortium.server.start_server as start_server
from consortium.client.utils.formatter_utils import format_argparse_epilog


def main():
    parser = argparse.ArgumentParser(
        prog="consortium",
        description="Start the consortium server or client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=format_argparse_epilog(
            """
            Examples:
                consortium server -h
                consortium client -h
            """,
        ),
    )
    subparsers = parser.add_subparsers(
        help="Commands for invoking either the server or client",
        dest="command",
        required=True,
    )

    server_parser = subparsers.add_parser(
        name="server",
        help="Start the consortium server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=format_argparse_epilog(
            """
            Examples:
                consortium server
                consortium server -d
            """,
        ),
    )
    server_parser.add_argument(
        "-c",
        "--config",
        help=(
            "The filepath of the server configuration file to use when starting the "
            "server. By default the server configuration file from "
            "`data/server/server_config.json` is used."
        ),
        nargs="?",
        default=None,
    )
    server_parser.add_argument(
        "-d",
        "--debug",
        help=(
            "Start the server in debug mode. This will log messages with severity "
            "'DEBUG' and below. Note that this flag overrides whatever log level was "
            "set in the supplied server configuration file."
        ),
        action="store_true",
    )
    server_parser.add_argument(
        "-r",
        "--reload",
        help=(
            "Start the server with framework reloading enabled. This will reload the "
            "server on file changes made to the listener (`framework/listeners`), "
            "agents (`framework/agents`), plugins (`framework/plugins`), and event "
            "hooks (`framework/event_hooks`) framework directories where custom user "
            "extended code is loaded from. This is helpful for developing custom "
            "components."
        ),
        action="store_true",
    )

    client_parser = subparsers.add_parser(
        name="client",
        help="Start the consortium client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=format_argparse_epilog(
            """
            Examples:
                consortium client
                consortium client -d
            """,
        ),
    )
    client_parser.add_argument(
        "-c",
        "--config",
        help=(
            "The filepath of the client configuration file to use when starting the "
            "server. By default the client configuration file from "
            "`data/client/client_config.json` is used."
        ),
        nargs="?",
        default=None,
    )
    client_parser.add_argument(
        "-d",
        "--debug",
        help="Start the client in debug mode",
        action="store_true",
    )

    arguments = parser.parse_args()
    if arguments.command == "server":
        start_server.main(arguments)
    elif arguments.command == "client":
        start_client.main(arguments)


if __name__ == "__main__":
    main()
