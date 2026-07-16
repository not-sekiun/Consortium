import shutil

from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.signal_exceptions import (
    AgentGeneratorStartError,
)


class SetupDockerContainer(BaseAgentGeneratorBuildStep):
    name = "Setup Docker Container"
    description = (
        "Set up a Docker container for the agent, including copying necessary files and "
        "configuring the environment."
    )

    async def build(self, parameters: dict) -> None:
        pass


class CompileAgent(BaseAgentGeneratorBuildStep):
    name = "Compile Agent"
    description = "Run the compilation within the Docker container"

    async def build(self, parameters: dict) -> None:
        pass


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [
        SetupDockerContainer,
        CompileAgent,
    ]

    async def on_started(self) -> None:
        if shutil.which("docker") is None:
            raise AgentGeneratorStartError(
                "Docker is not installed or not found in the system PATH. Hint: See "
                "https://docs.docker.com/get-started/get-docker/ for installing docker"
            )
