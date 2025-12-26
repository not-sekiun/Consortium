import argparse

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
        "-s",
        "--server-config",
        help=(
            "The filepath of the server configuration file to use when starting the "
            "server. By default the server configuration file from "
            "`content/server/server_config.json` is used."
        ),
        nargs="?",
        default=None,
    )
    server_parser.add_argument(
        "-l",
        "--logging-config",
        help=(
            "The filepath of the logging configuration file to use when starting the "
            "server. By default the logging configuration file from "
            "`content/server/logging_config.json` is used."
        ),
        nargs="?",
        default=None,
    )
    server_parser.add_argument(
        "-d",
        "--debug",
        help=(
            "Start the server in debug mode. This will log messages with severity "
            "'DEBUG' and higher. Note that this flag overrides whatever log level was "
            "set in the supplied logging configuration file."
        ),
        action="store_true",
    )
    server_parser.add_argument(
        "-r",
        "--reload",
        help=(
            "Start the server with framework reloading enabled. This will reload the "
            "server on file changes made to the listener "
            "(consortium/components/listeners), agents (consortium/components/agents), "
            "plugins (consortium/components/plugins), and event hooks "
            "(consortium/components/event_hooks) framework component directories where "
            "custom framework components are loaded from. This is helpful for "
            "developing custom components."
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
            "`content/client/client_config.json` is used."
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
    # Conditional import because if you try to start a server "headless" without
    # client dependencies installed or without access to a console, it will error out
    # because of the client imports
    if arguments.command == "server":
        import consortium.server.start_server as start_server

        start_server.main(arguments)
    elif arguments.command == "client":
        import consortium.client.start_client as start_client

        start_client.main(arguments)


if __name__ == "__main__":
    main()
