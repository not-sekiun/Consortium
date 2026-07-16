from pathlib import Path

from consortium.framework.agents import BaseAgentTemplate
from consortium.framework.framework_types import JSONObject
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
)
from consortium.framework.signal_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.utils.random_utils import random_name

from ..agent_type import AgentType
from .agent_generator import AgentGenerator


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


def _check_goos_and_goarch_compatibility(parameters: JSONObject) -> None:
    go_tool_dist = [
        "darwin/amd64",
        "darwin/arm64",
        "linux/386",
        "linux/amd64",
        "linux/arm",
        "linux/arm64",
        "linux/loong64",
        "linux/mips",
        "linux/mips64",
        "linux/mips64le",
        "linux/mipsle",
        "linux/ppc64",
        "linux/ppc64le",
        "linux/riscv64",
        "linux/s390x",
        "windows/386",
        "windows/amd64",
        "windows/arm64",
    ]  # Output taken from `go tool dist list`
    if (parameters["os"] + "/" + parameters["arch"]) not in go_tool_dist:
        raise OptionValueValidationError(
            f"The provided OS '{parameters['os']}' and architecture "
            f"'{parameters['arch']}' combination is not supported by the Go toolchain. "
            f"Hint: Available combinations for the provided OS are: "
            f"{', '.join([i for i in go_tool_dist if i.startswith(parameters['os'])])}."
        )


class AgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.eula.golang"
    name = "Consortium Golang Eula Agent"
    description = (
        "The canonical Consortium agent, Eula, written in golang that communicates "
        "over the HTTP transport. This agent supports running on Windows, "
        "MacOS, and Linux, and supports cross-compilation."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    agent_generator = AgentGenerator
    agent_type = AgentType
    options = {
        SingleValueOption(
            name="name",
            description="Name of the agent generator.",
            required=False,
            default_value="",
            value_type=str,
        ),
        SingleValueOption(
            name="remote_host",
            description="Remote listener host address for the agent to connect back to.",
            value_type=str,
            default_value="127.0.0.1",
            required=False,
        ),
        SingleValueOption(
            name="remote_port",
            description="Remote listener port for the agent to connect back through.",
            default_value=1337,
            value_type=int,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=65535,
            required=False,
        ),
        ListValueOption(
            name="tasks_url_paths",
            description=(
                "List of available URL paths the agent randomly selects from when "
                "requesting tasks."
            ),
            default_value=["/tasks"],
            allow_duplicates=False,
            value_type=str,
            required=False,
            validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
        ),
        ListValueOption(
            name="results_url_paths",
            description=(
                "List of available URL paths the agent randomly selects from when "
                "posting task results."
            ),
            default_value=["/results"],
            allow_duplicates=False,
            value_type=str,
            required=False,
            validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
        ),
        ListValueOption(
            name="registration_url_paths",
            description=(
                "List of available URL paths the agent randomly selects from when "
                "registering with a listener."
            ),
            default_value=["/register"],
            value_type=str,
            required=False,
            validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
        ),
        SingleValueOption(
            name="sleep_time",
            description="Time in seconds to sleep between HTTP requests to the listener.",
            default_value=1.0,
            value_type=float,
            required=False,
        ),
        SingleValueOption(
            name="sleep_time_jitter",
            description=(
                "Random delay variance as a percentage of sleep time. Example: 0.5 "
                "adds +-50% randomness to sleep timing."
            ),
            default_value=0.5,
            value_type=float,
            greater_than_or_equal_to=0.0,
            required=False,
        ),
        SingleValueOption(
            name="file_name",
            description=(
                "Output filename of agent without extension. Extension is "
                "automatically appended based on format."
            ),
            default_value="agent",
            validating_function=_check_filename_does_not_traverse_directories,
            required=False,
        ),
        DictionaryValueOption(
            name="extra_headers",
            description=(
                "Dictionary of additional HTTP headers to include in each request to "
                "the listener."
            ),
            default_value={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0)",
            },
            value_type=str,
            required=False,
        ),
        ChoiceValueOption(
            name="os",
            description=(
                "Operating system for which to build the agent (only Windows, MacOS "
                "(darwin) and Linux are officially supported)."
            ),
            default_value="windows",
            available_values={"linux", "windows", "darwin"},
            required=False,
        ),
        ChoiceValueOption(
            name="arch",
            description=(
                "Architecture for which to build the agent (can be any GOARCH "
                "compatible string for the target platform)."
            ),
            default_value="amd64",
            available_values={
                "riscv64",
                "ppc64le",
                "arm64",
                "s390x",
                "loong64",
                "mips",
                "ppc64",
                "386",
                "mips64le",
                "amd64",
                "mipsle",
                "arm",
                "mips64",
            },
            required=False,
        ),
    }
    compatible_listener_types = {"http_consortium"}
    validating_function = _check_all_url_endpoints_unique

    def resolve_agent_generator_name(self, parameters: JSONObject) -> str:
        name = parameters.get("name", "")
        return str(name) if name else random_name()
