import json

from consortium.framework.plugins import BasePlugin


class Plugin(BasePlugin):
    label = "consortium.plugins.persistent_agent_generators_plugin"
    name = "Persistent Agent Generators Plugin"
    description = (
        "A plugin that tracks what agent generators are created right before the "
        "framework exits. Upon startup again, this plugin will automatically create "
        "those generators that were previously created."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_started(self) -> None:
        persistent_agent_generators_json_file = (
            self.plugin_project_folder / "persistent_agent_generators.json"
        )
        # Save a reference so the `on_stopped` method can access it
        self.environment.persistent_agent_generators_json_file = (
            persistent_agent_generators_json_file
        )

        if not persistent_agent_generators_json_file.exists():
            self.logger.info(
                "No persistent agent generators file found. Creating new persistent "
                "agent generators file at: {}",
                persistent_agent_generators_json_file,
            )
            with persistent_agent_generators_json_file.open("w") as file:
                file.write("{}")
            return

        self.logger.info(
            "Loading persistent agent generators from: {}",
            persistent_agent_generators_json_file,
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
                    self.logger.warning(
                        "No agent template was found with the name "
                        "'{}' from the persistent agent generators "
                        "file. The corresponding agent profile may have been renamed "
                        "or removed. Skipping...",
                        agent_template_name,
                    )
                    continue
                agent_template = name_to_agent_template_map[agent_template_name]
                agent_generator_name = agent_generator_data["name"]
                self.logger.success(
                    "Creating agent generator '{}'...", agent_generator_name
                )
                self.server_services.agent_generators_service.create_agent_generator_from_agent_template_by_agent_template_id(
                    agent_template_id=str(agent_template.agent_template_id),
                    parameters=agent_generator_data["parameters"],
                    name=agent_generator_data["name"],
                    description=agent_generator_data["description"],
                )

    async def on_running(self) -> None:
        # TODO: If a plugin does not define a asynchronously blocking
        #  `on_running` function it is not counted as running because it
        #  immediately exits. Therefore the `on_stopped` method won't be called.
        #  Hence, we need to asynchronously block in this method for the plugin to be
        #  considered as "running". Maybe fix this behaviour?
        await self.stop_event.wait()

    async def on_stopped(self) -> None:
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
            self.logger.warning(
                "No persistent agent generators file found even after plugin was "
                "started. Creating new persistent agent generators file at: "
                "{}",
                persistent_agent_generators_json_file,
            )
            with persistent_agent_generators_json_file.open("w") as file:
                file.write("{}")

        with persistent_agent_generators_json_file.open("w") as file:
            file.write(json.dumps(persistent_agent_generators_json_data))
