import asyncio
import pathlib
import shutil
import tempfile

from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.agents.agent_generator_utils import multiple_string_replace

# TODO: Move framework exceptions to signals to be more explicit
from consortium.framework.signal_exceptions import (
    AgentGeneratorBuildStepRuntimeError,
    AgentGeneratorStartError,
)


class BuildAgent(BaseAgentGeneratorBuildStep):
    name = "Build Agent"
    description = (
        "Build and export the agent as a Python script, oneliner command, or "
        "self-extracting PyInstaller executable."
    )

    async def build(self, parameters: dict) -> None:
        with open(
            self.working_directory / "agent_source" / "agent.py",
        ) as file:
            template_source_code = file.read()
            source_code = multiple_string_replace(
                template_source_code,
                {
                    'REMOTE_HOST = "127.0.0.1"': f"REMOTE_HOST = {repr(parameters['remote_host'])}",
                    "REMOTE_PORT = 1337": f"REMOTE_PORT = {repr(parameters['remote_port'])}",
                    "SLEEP_TIME = 1": f"SLEEP_TIME = {repr(parameters['sleep_time'])}",
                    "SLEEP_TIME_JITTER = 0.5": f"SLEEP_TIME_JITTER = {repr(parameters['sleep_time_jitter'])}",
                    'TASKS_URL_PATHS = ["/tasks"]': f"TASKS_URL_PATHS = {repr(parameters['tasks_url_paths'])}",
                    'RESULTS_URL_PATHS = ["/results"]': f"RESULTS_URL_PATHS = {repr(parameters['results_url_paths'])}",
                    'REGISTRATION_URL_PATHS = ["/register"]': f"REGISTRATION_URL_PATHS = {repr(parameters['registration_url_paths'])}",
                    'EXTRA_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)"}': f"EXTRA_HEADERS = {repr(parameters['extra_headers'])}",
                },
            )

        if parameters["format"] == "script":
            self.agent_templates_payload_service.create_payload_file(
                build_parameters=parameters,
                content=source_code,
                name=f"{parameters['file_name']}.py",
            )
        elif parameters["format"] == "executable":
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = pathlib.Path(temp_dir)
                agent_source_path = temp_path / "agent.py"
                agent_source_path.write_text(source_code)

                process = await asyncio.create_subprocess_exec(
                    "pyinstaller",
                    "--onefile",
                    "--windowed",
                    "--distpath",
                    str(temp_path / "dist"),
                    "--workpath",
                    str(temp_path / "build"),
                    "--specpath",
                    str(temp_path),
                    "--name",
                    parameters["file_name"],
                    str(agent_source_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise AgentGeneratorBuildStepRuntimeError(
                        f"PyInstaller failed to build the agent executable. "
                        f"Standard error output: {stderr.decode()}"
                    )

                dist_path = temp_path / "dist"
                exe_candidates = list(dist_path.iterdir())
                if not exe_candidates:
                    raise AgentGeneratorBuildStepRuntimeError(
                        "PyInstaller completed successfully but no output file "
                        f"was found in the dist directory '{dist_path}'."
                    )
                exe_path = exe_candidates[0]

                self.agent_templates_payload_service.add_payload_file(
                    build_parameters=parameters,
                    path=exe_path,
                    name=exe_path.name,
                )
        elif parameters["format"] == "oneliner":
            self.agent_templates_payload_service.create_payload_file(
                build_parameters=parameters,
                content='python -c "' + repr(source_code) + '"',
                name=f"{parameters['file_name']}.txt",
            )
        else:
            raise AgentGeneratorBuildStepRuntimeError(
                f"Unknown agent format '{parameters['format']}' specified when "
                "building the agent."
            )


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [
        BuildAgent,
    ]

    async def on_started(self) -> None:
        if (
            self.parameters["format"] == "executable"
            and shutil.which("pyinstaller") is None
        ):
            raise AgentGeneratorStartError(
                "For the `format` option set to 'executable', the `pyinstaller` "
                "tool is required to build a frozen executable of the agent, however, "
                "no such package was found on the system's path."
            )
