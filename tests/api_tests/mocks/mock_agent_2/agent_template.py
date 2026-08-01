from consortium.framework.agents import BaseAgentTemplate
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)

from .agent_generator import AgentGenerator
from .agent_type import AgentType


class AgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.mock_2"
    name = "Mock Agent 2"
    description = (
        "No-op agent 2 used by API tests; does not generate a real agent binary."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"test"}
    agent_generator = AgentGenerator
    agent_type = AgentType
    compatible_listener_types = set()
    options = {
        # Deliberately named "name" to keep the tests honest: a template option called
        # "name" is an ordinary option like any other and must never be conflated with
        # the created agent generator's display name.
        SingleValueOption(
            name="name",
            description="Arbitrary label carried as an agent generator parameter.",
            required=False,
            default_value="",
            value_type=str,
        ),
        SingleValueOption(
            name="beacon_jitter",
            description="Percentage variance applied to sleep_time for anti-pattern.",
            required=False,
            default_value=0.25,
            value_type=float,
            greater_than_or_equal_to=0.0,
            less_than_or_equal_to=1.0,
        ),
        SingleValueOption(
            name="max_task_size",
            description="Maximum task payload size in bytes the agent will accept.",
            required=False,
            default_value=4096,
            value_type=int,
            greater_than_or_equal_to=512,
        ),
        SingleValueOption(
            name="stealth_mode",
            description="Suppress all console and file output from the agent process.",
            required=False,
            default_value=False,
            value_type=bool,
        ),
        ListValueOption(
            name="proxy_urls",
            description="HTTP proxy URLs the agent will route traffic through.",
            required=False,
            default_value=[],
            allow_duplicates=False,
            value_type=str,
        ),
        ChoiceValueOption(
            name="arch",
            description="Target CPU architecture for the compiled agent binary.",
            required=False,
            default_value="x64",
            available_values={"x64", "x86", "arm64"},
        ),
        ToggleableChoicesValueOption(
            name="persistence_methods",
            description="Persistence mechanisms the agent registers on the host.",
            required=False,
            default_value={"registry_run_key": False, "scheduled_task": False},
            available_values={"registry_run_key", "scheduled_task", "startup_folder"},
        ),
        DictionaryValueOption(
            name="environment_vars",
            description="Environment variables injected into the agent at runtime.",
            required=False,
            default_value={},
            value_type=str,
        ),
        SingleValueOption(
            name="retry_count",
            description="Number of times the agent retries a failed check-in.",
            required=False,
            default_value=3,
            value_type=int,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=100,
        ),
    }
