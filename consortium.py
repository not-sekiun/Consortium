import argparse

import consortium.client.start_client as start_client
import consortium.server.start_server as start_server


def main():
    parser = argparse.ArgumentParser(
        prog="consortium",
        description="Start the consortium server or client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    consortium server -h
    consortium client -h
""",
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
        epilog="""
Examples:
    consortium server
    consortium server -d
""",
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
        epilog="""
Examples:
    consortium client
    consortium client -d
""",
    )
    parser_client.add_argument(
        "-d",
        "--debug",
        help="Start the client in debug mode",
        action="store_true",
    )

    args = parser.parse_args()
    if args.command == "server":
        start_server.main(args)
    elif args.command == "client":
        start_client.main(args)


if __name__ == "__main__":
    main()
