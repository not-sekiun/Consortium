import json

from consortium.framework.base_plugin import BasePlugin


class Plugin(BasePlugin):
    name = "Persistent Agent Generators Plugin"
    description = (
        "A plugin that tracks what agent generators are created right before the "
        "framework exits. Upon startup again, this plugin will automatically create "
        "those generators that were previously created."
    )
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_plugin_started(self) -> None:
        persistent_agent_generators_json_file = (
            self.plugin_project_folder_path / "persistent_agent_generators.json"
        )
        # Save a reference so the `on_plugin_stopped` method can access it
        self.environment.persistent_agent_generators_json_file = (
            persistent_agent_generators_json_file
        )

        if not persistent_agent_generators_json_file.exists():
            self.plugin_logger.info(
                f"No persistent agent generators file found. Creating new persistent "
                f"agent generators file at: {persistent_agent_generators_json_file}",
            )
            with persistent_agent_generators_json_file.open("w") as file:
                file.write("{}")
            return

        self.plugin_logger.info(
            f"Reading persistent agent generators from: "
            f"{persistent_agent_generators_json_file}",
        )
        with persistent_agent_generators_json_file.open("r") as file:
            json_data = json.loads(file.read())

        # We refer to each agent template by its name (assume names are unique)
        # TODO: Provide a persistent way of referring to different agent templates
        #  across reboot.
        agent_templates = (
            self.server_services.agent_templates_service.get_all_agent_templates()
        )
        name_to_agent_template_map = {
            agent_template.name: agent_template for agent_template in agent_templates
        }
        for agent_template_name, agent_generators in json_data.items():
            for agent_generator_data in agent_generators:
                if agent_template_name not in name_to_agent_template_map:
                    self.plugin_logger.warning(
                        f"No agent template was found with the name "
                        f"'{agent_template_name}' from the persistent agent generators "
                        f"file. The corresponding agent profile may have been renamed "
                        f"or removed. Skipping...",
                    )
                    continue
                agent_template = name_to_agent_template_map[agent_template_name]
                agent_generator_name = agent_generator_data["name"]
                self.plugin_logger.success(
                    f"Creating agent generator '{agent_generator_name}'...",
                )
                self.server_services.agent_generators_service.create_agent_generator_from_agent_template_by_agent_template_id(
                    agent_template_id=str(agent_template.agent_template_id),
                    options=agent_generator_data["parameters"],
                    name=agent_generator_data["name"],
                    description=agent_generator_data["description"],
                )

    async def on_plugin_running(self) -> None:
        # TODO: If a plugin does not define a asynchronously blocking
        #  `on_plugin_running` function it is not counted as running because it
        #  immediately exits. Therefore the `on_plugin_stopped` method won't be called.
        #  Hence, we need to asynchronously block in this method for the plugin to be
        #  considered as "running". Maybe fix this behaviour?
        await self.stop_plugin_event.wait()

    async def on_plugin_stopped(self) -> None:
        persistent_agent_generators_json_file = (
            self.environment.persistent_agent_generators_json_file
        )
        persistent_agent_generators_json_data = {}
        for (
            agent_generator
        ) in self.server_services.agent_generators_service.get_all_agent_generators():
            if (
                str(agent_generator.creating_agent_template.name)
                not in persistent_agent_generators_json_data
            ):
                persistent_agent_generators_json_data[
                    str(agent_generator.creating_agent_template.name)
                ] = []
            persistent_agent_generators_json_data[
                str(agent_generator.creating_agent_template.name)
            ].append(
                {
                    "name": agent_generator.name,
                    "description": agent_generator.description,
                    "parameters": agent_generator.parameters,
                },
            )

        if not persistent_agent_generators_json_file.exists():
            self.plugin_logger.warning(
                f"No persistent agent generators file found even after plugin was "
                f"started. Creating new persistent agent generators file at: "
                f"{persistent_agent_generators_json_file}",
            )
            with persistent_agent_generators_json_file.open("w") as file:
                file.write("{}")

        with persistent_agent_generators_json_file.open("w") as file:
            file.write(json.dumps(persistent_agent_generators_json_data))

    async def on_plugin_cancelled(self) -> None:
        pass

    async def on_plugin_errored(self, exc: Exception) -> None:
        self.plugin_logger.opt(exception=exc).error(
            "Persistent agent generators plugin encountered a fatal error while "
            "running",
        )
