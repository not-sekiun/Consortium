import asyncio
import shutil

from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.agents.agent_generator_utils import multiple_string_replace

# TODO: Move framework exceptions to signals to be more explicit
from consortium.framework.exceptions import (
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
        await asyncio.sleep(5)

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
            )
        elif parameters["format"] == "executable":
            pass
            #     with tempfile.TemporaryDirectory() as temporary_directory:
            #         os.chdir(temporary_directory)
            #
            #         with open("agent.py") as temporary_file:
            #             temporary_file.write(source_code)
            #
            #         process = await run_command(
            #             "pyinstaller",
            #             "--onefile",
            #             "--windowed",
            #             "agent.py",
            #         )
            #
            #         if process.return_code != 0:
            #             raise AgentGeneratorBuildStepRuntimeError(
            #                 f"Pyinstaller failed to freeze agent source code into packaged "
            #                 f"executable. Standard error output: {process.stderr}"
            #             )
            #
            #         shutil.move(
            #             "agent.exe",
            #             str(CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / parameters["filename"])
            #             + ".exe",
            #         )
        elif parameters["format"] == "oneliner":
            self.agent_templates_payload_service.create_payload_file(
                build_parameters=parameters,
                content='python -c "' + repr(source_code) + '"',
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
