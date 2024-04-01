import argparse
import random
from typing import Type

from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.interpreters.base_interpreter import BaseInterpreter
from consortium.client.objects.command_objects import (
    ContinueReturnStatus,
    InterpreterCommand,
)
from consortium.client.utils.data_structure_utils import argparse_epilog_formatter
from consortium.client.utils.standard_io_utils import (
    color_cyan,
    color_green,
    color_red,
    color_white,
    print_plain,
)


class BannerCommand(BaseCommand):
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog="banner",
            description="Display a banner.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=argparse_epilog_formatter(
                """
                Examples:
                    banner

                """,
            ),
        )
        super().__init__(parser)

    @staticmethod
    async def _print_banner(client_session: ClientSession) -> None:
        flavor_text = [
            # color_white(
            #     "Audentes fortuna adiuvat | Fortune favors the bold", bold=True
            # ),
            # color_white("Cogito, ergo sum", bold=True),
            # color_white("Powered by prompt-toolkit", bold=True),
            # color_white("CTRL-C resistant", bold=True),
            # color_white("No shortage of spaghetti code", bold=True),
            # color_white("∫E.da = qenc/ε0", bold=True),
            # color_white("RIP Fluxnotes, 2018-2018", bold=True),
            # color_magenta(
            #     "Inazuma shines eternal ⛩️ 稲光、すなわち永遠なり。", bold=True
            # ),
            # "".join(
            #     random.choice(
            #         [
            #             color_white,
            #             color_red,
            #             color_green,
            #             color_blue,
            #             color_cyan,
            #             color_magenta,
            #         ]
            #     )(char, bold=True)
            #     for char in "Full color support on all major OSes!"
            # ),
            color_white("Hint: Press tab to autocomplete commands", bold=True),
            color_white(
                "Hint: Access the command history with the up or down arrow keys",
                bold=True,
            ),
            color_white(
                'Hint: To escape quotes within quotes use a backslash like this "\\"Quoted argument\\""',
                bold=True,
            ),
            color_white(
                "Hint: Every event that happens on the Consortium server and client is logged, log files are located at data/{server, client}/logs",
                bold=True,
            ),
            color_white(
                'Hint: "!" is the default alias for "local -c" allowing you to run shell commands locally by prepending them with "! "',
                bold=True,
            ),
            color_white(
                'Hint: "?" is the default alias for "help" allowing you to quickly get help for commands by prepending them with "? "',
                bold=True,
            ),
            color_white(
                "Hint: Enter multiline input by ending a line with a quote character (\", ') and then pressing enter to continue input on the next line",
                bold=True,
            ),
        ]

        # fmt: off
        star_banner = \
            "\n" + color_white("        .        x      ", bold=True) + color_red("------", bold=True) + color_white("+             `        .          *   `     --.", bold=True) + "\n" + \
            color_white("  <<o>>            `     .          +               o         ", bold=True) + color_red("----------", bold=True) + color_white("X", bold=True) + "\n" + \
            color_white("             x                       ,        +++       -<o>-       x" + "\n" + "    `   o          =      '    -o        .         `     x      o  ", bold=True) + "\n" + \
            color_red("       __________  _   _______ ____  ____  ____________  ____  ___", bold=True) + color_red("    -------", bold=True) + color_white("X", bold=True) + "\n" + \
            color_white("x   .", bold=True) + color_red(" / ____/ __ \\/ | / / ___// __ \\/ __ \\/_  __/  _/ / / /  |/  /", bold=True) + "\n" + \
            color_red("     / /   / / / /  |/ /\\__ \\/ / / / /_/ / / /  / // / / / /|_/ / ", bold=True) + color_white("   +   `", bold=True) + "\n" + \
            color_red("    / /___/ /_/ / /|  /___/ / /_/ / _, _/ / / _/ // /_/ / /  / /  ", bold=True) + color_red("------", bold=True) + color_white("X", bold=True) + "\n" + \
            color_white(" ,", bold=True) + color_red("  \\____/\\____/_/ |_//____/\\____/_/ |_| /_/ /___/\\____/_/  /_/   ", bold=True) + color_white("`   .   -", bold=True) + "\n" + \
            color_white("                          .                             -  ", bold=True) + "\n" + \
            color_white("   x    ", bold=True) + color_red("--------", bold=True) + color_white("+", bold=True) + color_white("    .              <o>         X          ", bold=True) + color_red("--------", bold=True) + color_white("x * <<o>>", bold=True) + "\n" + \
            color_white("      x              -x-       o          <o>        ,        ' `" + "\n" + " <o>      .--+x   .          ", bold=True) + color_red("--------", bold=True) + color_white("+ .        `     --.    x  ", bold=True) + color_cyan("   [Ad astra!]") + "\n"
        # fmt: on
        banner_art = [star_banner]

        if client_session is None:
            number_of_listeners = "N/A"
            number_of_agents = "N/A"
            server_release = "N/A"
            role = "N/A"
            connection_status_banner = (
                color_white("    Status         - ", bold=True)
                + color_red("Disconnected", bold=True)
                + color_white(f" | Logged in as ? (role: {role})", bold=True)
            )
        else:
            server_release = await (
                await client_session.authorized_session.get(
                    f"{client_session.api_url}/server/release",
                )
            ).json()
            listeners = await (
                await client_session.authorized_session.get(
                    f"{client_session.api_url}/listeners/all",
                )
            ).json()
            own_user = await (
                await client_session.authorized_session.get(
                    f"{client_session.api_url}/users/me",
                )
            ).json()
            # TODO: Add agent API endpoint
            agents = []

            number_of_listeners = str(len(listeners))
            number_of_agents = str(len(agents))
            server_release = (
                f'v{server_release["version"]} "{server_release["codename"]}"'
            )

            role = own_user["role"]

            if role in ("OPERATOR", "SPECTATOR"):
                connection_status_banner = (
                    color_white("    Status         - ", bold=True)
                    + color_green("Connected", bold=True)
                    + color_white(
                        f' | Logged in as "{client_session.client_config.username}" (role: {role})',
                        bold=True,
                    )
                )
            else:  # admin account
                connection_status_banner = (
                    color_white(
                        f"    Status         - ",
                        bold=True,
                    )
                    + color_green("Connected", bold=True)
                    + color_white(
                        f' | Logged in as "{client_session.client_config.username}" (role: ',
                        bold=True,
                    )
                    + color_red(role, bold=True)
                    + color_white(")", bold=True)
                )

        banner_art = random.choice(banner_art)
        author_banner = color_white(
            "    Author         - Sekiun (https://github.com/not-sekiun)",
            bold=True,
        )
        client_version_banner = color_white(
            f'    Client Release - v{client_session.client_release.version} "{client_session.client_release.codename}"',
            bold=True,
        )
        server_version_banner = color_white(
            f"    Server Release - {server_release}",
            bold=True,
        )
        info_banner = (
            color_white("    Information    - ", bold=True)
            + color_white(number_of_listeners + " Active listener(s) | ", bold=True)
            + color_white(number_of_agents + " Active agent(s)", bold=True)
        )
        quote_banner = "    " + random.choice(flavor_text)

        print_plain(banner_art)
        print_plain(author_banner)
        print_plain(client_version_banner)
        print_plain(server_version_banner)
        print_plain(connection_status_banner)
        print_plain(info_banner)
        print_plain()
        print_plain(quote_banner)
        print_plain()

    async def run_command(
        self,
        interpreter_command: InterpreterCommand,
        client_session: ClientSession,
        interpreter: Type[BaseInterpreter],
    ) -> ContinueReturnStatus:
        try:
            _ = self._parser.parse_args(interpreter_command.arguments)
            await self._print_banner(client_session)
        except SystemExit:
            pass

        return ContinueReturnStatus()
