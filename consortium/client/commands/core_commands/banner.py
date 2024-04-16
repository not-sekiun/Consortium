import random

from consortium.client.client_config import CLIENT_RELEASE
from consortium.client.client_connection import ClientConnection
from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class BannerCommand(BaseCommand):
    name = "banner"
    description = "Display a banner."
    epilog = argparse_epilog_formatter(
        """
        Examples:
            banner  # Display a banner.
        """,
    )

    @staticmethod
    async def _display_banner(client_connection: ClientConnection | None) -> None:
        star_banner = (
            "[bold white]        .        x      "
            "[bold red]------[bold white]+             `        .          *   `     --.\n"
            "[bold white]  <<o>>            `     .          +               o         [bold red]----------[bold white]X\n"
            "[bold white]             x                       ,        +++       -<o>-       x\n"
            "[bold white]    `   o          =      '    -o        .         `     x      o  \n"
            "[bold red]       __________  _   _______ ____  ____  ____________  ____  ___    -------[bold white]X\n"
            "[bold white]x   .[bold red] / ____/ __ \\/ | / / ___// __ \\/ __ \\/_  __/  _/ / / /  |/  /\n"
            "[bold red]     / /   / / / /  |/ /\\__ \\/ / / / /_/ / / /  / // / / / /|_/ / [bold white]   +   `\n"
            "[bold red]    / /___/ /_/ / /|  /___/ / /_/ / _, _/ / / _/ // /_/ / /  / /  [bold red]------[bold white]X\n"
            "[bold white] ,[bold red]  \\____/\\____/_/ |_//____/\\____/_/ |_| /_/ /___/\\____/_/  /_/   [bold white]`   .   -\n"
            "[bold white]                          .                             -  \n"
            "[bold white]   x    [bold red]--------[bold white]+    .              <o>         X          [bold red]--------[bold white]x * <<o>>\n"
            "[bold white]      x              -x-       o          <o>        ,        ' `\n"
            "[bold white] <o>      .--+x   .          [bold red]--------[bold white]+ .        `     --.    x  [bold cyan]   [Ad astra!]\n"
        )
        banner_art = [star_banner]
        banner_text = [""]

        if client_connection is None:
            number_of_listeners = "N/A"
            number_of_agents = "N/A"
            server_release_formatted_string = "N/A"
            role = "N/A"
            connection_status_banner = (
                "[bold white]    Status         - "
                + "[bold red]Disconnected"
                + f"[bold white] | Logged in as N/A (role: {role})"
            )
        else:
            server_release = await client_connection.get_server_release()
            listeners = await client_connection.get_all_listeners()
            own_user = await client_connection.get_own_user_info()
            # TODO: Add agent API endpoint
            agents = []

            number_of_listeners = str(len(listeners))
            number_of_agents = str(len(agents))
            server_release_formatted_string = (
                f'v{server_release["version"]} "{server_release["codename"]}"'
            )

            role = own_user["role"]
            if role in ("OPERATOR", "SPECTATOR"):
                connection_status_banner = (
                    "[bold white]    Status         - "
                    + "[bold green]Connected"
                    + f'[bold white] | Logged in as "{client_connection.username}" (role: {role})'
                )
            else:  # Display the role in red for admin accounts.
                connection_status_banner = (
                    "[bold white]    Status         - "
                    + "[bold green]Connected"
                    + f'[bold white] | Logged in as "{client_connection.username}" (role: '
                    + f"[bold red]{role}"
                    + "[bold white])"
                )

        banner_art = random.choice(banner_art)
        author_banner = (
            "[bold white]    Author         - Sekiun (https://github.com/not-sekiun)"
        )
        client_version_banner = f'[bold white]    Client Release - v{CLIENT_RELEASE.version} "{CLIENT_RELEASE.codename}"'
        server_version_banner = (
            f"[bold white]    Server Release - {server_release_formatted_string}"
        )
        info_banner = (
            "[bold white]    Information    - "
            + f"[bold white]{number_of_listeners} Active listener(s) | "
            + f"[bold white]{number_of_agents} Active agent(s)"
        )
        quote_banner = f"    {random.choice(banner_text)}"

        CONSOLE.print(banner_art)
        CONSOLE.print(author_banner)
        CONSOLE.print(client_version_banner)
        CONSOLE.print(server_version_banner)
        CONSOLE.print(connection_status_banner)
        CONSOLE.print(info_banner)
        CONSOLE.print()
        CONSOLE.print(quote_banner)
        CONSOLE.print()

    def configure_parser(self, parser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            await self._display_banner(
                command_context.environment.get("client_connection"),
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
