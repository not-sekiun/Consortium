from pathlib import Path

from consortium.components.agents.consortium.http.agent_generator import AgentGenerator
from consortium.components.agents.consortium.http.agent_type import AGENT_TYPE
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.framework_types import JSONObject
from consortium.framework.options import (
    ChoiceValueOption,
    ListValueOption,
    SingleValueOption,
)


def _check_jitter_percent_is_non_negative(jitter_percent: float):
    """
    Checks that the jitter percent is non-negative.
    """
    if jitter_percent < 0:
        raise OptionValueValidationError(
            "Jitter percent cannot be less than zero.",
        )


def _check_filename_does_not_traverse_directories(filename: str):
    """
    Checks that the filename does not attempt to traverse directories.
    """
    if filename != Path(filename).name:
        raise OptionValueValidationError(
            "Filename cannot traverse directories.",
        )


def _check_all_url_endpoints_unique(
    parameters: JSONObject,
) -> None:
    """
    Checks that the sets of the tasks, results and registration URL paths are mutually
    disjoint.
    """
    all_url_paths = (
        parameters["tasks_url_paths"]
        + parameters["results_url_paths"]
        + parameters["registration_url_paths"]
    )
    unique_elements = set()
    for element in all_url_paths:
        if element in unique_elements:
            raise OptionValueValidationError(
                f"The provided URL path '{element}' is not unique among the the tasks, "
                f"results and registration URL paths.",
            )
        unique_elements.add(element)


def _check_integer_is_a_valid_port_number(port: int) -> None:
    """
    Check that the integer provided is a valid port number between 0 and 65535.
    """
    if port not in range(0, 65536):
        raise OptionValueValidationError(
            f"The port number provided {port} is not a valid port number between 0 and "
            f"65535",
        )


class AgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.http_agent"
    name = "HTTP Agent"
    description = "An agent that communicates over the HTTP transport."
    version = "0.1.0"
    compatible_framework_version = ">=1.0.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    agent_generator = AgentGenerator
    agent_type = AGENT_TYPE
    options = {
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
            default_value="127.0.0.1",
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
            name="sleep_time_jitter",
            description=(
                "The percentage of the duration of the sleep time to randomly vary "
                "sleeping by expressed as a decimal. A random value between 0 and "
                "the value of the jitter percentage option is chosen to randomly "
                "increase or decrease the duration of the sleep time by."
            ),
            default_value=0.5,
            value_type=float,
            validating_function=_check_jitter_percent_is_non_negative,
        ),
        ChoiceValueOption(
            name="format",
            description=(
                "The format of the agent to be generated. It can be a single "
                "python script (script), a frozen pyinstaller executable "
                "(executable) or a oneliner python command (oneliner)."
            ),
            default_value="script",
            available_values={"script", "executable", "oneliner"},
        ),
        SingleValueOption(
            name="filename",
            description=(
                "The filename of the agent to be generated. The appropriate file "
                "extension is appended depending on the value of the 'format' "
                "option of the generated agent."
            ),
            default_value="agent",
            validating_function=_check_filename_does_not_traverse_directories,
        ),
    }
    validating_function = _check_all_url_endpoints_unique

    def resolve_agent_generator_name(self, parameters: JSONObject) -> str:
        return parameters["name"]
