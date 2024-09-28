import json

from consortium.framework.base_plugin import BasePlugin


class Plugin(BasePlugin):
    name = "Persistent Listeners Plugin"
    description = (
        "A plugin that tracks what listeners are created and running right before the "
        "framework exits. Upon startup again, this plugin will automatically create "
        "and run those listeners that were previously created and running again."
    )
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_plugin_started(self) -> None:
        persistent_listeners_json_file = (
            self.plugin_project_folder_path / "persistent_listeners.json"
        )
        # Save a reference so the `on_plugin_stopped` method can access it
        self.environment.persistent_listeners_json_file = persistent_listeners_json_file

        if not persistent_listeners_json_file.exists():
            self.plugin_logger.info(
                f"No persistent listeners file found. Creating new persistent "
                f"listeners file at: {persistent_listeners_json_file}",
            )
            with persistent_listeners_json_file.open("w") as file:
                file.write("{}")
            return

        self.plugin_logger.info(
            f"Reading persistent listeners from: {persistent_listeners_json_file}",
        )
        with persistent_listeners_json_file.open("r") as file:
            json_data = json.loads(file.read())

        # We refer to each listener template by its name (assume names are unique)
        # TODO: Provide a persistent way of referring to different listener templates
        #  across reboot.
        listener_templates = (
            self.server_services.listener_templates_service.get_all_listener_templates()
        )
        name_to_listener_template_map = {
            listener_template.name: listener_template
            for listener_template in listener_templates
        }
        for listener_template_name, listeners in json_data.items():
            for listener_data in listeners:
                if listener_template_name not in name_to_listener_template_map:
                    self.plugin_logger.warning(
                        f"No listener template was found with the name "
                        f"'{listener_template_name}' from the persistent listeners "
                        f"file. The corresponding listener profile may have been "
                        f"renamed or removed. Skipping...",
                    )
                    continue
                listener_template = name_to_listener_template_map[
                    listener_template_name
                ]
                listener_name = listener_data["name"]
                if listener_data["previously_running"]:
                    self.plugin_logger.success(
                        f"Creating and starting listener '{listener_name}'...",
                    )
                    listener = await self.server_services.listeners_service.create_listener_from_listener_template_by_listener_template_id(
                        listener_template_id=str(
                            listener_template.listener_template_id,
                        ),
                        options=listener_data["parameters"],
                        name=listener_data["name"],
                        description=listener_data["description"],
                    )
                    await self.server_services.listeners_service.start_listener_by_listener_id(
                        listener_id=str(listener.listener_id),
                    )
                else:
                    self.plugin_logger.success(
                        f"Creating listener '{listener_name}'...",
                    )
                    await self.server_services.listeners_service.create_listener_from_listener_template_by_listener_template_id(
                        listener_template_id=str(
                            listener_template.listener_template_id,
                        ),
                        options=listener_data["parameters"],
                        name=listener_data["name"],
                        description=listener_data["description"],
                    )

    async def on_plugin_running(self) -> None:
        # TODO: If a plugin does not define a asynchronously blocking
        #  `on_plugin_running` function it is not counted as running because it
        #  immediately exits. Therefore the `on_plugin_stopped` method won't be called.
        #  Hence, we need to asynchronously block in this method for the plugin to be
        #  considered as "running". Maybe fix this behaviour?
        await self.stop_plugin_event.wait()

    async def on_plugin_stopped(self) -> None:
        persistent_listeners_json_file = self.environment.persistent_listeners_json_file
        persistent_listeners_json_data = {}
        for listener in self.server_services.listeners_service.get_all_listeners():
            if (
                str(listener.creating_listener_template.name)
                not in persistent_listeners_json_data
            ):
                persistent_listeners_json_data[
                    str(listener.creating_listener_template.name)
                ] = []
            persistent_listeners_json_data[
                str(listener.creating_listener_template.name)
            ].append(
                {
                    "previously_running": listener.status.state == "RUNNING",
                    "name": listener.name,
                    "description": listener.description,
                    "parameters": listener.parameters,
                },
            )

        if not persistent_listeners_json_file.exists():
            self.plugin_logger.warning(
                f"No persistent listeners file found even after plugin was "
                f"started. Creating new persistent listeners file at: "
                f"{persistent_listeners_json_file}",
            )
            with persistent_listeners_json_file.open("w") as file:
                file.write("{}")

        with persistent_listeners_json_file.open("w") as file:
            file.write(json.dumps(persistent_listeners_json_data))

    async def on_plugin_cancelled(self) -> None:
        pass

    async def on_plugin_errored(self, exc: Exception) -> None:
        self.plugin_logger.opt(exception=exc).error(
            "Persistent listeners plugin encountered a fatal error while running",
        )
