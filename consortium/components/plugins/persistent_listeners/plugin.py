import json

from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    label = "consortium.plugins.persistent_listeners_plugin"
    name = "Persistent Listeners Plugin"
    description = (
        "A plugin that tracks what listeners are created and running right before the "
        "framework exits. Upon startup again, this plugin will automatically create "
        "and run those listeners that were previously created and running again."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_started(self) -> None:
        persistent_listeners_json_file = (
            self.root_directory / "persistent_listeners.json"
        )
        # Save a reference so the `on_stopped` method can access it
        self.environment.persistent_listeners_json_file = persistent_listeners_json_file

        if not persistent_listeners_json_file.exists():
            self.logger.info(
                "No persistent listeners file found. Creating new persistent "
                "listeners file at: {}",
                persistent_listeners_json_file,
            )
            with persistent_listeners_json_file.open("w") as file:
                file.write("{}")
            return

        self.logger.info(
            "Loading persistent listeners from: {}", persistent_listeners_json_file
        )
        with persistent_listeners_json_file.open("r") as file:
            content = file.read().strip()
            # Handle empty file
            if not content:
                self.logger.warning(
                    "Persistent listeners JSON file is empty. "
                    "Treating as no persistent listeners."
                )
                json_data = {}
            else:
                json_data = json.loads(content)

        # We refer to each listener template by its label
        listener_templates = (
            self.services.listener_templates_service.get_all_listener_templates()
        )
        label_to_listener_template_map = {
            listener_template.label: listener_template
            for listener_template in listener_templates
        }
        for listener_template_label, listeners in json_data.items():
            for listener_data in listeners:
                if listener_template_label not in label_to_listener_template_map:
                    self.logger.warning(
                        "No listener template was found with the label "
                        "'{}' from the persistent listeners "
                        "file. The corresponding listener profile may have been "
                        "relabelled or removed. Skipping...",
                        listener_template_label,
                    )
                    continue
                listener_template = label_to_listener_template_map[
                    listener_template_label
                ]
                listener_name = listener_data["name"]
                if listener_data["previously_running"]:
                    self.logger.success(
                        "Creating and starting listener '{}'...", listener_name
                    )
                    listener = self.services.listeners_service.create_listener_from_listener_template_by_listener_template_id(
                        listener_template_id=str(
                            listener_template.listener_template_id,
                        ),
                        parameters=listener_data["parameters"],
                        name=listener_data["name"],
                        description=listener_data["description"],
                    )
                    await self.services.listeners_service.start_listener_by_listener_id(
                        listener_id=str(listener.listener_id),
                    )
                else:
                    self.logger.success("Creating listener '{}'...", listener_name)
                    self.services.listeners_service.create_listener_from_listener_template_by_listener_template_id(
                        listener_template_id=str(
                            listener_template.listener_template_id,
                        ),
                        parameters=listener_data["parameters"],
                        name=listener_data["name"],
                        description=listener_data["description"],
                    )

    async def on_running(self) -> None:
        await self.stop_event.wait()

    async def on_stopped(self) -> None:
        persistent_listeners_json_file = self.environment.persistent_listeners_json_file
        persistent_listeners_json_data = {}
        for listener in self.services.listeners_service.get_all_listeners():
            if (
                str(listener.creating_listener_template.label)
                not in persistent_listeners_json_data
            ):
                persistent_listeners_json_data[
                    str(listener.creating_listener_template.label)
                ] = []
            persistent_listeners_json_data[
                str(listener.creating_listener_template.label)
            ].append(
                {
                    "previously_running": listener.status.state == "RUNNING",
                    "name": listener.name,
                    "description": listener.description,
                    "parameters": listener.parameters,
                },
            )

        if not persistent_listeners_json_file.exists():
            self.logger.warning(
                "No persistent listeners file found even after plugin was "
                "started. Creating new persistent listeners file at: "
                "{}",
                persistent_listeners_json_file,
            )
            with persistent_listeners_json_file.open("w") as file:
                file.write("{}")

        with persistent_listeners_json_file.open("w") as file:
            file.write(json.dumps(persistent_listeners_json_data))
