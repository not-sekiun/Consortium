import asyncio
import shutil
from types import SimpleNamespace
from typing import Any

from consortium.framework.agents.agent_generator_utils.filesystem_utils import (
    TemporarilyChangeWorkingDirectory,
)
from consortium.framework.agents.agent_generator_utils.shell_utils import run_command
from consortium.framework.agents.base_agent_generator import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorBuildError,
    AgentGeneratorStartError,
)
from consortium.server.server_config import (
    CONSORTIUM_AGENTS_DIRECTORY_PATH,
    CONSORTIUM_ARTIFACTS_DIRECTORY_PATH,
)


def _cleanup_temporary_directory() -> None:
    temporary_directory = (
        CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp"
    )
    if temporary_directory.is_dir():
        shutil.rmtree(str(temporary_directory))


class CreateTemporaryDirectory(BaseAgentGeneratorBuildStep):
    name = "Create Temporary Directory"
    description = (
        "Create a temporary directory to store the intermediate agent source code "
        "for freezing the agent into an executable if necessary."
    )
    ignore_failure = False

    async def on_running(
        self,
        stop_event: asyncio.Event,
        parameters: dict,
        environment: SimpleNamespace,
    ):
        temporary_directory = self.working_directory / ".tmp"
        if parameters["format"] == "executable":
            # Create the temporary directory, if it already exists, no error is raised.
            temporary_directory.mkdir(exist_ok=True)
        environment.temporary_directory = temporary_directory


class BuildAgent(BaseAgentGeneratorBuildStep):
    name = "Build Agent"
    description = "Build the agent source code into the desired format."
    ignore_failure = False

    async def on_running(
        self,
        stop_event: asyncio.Event,
        parameters: dict[str, Any],
        environment: SimpleNamespace,
    ):
        with open(
            self.working_directory / "agent_source" / "_agent.py",
        ) as file:
            template_source_code = file.read()
            source_code = (
                template_source_code.replace(
                    '"REMOTE_HOST"',
                    repr(parameters["remote_host"]),
                    1,
                )
                .replace(
                    '"REMOTE_PORT"',
                    repr(parameters["remote_port"]),
                    1,
                )
                .replace(
                    '"SLEEP_TIME"',
                    repr(parameters["sleep_time"]),
                    1,
                )
                .replace(
                    '"SLEEP_TIME_JITTER"',
                    repr(parameters["sleep_time_jitter"]),
                    1,
                )
                .replace(
                    '"TASKS_URL_PATHS"',
                    repr(parameters["tasks_url_paths"]),
                    1,
                )
                .replace(
                    '"RESULTS_URL_PATHS"',
                    repr(parameters["results_url_paths"]),
                    1,
                )
                .replace(
                    '"REGISTRATION_URL_PATHS"',
                    repr(parameters["registration_url_paths"]),
                    1,
                )
            )
            environment.source_code = source_code


class ExportAgentArtifact(BaseAgentGeneratorBuildStep):
    name = "Export Agent Artifact"
    description = (
        "Export the agent to the server's artifacts folder. Freeze the agent into an "
        "executable with pyinstaller if specified by the 'format' option."
    )

    async def on_running(
        self,
        stop_event: asyncio.Event,
        parameters: dict,
        environment: SimpleNamespace,
    ):
        if parameters["format"] == "script":
            with open(
                CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / (parameters["filename"] + ".py"),
                "w",
            ) as file:
                file.write(environment.source_code)
        elif parameters["format"] == "executable":
            temporary_agent_file_path = environment.temporary_directory / "tmp.py"

            with open(temporary_agent_file_path, "w") as file:
                file.write(environment.source_code)

            # Changing back to the previous working directory is crucial to avoid any
            # issues with deleting the temporary directory after building the agent due
            # to the server process still "using" the directory while it is in that
            # directory
            with TemporarilyChangeWorkingDirectory(
                new_working_directory=environment.temporary_directory,
            ):
                command_result = await run_command(
                    "pyinstaller",
                    "--onefile",
                    "--windowed",
                    str(temporary_agent_file_path),
                )

                if command_result.return_code != 0:
                    raise AgentGeneratorBuildError(
                        message=(
                            f"Failed to build agent executable: {command_result.stderr}"
                        ),
                    )

                shutil.move(
                    str(environment.temporary_directory / "dist" / "tmp.exe"),
                    str(CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / parameters["filename"])
                    + ".exe",
                )
        elif parameters["format"] == "oneliner":
            with open(
                CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / (parameters["filename"] + ".txt"),
                "w",
            ) as file:
                file.write('python -c "' + repr(environment.source_code) + '"')


class CleanupTemporaryDirectory(BaseAgentGeneratorBuildStep):
    name = "Cleanup Temporary Directory"
    description = (
        "Cleanup the temporary directory created to store the intermediate agent "
        "source code for freezing the agent into an executable if necessary."
    )
    ignore_failure = False

    async def on_running(
        self,
        stop_event: asyncio.Event,
        parameters: dict,
        environment: SimpleNamespace,
    ):
        _cleanup_temporary_directory()


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [
        CreateTemporaryDirectory(),
        BuildAgent(),
        ExportAgentArtifact(),
        CleanupTemporaryDirectory(),
    ]

    async def on_started(self) -> None:
        if self.parameters["format"] == "executable" and (
            shutil.which("pyinstaller") is None or shutil.which("python") is None
        ):
            raise AgentGeneratorStartError(
                message=(
                    "For the 'format' option set to 'executable', the PyInstaller "
                    "python package is required to build a frozen executable of the "
                    "agent. No such package was found on the system's path."
                ),
            )

    async def on_stopped(self) -> None:
        _cleanup_temporary_directory()

    async def on_cancelled(self) -> None:
        _cleanup_temporary_directory()

    async def on_errored(self, error: AgentGeneratorBuildError) -> None:
        await super().on_errored(error=error)
        _cleanup_temporary_directory()
