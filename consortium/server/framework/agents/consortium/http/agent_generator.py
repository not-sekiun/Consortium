import asyncio
import os
import pathlib
import shutil

from consortium.server.framework.base_agent_generator import BaseAgentGenerator
from consortium.server.framework.framework_exceptions import AgentGeneratorQueueError
from consortium.server.server_config import (
    CONSORTIUM_AGENTS_DIRECTORY_PATH,
    CONSORTIUM_ARTIFACTS_DIRECTORY_PATH,
)


def cleanup_tmp_dir(tmp_dir: pathlib.Path) -> None:
    if tmp_dir.exists():
        shutil.rmtree(str(tmp_dir))


# TODO: Shift all this to a docker container
class AgentGenerator(BaseAgentGenerator):
    async def on_agent_generator_queued(self) -> bool:
        # Check the existence of required tools.
        if shutil.which("python") is None:
            raise AgentGeneratorQueueError(
                "Python is required to build the agent but was not found.",
            )
        if shutil.which("pyinstaller") is None:
            raise AgentGeneratorQueueError(
                "The pyinstaller package is required to build the agent but was not "
                "found.",
            )

    async def on_agent_generator_building(self) -> None:
        with open(
            str(
                CONSORTIUM_AGENTS_DIRECTORY_PATH
                / "consortium"
                / "http"
                / "source"
                / "http_transport.py",
            ),
            "r",
        ) as file:
            file_output = file.read()
            file_output = file_output.replace(
                '"REMOTE_HOST"',
                repr(self.options["remote_host"]),
                1,
            )
            file_output = file_output.replace(
                '"REMOTE_PORT"',
                repr(self.options["remote_port"]),
                1,
            )
            file_output = file_output.replace(
                '"SLEEP_TIME"',
                repr(self.options["sleep_time"]),
                1,
            )
            file_output = file_output.replace(
                '"JITTER_PERCENTAGE"',
                repr(self.options["jitter_percentage"]),
                1,
            )
            file_output = file_output.replace(
                '"TASKS_URL_PATHS"',
                repr(self.options["tasks_url_paths"]),
                1,
            )
            file_output = file_output.replace(
                '"RESULTS_URL_PATHS"',
                repr(self.options["results_url_paths"]),
                1,
            )
            file_output = file_output.replace(
                '"REGISTRATION_URL_PATHS"',
                repr(self.options["registration_url_paths"]),
                1,
            )
        with open(
            str(
                CONSORTIUM_AGENTS_DIRECTORY_PATH
                / "consortium"
                / "http"
                / "source"
                / "agent.py",
            ),
            "r",
        ) as file:
            file_output += file.read()

        if self.parameters["format"] == "py_script":
            with open(
                str(CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / self.parameters["file_path"])
                + ".py",
                "w",
            ) as file:
                file.write(file_output)
        elif self.parameters["format"] == "py_freeze":
            tmp_dir = CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp"
            if not tmp_dir.is_dir():
                os.mkdir(str(tmp_dir))
            with open(str(tmp_dir / "tmp.py"), "w") as file:
                file.write(file_output)
            await asyncio.create_subprocess_exec(
                "pyinstaller",
                "--onefile",
                "--windowed",
                str(tmp_dir / "tmp.py"),
            )
            shutil.move(
                str(tmp_dir / "dist" / "tmp.exe"),
                str(CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / self.parameters["file_path"])
                + ".exe",
            )
        elif self.parameters["format"] == "py_oneline":
            with open(
                str(CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / self.parameters["file_path"])
                + ".txt",
                "w",
            ) as file:
                file.write('python -c "' + repr(file_output) + '"')

    async def on_agent_generator_completed(self) -> None:
        cleanup_tmp_dir(
            CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp",
        )

    async def on_agent_generator_cancelled(self) -> None:
        pass
        if (CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp").exists():
            shutil.rmtree(
                str(CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp"),
            )

    async def on_agent_generator_errored(self, exc: Exception) -> None:
        if (CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp").exists():
            shutil.rmtree(
                str(CONSORTIUM_AGENTS_DIRECTORY_PATH / "consortium" / "http" / ".tmp"),
            )
