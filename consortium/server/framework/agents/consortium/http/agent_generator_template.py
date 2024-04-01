from consortium.server.framework.agents.consortium.http.agent_generator import (
    AgentGenerator,
)
from consortium.server.framework.agents.consortium.http.agent_type import AGENT_TYPE
from consortium.server.framework.base_agent_generator_template import (
    BaseAgentGeneratorTemplate,
)
from consortium.server.framework.options import (
    ChoiceValueOption,
    ListValueOption,
    SingleValueOption,
)


def _check_all_url_endpoints_unique(
    options_dict: dict[str, SingleValueOption | ListValueOption],
) -> None:
    """Check that all the url endpoints are unique between the tasks, results and registration url paths."""
    all_url_paths = (
        options_dict["tasks_url_paths"].get_option_value()
        + options_dict["results_url_paths"].get_option_value()
    )
    all_url_paths.append(options_dict["registration_url_path"].get_option_value())
    unique_elements = set()
    for element in all_url_paths:
        if element in unique_elements:
            raise ValueError(
                'the tasks, results and registration url paths must not share any common url endpoints between all of them. the url path "{element}" violates this requirement',
            )
        unique_elements.add(element)


def _check_integer_is_a_valid_port_number(port: int) -> None:
    """Check that the integer provided is a valid port number (0 to 65535)."""
    if port not in range(0, 65536):
        raise ValueError(
            f"the port number {port} is not a valid port number. port numbers must be in the range of 0 to 65535",
        )


class AgentGeneratorTemplate(BaseAgentGeneratorTemplate):
    def __init__(self):
        name = "HTTP Consortium Agent"
        description = (
            "An HTTP based agent that is compatible with the HTTP Consortium Listener"
        )
        authors = ["Sekiun (github.com/not-sekiun)"]
        options = [
            SingleValueOption(
                name="remote_host",
                description="remote host interface of the listener to connect to",
                required=True,
                default_value="0.0.0.0",
                value_type=str,
            ),
            SingleValueOption(
                name="remote_port",
                description="remote port of the listener to connect to",
                required=True,
                default_value=1337,
                value_type=int,
                validating_function=_check_integer_is_a_valid_port_number,
            ),
            ListValueOption(
                name="tasks_url_paths",
                description="url paths for the agent to make GET requests to to obtain the task to run. url paths are randomly chosen",
                required=True,
                default_value=["/tasks"],
                allow_duplicates=False,
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            ListValueOption(
                name="results_url_paths",
                description="url paths for the agent to make POST requests to to return the results of tasks that were finished running. url paths are randomly chosen",
                required=True,
                default_value=["/results"],
                allow_duplicates=False,
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            ListValueOption(
                name="registration_url_paths",
                description="url paths for the agents to make POST requests to to register with the listener. the agent will query this path once at start up before receiving tasks and sending results. url paths are randomly chosen",
                required=True,
                default_value=["/register"],
                value_type=str,
                validating_regex=r"^\/[\w-]+(\.[\w-]+)*$",
            ),
            SingleValueOption(
                name="sleep_time",
                description="the amount of time in seconds to sleep between each request made to the listener. decimal values can be provided",
                required=True,
                default_value=1.0,
                value_type=float,
            ),
            SingleValueOption(
                name="jitter_percentage",
                description="the percentage of sleep_time to vary sleeping by. a random percentage value from 0 to jitter_time is chosen. decimal values can be provided",
                required=True,
                default_value=0.5,
                value_type=float,
                validating_function=lambda x: x >= 0,
            ),
            ChoiceValueOption(
                name="format",
                description="the format of the agent to be generated. it can be a single python script (py_script), a frozen pyinstaller executable (py_frozen) or a oneliner python command (py_oneline)",
                required=True,
                default_value="py_script",
                available_values=["py_script", "py_frozen", "py_oneline"],
            ),
            SingleValueOption(
                name="file_name",
                description="the name of the file to be generated. the file extension will be automatically appended based on format_option",
                required=True,
                default_value="agent",
                value_type=str,
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
