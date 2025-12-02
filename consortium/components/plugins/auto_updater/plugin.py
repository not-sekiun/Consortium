import json
import os
import subprocess
from datetime import datetime

import aiohttp
import prompt_toolkit

from consortium.framework.plugins.base_plugin import BasePlugin
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
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_plugin_started(self) -> None:
        pass

    async def on_plugin_running(self) -> None:
        latest_project_version_file_url = "https://raw.githubusercontent.com/not-sekiun/Consortium/refs/heads/main/data/release.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(latest_project_version_file_url) as response:
                if response.status != 200:
                    self.plugin_logger.error(
                        f"Failed to retrieve new release data due to invalid HTTP "
                        f"response status code: {response.status}",
                    )
                    return

                try:
                    raw_data = await response.text()
                except aiohttp.ClientError as exc:
                    self.plugin_logger.error(
                        f"Failed to retrieve new release data: {exc}",
                    )

                json_data = json.loads(raw_data)

        latest_release_datetime = datetime.fromisoformat(json_data["datetime_released"])
        current_release_datetime = SERVER_RELEASE.datetime_released

        self.plugin_logger.info(
            f"Current release: '{SERVER_RELEASE.codename}' "
            f"({SERVER_RELEASE.version}) released at {SERVER_RELEASE.datetime_released}",
        )
        self.plugin_logger.info(
            f"Latest release: '{json_data["codename"]}' ({json_data["version"]}) "
            f"released at {json_data["datetime_released"]}",
        )

        if latest_release_datetime > current_release_datetime:
            self.plugin_logger.info("New release found.")
            while True:
                option = await prompt_toolkit.PromptSession().prompt_async(
                    "Update and restart? [y/N]: ",
                )
                if option.lower() in ("y", "yes"):
                    # Intentionally block the event loop here to update and restart
                    # without letting any other services start up.
                    self.plugin_logger.info("[1/3] Changing to project root...")
                    os.chdir(str(CONSORTIUM_HOME_DIRECTORY_PATH.resolve()))
                    self.plugin_logger.info("[2/3] Pulling new release...")
                    subprocess.run("git pull")
                    self.plugin_logger.info("[3/3] Installing new dependencies...")
                    subprocess.run("poetry install")
                    self.plugin_logger.success("Done. Exiting framework...")
                    # TODO: Provide an actual mechanism for exiting that is cleaner.
                    #  This raises a SystemExit exception which blows up the event loop
                    #  with an ugly looking exception.
                    quit()
                elif option.lower() in ("n", "no", None):
                    return
                else:
                    continue
        else:
            self.plugin_logger.info("Already on latest release.")

    async def on_plugin_stopped(self) -> None:
        pass

    async def on_plugin_cancelled(self) -> None:
        pass

    async def on_plugin_errored(self, exc: Exception) -> None:
        self.plugin_logger.error(
            "Auto updater plugin encountered a fatal error while running.",
        )
