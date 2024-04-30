import asyncio
import os
import shutil
from types import SimpleNamespace

from consortium.server.framework.base_agent_generator import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.server.framework.exceptions import AgentGeneratorStartError
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
    def __init__(self) -> None:
        name = "Create temporary directory"
        description = (
            "Create a temporary directory to store the intermediate agent source code"
            "for freezing the agent into an executable if necessary."
        )
        ignore_failure = False
        super().__init__(
            name=name,
            description=description,
            ignore_failure=ignore_failure,
        )

    async def on_agent_generator_build_step_running(
        self,
        stop_agent_generator_event: asyncio.Event,
        parameters: dict,
        build_context: SimpleNamespace,
    ):
        temporary_directory = (
            CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp"
        )
        if parameters["format"] == "executable":
            if not temporary_directory.is_dir():
                os.mkdir(str(temporary_directory))
        build_context.temporary_directory = temporary_directory


class BuildAgent(BaseAgentGeneratorBuildStep):
    def __init__(self) -> None:
        name = "Build agent"
        description = "Build the agent source code into the desired format."
        ignore_failure = False
        super().__init__(
            name=name,
            description=description,
            ignore_failure=ignore_failure,
        )

    async def on_agent_generator_build_step_running(
        self,
        stop_agent_generator_event: asyncio.Event,
        parameters: dict,
        build_context: SimpleNamespace,
    ):
        with open(
            CONSORTIUM_AGENTS_DIRECTORY_PATH
            / "consortium"
            / "http"
            / "source"
            / "agent.py",
            "r",
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
                    '"JITTER_PERCENTAGE"',
                    repr(parameters["jitter_percentage"]),
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
            build_context.source_code = source_code


class ExportAgentArtifact(BaseAgentGeneratorBuildStep):
    def __init__(self) -> None:
        name = "Export agent artifact"
        description = (
            "Export the agent to the server's artifacts folder. Freeze the "
            "agent into an executable with pyinstaller if specified by the "
            '"format" option'
        )
        ignore_failure = False
        super().__init__(
            name=name,
            description=description,
            ignore_failure=ignore_failure,
        )

    async def on_agent_generator_build_step_running(
        self,
        stop_agent_generator_event: asyncio.Event,
        parameters: dict,
        build_context: SimpleNamespace,
    ):
        if parameters["format"] == "script":
            with open(
                CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / parameters["filename"] + ".py",
                "w",
            ) as file:
                file.write(build_context.source_code)
        elif parameters["format"] == "executable":
            temporary_agent_file_path = (
                CONSORTIUM_AGENTS_DIRECTORY_PATH
                / "consortium"
                / "http"
                / ".tmp"
                / "tmp.py"
            )

            with open(temporary_agent_file_path, "w") as file:
                file.write(build_context.source_code)

            await asyncio.create_subprocess_exec(
                "pyinstaller",
                "--onefile",
                "--windowed",
                str(temporary_agent_file_path),
            )

            shutil.move(
                str(build_context.temporary_directory / "dist" / "tmp.exe"),
                str(CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / parameters["filename"])
                + ".exe",
            )
        elif parameters["format"] == "oneliner":
            with open(
                CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / parameters["filename"] + ".txt",
                "w",
            ) as file:
                file.write('python -c "' + repr(build_context.source_code) + '"')


class CleanupTemporaryDirectory(BaseAgentGeneratorBuildStep):
    def __init__(self) -> None:
        name = "Cleanup temporary directory"
        description = (
            "Cleanup the temporary directory created to store the intermediate agent "
            "source code for freezing the agent into an executable if necessary."
        )
        ignore_failure = False
        super().__init__(
            name=name,
            description=description,
            ignore_failure=ignore_failure,
        )

    async def on_agent_generator_build_step_running(
        self,
        stop_agent_generator_event: asyncio.Event,
        parameters: dict,
        build_context: SimpleNamespace,
    ):
        _cleanup_temporary_directory()


class AgentGenerator(BaseAgentGenerator):
    def __init__(self, *args, **kwargs) -> None:
        agent_generator_build_steps = [
            CreateTemporaryDirectory(),
            BuildAgent(),
            ExportAgentArtifact(),
            CleanupTemporaryDirectory(),
        ]
        super().__init__(
            *args,
            agent_generator_build_steps=agent_generator_build_steps,
            **kwargs,
        )

    def on_agent_generator_started(self) -> None:
        if self.parameters["format"] == "executable" and (
            shutil.which("pyinstaller") is None or shutil.which("python") is None
        ):
            raise AgentGeneratorStartError(
                message=(
                    "The PyInstaller python package is required to build a frozen "
                    'executable of the agent for the "format" option set to "frozen" '
                    "but was not found on the system's path."
                ),
            )

    def on_agent_generator_completed(self) -> None:
        # Cleanup temporary directory agent generator build step is guaranteed to have
        # ran already.
        pass

    def on_agent_generator_stopped(self) -> None:
        _cleanup_temporary_directory()

    def on_agent_generator_cancelled(self) -> None:
        _cleanup_temporary_directory()

    def on_agent_generator_errored(self, exc: Exception) -> None:
        _cleanup_temporary_directory()
