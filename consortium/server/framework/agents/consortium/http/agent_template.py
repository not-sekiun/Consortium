from pathlib import Path

from consortium.server.framework.agents.consortium.http.agent_generator import (
    AgentGenerator,
)
from consortium.server.framework.agents.consortium.http.agent_type import AGENT_TYPE
from consortium.server.framework.base_agent_template import BaseAgentTemplate
from consortium.server.framework.options import (
    ChoiceValueOption,
    ListValueOption,
    SingleValueOption,
)


def _check_jitter_percent_is_positive(jitter_percent: float):
    if jitter_percent < 0:
        raise ValueError(
            "Jitter percent cannot be less than zero.",
        )


def _check_filename_does_not_traverse_directories(filename: str):
    """
    Checks that the filename does not attempt to traverse directories.
    """
    if filename != Path(filename).name:
        raise ValueError(
            "Filename cannot traverse directories.",
        )


def _check_all_url_endpoints_unique(
    options_dict: dict[str, SingleValueOption | ListValueOption],
) -> None:
    """
    Checks that the list of the tasks, results and registration URL paths are mutually
    exclusive to one another.
    """
    all_url_paths = (
        options_dict["tasks_url_paths"].get_option_value()
        + options_dict["results_url_paths"].get_option_value()
    )
    all_url_paths.append(options_dict["registration_url_paths"])
    unique_elements = set()
    for element in all_url_paths:
        if element in unique_elements:
            raise ValueError(
                f'The provided URL path "{element}" is not unique among the the tasks, '
                f"results and registration URL paths.",
            )
        unique_elements.add(element)


def _check_integer_is_a_valid_port_number(port: int) -> None:
    """
    Check that the integer provided is a valid port number between 0 and 65535.
    """
    if port not in range(0, 65536):
        raise ValueError(
            f"The port number provided {port} is not a valid port number between 0 and "
            "65535",
        )


class AgentTemplate(BaseAgentTemplate):
    def __init__(self):
        name = "HTTP Agent"
        description = "An agent that communicates over the HTTP transport."
        authors = ["Sekiun (github.com/not-sekiun)"]
        options = [
            SingleValueOption(
                name="name",
                description="The name of the agent generator being created.",
                required=False,
                default_value="",
                value_type=str,
            ),
            SingleValueOption(
                name="remote_host",
                description=(
                    "The remote host address of the listener for the agent to connect "
                    "back to."
                ),
                default_value="0.0.0.0",
                value_type=str,
            ),
            SingleValueOption(
                name="remote_port",
                description=(
                    "The remote port of the listener for the agent to connect back to."
                ),
                default_value=1337,
                value_type=int,
                validating_function=_check_integer_is_a_valid_port_number,
            ),
            ListValueOption(
                name="tasks_url_paths",
                description=(
                    "A list of available URL paths for the agent to randomly query "
                    "when obtaining tasks to run."
                ),
                default_value=["/tasks"],
                allow_duplicates=False,
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            ListValueOption(
                name="results_url_paths",
                description=(
                    "A list of available URL paths for the agent to randomly submit "
                    "to when returning the results of finished tasks."
                ),
                default_value=["/results"],
                allow_duplicates=False,
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            ListValueOption(
                name="registration_url_paths",
                description=(
                    "A list of available URL paths for the agent to randomly query "
                    "when registering with the listener."
                ),
                default_value=["/register"],
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            SingleValueOption(
                name="sleep_time",
                description=(
                    "The amount of time in seconds to sleep for between each request "
                    "made to the listener."
                ),
                default_value=1.0,
                value_type=float,
            ),
            SingleValueOption(
                name="jitter_percent",
                description=(
                    "The percentage of the duration of the sleep time to randomly vary "
                    "sleeping by. A random value between 0 and the value of the option "
                    '"jitter_percent" is chosen to randomly increase or decrease the'
                    "duration of the sleep time by."
                ),
                default_value=0.5,
                value_type=float,
                validating_function=_check_jitter_percent_is_positive,
            ),
            ChoiceValueOption(
                name="format",
                description=(
                    "The format of the agent to be generated. It can be a single "
                    "python script (script), a frozen pyinstaller executable "
                    "(executable) or a oneliner python command (oneliner)."
                ),
                default_value="script",
                available_values=["script", "executable", "oneliner"],
            ),
            SingleValueOption(
                name="filename",
                description=(
                    "The filename of the agent to be generated. The appropriate file "
                    'extension is appended depending on the value of the "format" '
                    "option of the generated agent."
                ),
                default_value="agent",
                validating_function=_check_filename_does_not_traverse_directories,
            ),
        ]
        validating_function = _check_all_url_endpoints_unique
        agent_generator = AgentGenerator
        super().__init__(
            name=name,
            description=description,
            agent_type=AGENT_TYPE,
            authors=authors,
            options=options,
            validating_function=validating_function,
            agent_generator=agent_generator,
        )

    def resolve_agent_generator_name(self) -> str:
        return self.options["name"].get_option_value()
