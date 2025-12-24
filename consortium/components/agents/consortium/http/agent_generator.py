import shutil

from consortium.framework.agents import (
    BaseAgentGenerator,
    BaseAgentGeneratorBuildStep,
)
from consortium.framework.agents.agent_generator_utils.string_utils import (
    multiple_string_replace,
)
from consortium.framework.exceptions import (
    AgentGeneratorStartError,
)


class BuildAgent(BaseAgentGeneratorBuildStep):
    name = "Build Agent"
    description = (
        "Build and export the agent to the server's payloads service. Will optionally "
        "freeze the agent into a bundled self-extracting executable with PyInstaller "
        "if specified by the 'format' option."
    )

    async def build(self, parameters: dict) -> None:
        with open(
            self.working_directory / "agent_source" / "_agent.py",
        ) as file:
            template_source_code = file.read()
            source_code = multiple_string_replace(
                template_source_code,
                {
                    "REMOTE_HOST": repr(parameters["remote_host"]),
                    "REMOTE_PORT": repr(parameters["remote_port"]),
                    "SLEEP_TIME": repr(parameters["sleep_time"]),
                    "SLEEP_TIME_JITTER": repr(parameters["sleep_time_jitter"]),
                    "TASKS_URL_PATHS": repr(parameters["tasks_url_paths"]),
                    "RESULTS_URL_PATHS": repr(parameters["results_url_paths"]),
                    "REGISTRATION_URL_PATHS": repr(
                        parameters["registration_url_paths"]
                    ),
                    "EXTRA_HEADERS": repr(parameters["extra_headers"]),
                },
            )
        print(source_code)

        # if parameters["format"] == "script":
        #     with open(
        #         CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / (parameters["filename"] + ".py"),
        #         "w",
        #     ) as file:
        #         file.write(source_code)
        # elif parameters["format"] == "executable":
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
        # elif parameters["format"] == "oneliner":
        #     with open(
        #         CONSORTIUM_ARTIFACTS_DIRECTORY_PATH / (parameters["filename"] + ".txt"),
        #         "w",
        #     ) as file:
        #         file.write('python -c "' + repr(source_code) + '"')
        # else:
        #     raise AgentGeneratorBuildStepRuntimeError(
        #         f"Unknown agent format '{parameters['format']}' specified when "
        #         "building the agent."
        #     )


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [
        BuildAgent(),
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
