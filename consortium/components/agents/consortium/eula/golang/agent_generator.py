import shutil
import uuid

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
        command = ["docker", "build", "-t", "agent-builder", "."]
        output = await run_command(
            *command, working_dir=self.project_folder / "agent_source"
        )
        if output.return_code != 0:
            raise AgentGeneratorBuildStepRuntimeError(
                f"Failed to execute command '{' '.join(command)}':\n"
                f"{output.stdout + output.stderr}"
            )


class BuildAgent(BaseAgentGeneratorBuildStep):
    name = "Build Agent"
    description = "Build the agent within the docker container."

    async def build(self, parameters: dict) -> None:
        container_id = f"temp-agent-builder-container-{uuid.uuid4()}"
        commands = [
            [
                "docker",  # Command to start up the docker container from built image
                "run",
                "--name",
                container_id,
                "-e",
                f"GOOS={parameters['os']}",  # Setup GOOS env variable externally
                "-e",
                f"GOARCH={parameters['arch']}",  # Setup GOARCH env variable externally
                "agent-builder",
                "go",  # Actual command running inside docker container
                "build",
                "-o",
                "agent",
                ".",
            ],  # Compile agent inside container
            [
                "docker",
                "cp",
                f"{container_id}:/agent_builder/agent",
                parameters["file_name"]
                + (".exe" if parameters["os"] == "windows" else ""),
            ],  # Copy agent to host machine
            ["docker", "rm", "-f", container_id],  # Remove container
        ]

        for cmd in commands:
            output = await run_command(
                *cmd, working_dir=self.project_folder / "agent_source"
            )
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
