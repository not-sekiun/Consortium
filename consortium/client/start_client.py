import argparse
import json
import sys
from datetime import datetime

from loguru import logger

from consortium.client.client_config import (
    CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH,
    CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH,
)
from consortium.client.objects.client_objects import ClientConfig


async def main(args: argparse.Namespace) -> None:
    # Load client configuration file
    with open(str(CONSORTIUM_CLIENT_CONFIG_JSON_FILE_PATH), "r") as file:
        json_data = json.load(fp=file)
    client_config = ClientConfig(**json_data)

    # Configure logging.
    logger.remove()  # Remove all default out of the box loggers.
    logger.add(
        # ":" is invalid in filenames, so we replace it with the URL safe character
        # "-"
        f"{CONSORTIUM_CLIENT_LOGS_DIRECTORY_PATH}/{datetime.now().isoformat().replace(":", "-")}.log",
        colorize=False,
        format="[{time:YYYY-MM-DDTHH:mm:ssZ}] {level:<8} {message}",
        level="DEBUG" if args.debug else "INFO",
    )
    logger.level("DEBUG", color="<bold><green>")
    logger.level("INFO", color="<bold><blue>")
    logger.level("WARNING", color="<bold><yellow>")
    logger.level("ERROR", color="<bold><red>")
    logger.level("CRITICAL", color="<white><RED><bold>")
    logger.add(
        sys.stdout,
        colorize=True,
        format=(
            "<dim><white>[{time:YYYY-MM-DDTHH:mm:ssZ}]</></> <level>{level:<8}</> "
            "<dim><white>{extra[logger_name]}</></>: {message}"
        ),
        level="DEBUG" if args.debug else "INFO",
    )

    from consortium.client.client_session import ClientSession
    from consortium.client.commands.global_commands.agents import AgentsCommand
    from consortium.client.commands.global_commands.alias import AliasCommand
    from consortium.client.commands.global_commands.banner import BannerCommand
    from consortium.client.commands.global_commands.clear import ClearCommand
    from consortium.client.commands.global_commands.exit import ExitCommand
    from consortium.client.commands.global_commands.generator import GeneratorCommand
    from consortium.client.commands.global_commands.help import HelpCommand
    from consortium.client.commands.global_commands.home import HomeCommand
    from consortium.client.commands.global_commands.listeners import ListenersCommand
    from consortium.client.commands.global_commands.local import LocalCommand
    from consortium.client.interpreters.base_interpreter import BaseInterpreter
    from consortium.client.utils.standard_io_utils import color_red, color_white

    # from consortium.client.commands.global_commands.resource import (
    #     GlobalCommand as ResourceCommand,
    # )
    # Attempt to log in to server.
    try:
        client_session = ClientSession(
            client_config=client_config,
        )
        await client_session.login_session()
    except Exception as exc:
        print(f"Failed to login to server: {str(exc)}")
        return

    # Create and run the interpreter.
    test_interpreter = BaseInterpreter(
        prompt=color_white("Consortium (", bold=True)
        + color_red("Test", bold=True)
        + color_white(") > ", bold=True),
        commands=[
            BannerCommand(),
            ExitCommand(),
            LocalCommand(),
            HelpCommand(),
            HomeCommand(),
            ListenersCommand(),
            AgentsCommand(),
            GeneratorCommand(),
            ClearCommand(),
            AliasCommand(),
        ],
        client_session=client_session,
    )

    await test_interpreter.run_interpreter()
