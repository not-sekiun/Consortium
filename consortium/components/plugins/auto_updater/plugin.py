import json
import os
import subprocess
from datetime import datetime

import aiohttp
import prompt_toolkit
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from consortium.framework.plugins import BasePlugin
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    SERVER_RELEASE,
)


class Plugin(BasePlugin):
    label = "consortium.plugins.auto_updater_plugin"
    name = "Auto Updater Plugin"
    description = (
        "A plugin that attempts to check if there are any updates to the Consortium "
        "framework available over github. If updates are available, the plugin will "
        "prompt the user to update and restart the framework."
    )
    version = "0.1.0"
    compatible_framework_version = ">=1.0.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    @staticmethod
    def _run_cmd_with_spinner(cmd: str, message: str) -> tuple[int, bytes, bytes]:
        console = Console()
        spinner = Spinner("line", message)

        with Live(
            spinner,
            console=console,
            refresh_per_second=12,
            transient=True,
        ):
            proc = subprocess.run(
                cmd,
                capture_output=True,
            )
            return proc.returncode, proc.stdout, proc.stderr

    async def _get_latest_release_json_data(self) -> dict[str, str] | None:
        latest_project_version_file_url = "https://raw.githubusercontent.com/not-sekiun/Consortium/refs/heads/main/data/release.json"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(latest_project_version_file_url) as response:
                    if response.status != 200:
                        self.logger.error(
                            "Failed to retrieve latest release data. HTTP response status "
                            "code '{}' returned when querying for new release data.",
                            response.status,
                        )
                        return None
                    raw_data = await response.text()
                    return json.loads(raw_data)
            except aiohttp.ClientError as exc:
                self.logger.error(
                    f"Failed to retrieve latest release data: {exc}",
                )
                return None
            except json.JSONDecodeError as exc:
                self.logger.error(
                    f"Failed to parse latest release data: {exc}",
                )
                return None

    async def on_running(self) -> None:
        # json_data = await self._get_latest_release_json_data()

        json_data = {
            "codename": "Mock Release",
            "version": "9.9.9",
            "datetime_released": "2099-12-31T23:59:59",
        }

        if json_data is None:
            return
        latest_release_datetime = datetime.fromisoformat(json_data["datetime_released"])
        current_release_datetime = SERVER_RELEASE.datetime_released

        if latest_release_datetime > current_release_datetime:
            self.logger.info("New release found.")
            self.logger.info(
                f"- Current release: '{SERVER_RELEASE.codename}' "
                f"(v{SERVER_RELEASE.version}) released at {SERVER_RELEASE.datetime_released}",
            )
            self.logger.info(
                f"- Latest release: '{json_data['codename']}' (v{json_data['version']}) "
                f"released at {json_data['datetime_released']}",
            )
            while True:
                option = await prompt_toolkit.PromptSession().prompt_async(
                    "Update the framework automatically? [y/N]: ",
                )
                if option.lower() in ("y", "yes"):
                    # We intentionally block the event loop here running subprocess to
                    # update the framework without letting anything else start up. This
                    # also helps prevent log messages from other plugins/components from
                    # interleaving with the update process messages.
                    self.logger.info("[1/3] Changing to project root...")
                    os.chdir(str(CONSORTIUM_HOME_DIRECTORY_PATH.resolve()))
                    self.logger.info("[2/3] Pulling new release...")
                    return_code, stdout, stderr = self._run_cmd_with_spinner(
                        "git pull",
                        "Pulling new release via `git pull`...",
                    )
                    if return_code != 0:
                        self.logger.error(
                            f"Failed to pull new release via `git pull`: "
                            f"{stderr.decode().strip()}",
                        )
                        return
                    self.logger.info("[3/3] Installing new dependencies...")
                    return_code, stdout, stderr = self._run_cmd_with_spinner(
                        "uv sync",
                        "Installing new dependencies via `uv sync`...",
                    )
                    if return_code != 0:
                        self.logger.error(
                            f"- Failed to pull install new dependencies via `uv sync`: "
                            f"{stderr.decode().strip()}",
                        )
                        return
                    self.logger.success(
                        "Done. Restart the framework (CTRL-C) to apply updates."
                    )
                    return
                elif option.lower() in ("n", "no", None):
                    return
                else:
                    continue
        else:
            self.logger.info("Already on latest release.")
