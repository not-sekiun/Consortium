import os
import shutil

from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.agents.agent_generator_utils import run_command
from consortium.framework.signal_exceptions import (
    AgentGeneratorBuildStepRuntimeError,
    AgentGeneratorStartError,
)


class SetupDockerContainer(BaseAgentGeneratorBuildStep):
    name = "Setup Docker Container"
    description = "Set up a Docker container to compile the agent with."

    async def build(self, parameters: dict) -> None:
        os.chdir(self.project_folder / "agent_source")
        command = ["docker", "build", "-t", "agent-builder", "."]
        output = await run_command(*command)
        if output.return_code != 0:
            raise AgentGeneratorBuildStepRuntimeError(
                f"Failed to execute command '{' '.join(command)}':\n"
                f"{output.stdout + output.stderr}"
            )


class BuildAgent(BaseAgentGeneratorBuildStep):
    name = "Build Agent"
    description = "Build the agent within the docker container."

    async def build(self, parameters: dict) -> None:
        container_id = "temp-agent-builder-container"
        commands = [
            ["docker", "run", "--name", container_id, "agent-builder"],
            [
                "docker",
                "cp",
                f"{container_id}:/agent_builder/agent",
                parameters["file_name"],
            ],
            ["docker", "rm", "-f", container_id],
        ]

        for cmd in commands:
            output = await run_command(*cmd)
            if output.return_code != 0:
                raise AgentGeneratorBuildStepRuntimeError(
                    f"Failed to execute command '{' '.join(cmd)}':\n"
                    f"{output.stdout + output.stderr}"
                )


class ExportAgent(BaseAgentGeneratorBuildStep):
    name = "Export Agent"
    description = "Export the compiled agent binary as a payload"

    async def build(self, parameters: dict) -> None:
        self.agent_templates_payload_service.add_payload_file(
            path=self.project_folder / "agent_source" / "agent",
            name=parameters["file_name"],
            build_parameters=parameters,
        )  # Moves the file instead of copy so no cleanup is necessary afterwards


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [
        SetupDockerContainer,
        BuildAgent,
        ExportAgent,
    ]

    async def on_started(self) -> None:
        if shutil.which("docker") is None:
            raise AgentGeneratorStartError(
                "Docker is not installed or not found on the system path. Hint: Check "
                "https://docs.docker.com/get-started/get-docker/ for installing docker"
            )
        output = await run_command("docker", "info")
        if output.return_code != 0:  # Non-zero return code on non-running engine
            raise AgentGeneratorStartError(
                "The Docker engine is not currently running or accessible. Hint: Start "
                "the Docker service on Linux or launch Docker Desktop if on "
                "Windows/MacOS"
            )
