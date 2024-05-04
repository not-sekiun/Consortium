import argparse

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

    parser_server = subparsers.add_parser(
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
    parser_server.add_argument(
        "-d",
        "--debug",
        help="Start the server in debug mode",
        action="store_true",
    )

    parser_client = subparsers.add_parser(
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
    parser_client.add_argument(
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
