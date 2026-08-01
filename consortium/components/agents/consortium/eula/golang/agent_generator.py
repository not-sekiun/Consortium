from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.utils.container_utils import (
    build_artifact_in_container,
    build_container_image,
    ensure_container_runtime_available,
)


class SetupDockerContainer(BaseAgentGeneratorBuildStep):
    name = "Setup Docker Container"
    description = "Set up a Docker container to compile the agent with."

    async def build(self, parameters: dict) -> None:
        self.environment.builder_image_tag = await build_container_image(
            self.root_directory / "agent_source"
        )


class BuildAgent(BaseAgentGeneratorBuildStep):
    name = "Build Agent"
    description = "Build the agent within the docker container."

    async def build(self, parameters: dict) -> None:
        # GOOS and GOARCH are read by the go toolchain from the environment, so the
        # one builder image cross compiles for every target.
        self.environment.agent_binary_path = await build_artifact_in_container(
            image_tag=self.environment.builder_image_tag,
            command=["garble", "build", "-o", "agent", "."],
            artifact_path="/agent_builder/agent",
            output_directory=self.root_directory / "agent_source",
            environment={"GOOS": parameters["os"], "GOARCH": parameters["arch"]},
        )


class ExportAgent(BaseAgentGeneratorBuildStep):
    name = "Export Agent"
    description = "Export the compiled agent binary as a payload"

    async def build(self, parameters: dict) -> None:
        await self.agent_templates_payload_service.add_payload_file(
            path=self.environment.agent_binary_path,
            name=parameters["file_name"]
            + (".exe" if parameters["os"] == "windows" else ""),
            build_parameters=parameters,
        )  # Moves the file instead of copy so no cleanup is necessary afterwards


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [
        SetupDockerContainer,
        BuildAgent,
        ExportAgent,
    ]

    async def on_started(self) -> None:
        await ensure_container_runtime_available()
