import random

from rich.text import Text

from consortium.client.client_config import CLIENT_RELEASE
from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context_models import AnyContext, ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_role_str_with_color,
)
from consortium.client.utils.printer_utils import console


class BannerCommand(BaseCommand[AnyContext]):
    name = "banner"
    description = "Display a banner with information about the Consortium framework"
    epilog = format_argparse_epilog(
        """
        Examples:
          banner
        """,
    )

    @staticmethod
    async def _display_banner(
        rest_api: RestAPI | None,
    ) -> None:
        logo_banner = Text.from_ansi(
            """
\x1b[2;90m    CONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTIU\x1b[0m                      \x1b[2;90mONSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m    \x1b[31mM@@@@@@@@@@@@@@@@@\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@p\x1b[0m  \x1b[31mM@@@@@@@@@@@@@@@\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@p\x1b[0m  \x1b[31m?@@@@@@@@@@@@@\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@m\x1b[0m \x1b[31ma[\x1b[0m        \x1b[31m`QL\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@@b\x1b[0m \x1b[31mMWL\x1b[0m     \x1b[31ma@f\x1b[0m   \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@@b\x1b[0m   \x1b[31mO@MMM@\x1b[0m      \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@@b\x1b[0m    \x1b[31mb\x1b[0m   \x1b[31m@\x1b[0m      \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@@b\x1b[0m   \x1b[31mo&mmm@\x1b[0m      \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@@b\x1b[0m \x1b[31mp@^\x1b[0m     \x1b[31mM@\x1b[0m    \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@@@B\x1b[0m \x1b[31mM[\x1b[0m        \x1b[31m;O^\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@@@M\x1b[0m  \x1b[31ma@@@@@@@@@@@@&\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m  \x1b[31m@M\x1b[0m  \x1b[31ma@@@@@@@@@@@@@@@\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTI\x1b[0m    \x1b[31ma@@@@@@@@@@@@@@@@@\x1b[0m  \x1b[2;90mNSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTIU\x1b[0m                      \x1b[2;90mONSORTIUMCONSORTIUM    \x1b[0m
\x1b[2;90m    CONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUM    \x1b[0m
"""
        )
        logo_banner = Text.from_ansi(
            """
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTIU\x1b[0m                      \x1b[2;38;2;146;131;116mONSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⡀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣦⡀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣦⣀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⣷⣄⣼⣍⠉⠉⠉⠉⠉⠉⠉⠉⢉⣽⣄\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⣿⡇⠈⠻⣷⣄⣀⣀⣀⣀⣀⣴⣿⠟⠁\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⣿⡇\x1b[0m  \x1b[38;2;204;36;29m⠈⣿⡿⠿⠿⠿⣿⡟⠁\x1b[0m    \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⣿⡇\x1b[0m   \x1b[38;2;204;36;29m⣿⡇\x1b[0m   \x1b[38;2;204;36;29m⣿⡇\x1b[0m     \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⣿⡇\x1b[0m  \x1b[38;2;204;36;29m⢀⣿⣷⣶⣶⣶⣿⣧⡀\x1b[0m    \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⣿⡇⢀⣴⡿⠋⠉⠉⠉⠉⠉⠻⣿⣦⡀\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⣿⣿⡿⠋⢻⣋⣀⣀⣀⣀⣀⣀⣀⣀⣈⣻⠋\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⣿⣿⠟⠉⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⣿⠟⠁⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTI\x1b[0m  \x1b[38;2;204;36;29m⠁⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿\x1b[0m  \x1b[2;38;2;146;131;116mNSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTIU\x1b[0m                      \x1b[2;38;2;146;131;116mONSORTIUMCONSORTIUM\x1b[0m
    \x1b[2;38;2;146;131;116mCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUMCONSORTIUM\x1b[0m
"""
        )
        ad_astra_banner = (
            "[bold white]        .        x      "
            "[bold red]    --[bold white]+             `        .          *   `     --.\n"
            "[bold white]  <<o>>            `     .          +               o         [bold red]        --[bold white]X\n"
            "[bold white]             x                       ,        +++       -<o>-       x\n"
            "[bold white]    `   o          =      '    -o        .         `     x      o  \n"
            "[bold red]       __________  _   _______ ____  ____  ____________  ____  ___        ---[bold white]X\n"
            "[bold white]x   .[bold red] / ____/ __ \\/ | / / ___// __ \\/ __ \\/_  __/  _/ / / /  |/  /\n"
            "[bold red]     / /   / / / /  |/ /\\__ \\/ / / / /_/ / / /  / // / / / /|_/ / [bold white]   +   `\n"
            "[bold red]    / /___/ /_/ / /|  /___/ / /_/ / _, _/ / / _/ // /_/ / /  / /  [bold red]    --[bold white]X\n"
            "[bold white] ,[bold red]  \\____/\\____/_/ |_//____/\\____/_/ |_| /_/ /___/\\____/_/  /_/   [bold white]`   .   -\n"
            "[bold white]                          .                             -  \n"
            "[bold white]   x    [bold red]        [bold white]+    .              <o>         X          [bold red]        [bold white]x * <<o>>\n"
            "[bold white]      x              -x-       o          <o>        ,        ' `\n"
            "[bold white] <o>      .--+x   .          [bold red]        [bold white]+ .        `     --.    x  [bold cyan]   [Ad astra!]\n"
        )
        banner_art = [ad_astra_banner, logo_banner]

        if rest_api is None:
            number_of_active_listeners = "N/A"
            number_of_online_agents = "N/A"
            server_release_formatted_string = "N/A"
            connection_status_banner = (
                "[bold white]    Connection Status  : [bold red]Disconnected"
            )
        else:
            server_release = await rest_api.get_server_release()
            listeners = [
                listener
                for listener in await rest_api.get_all_listeners()
                if listener["status"]["state"] == "RUNNING"
            ]
            own_user = await rest_api.get_own_user_info()
            agents = await rest_api.get_all_agents()

            number_of_active_listeners = str(len(listeners))
            number_of_online_agents = str(len(agents))
            server_release_formatted_string = (
                f"[bold cyan]v{server_release['version']} "
                f"[bold white]({server_release['codename']})"
            )

            connection_status_banner = (
                "    Connection Status  : "
                f"[bold green]Connected[bold white] as "
                f"'{rest_api.username}' "
                f"({format_role_str_with_color(role=own_user['role'])}[bold white])"
            )

        random_banner_art = random.choice(banner_art)
        author_banner = (
            "[bold white]    Author             : "
            "Sekiun (https://github.com/not-sekiun)"
        )
        client_version_banner = (
            f"[bold white]    Client Release     : "
            f"[bold cyan]v{CLIENT_RELEASE.version} "
            f"[bold white]({CLIENT_RELEASE.codename})"
        )
        server_version_banner = (
            f"[bold white]    Server Release     : {server_release_formatted_string}"
        )
        info_banner = (
            "[bold white]    Server Information : "
            f"[bold cyan]{number_of_active_listeners} [bold white]active [bold magenta]listener[bold white](s) | "
            f"[bold cyan]{number_of_online_agents} [bold white]online [bold magenta]agent[bold white](s)"
        )

        console.print(random_banner_art)
        console.print(author_banner)
        console.print(client_version_banner)
        console.print(server_version_banner)
        console.print(connection_status_banner)
        console.print(info_banner)
        console.print()

    async def run(
        self,
        context: AnyContext,
    ) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            await self._display_banner(
                rest_api=context.client_session.rest_api
                if isinstance(context, ConnectedContext)
                else None
            )
        except SystemExit:
            pass

        return ContinueSignal()
