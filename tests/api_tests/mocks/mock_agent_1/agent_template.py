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
    label = "consortium.agents.mock_1"
    name = "Mock Agent 1"
    description = (
        "No-op agent 1 used by API tests; does not generate a real agent binary."
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
            name="retry_count",
            description="Number of times the agent retries a failed check-in.",
            required=False,
            default_value=3,
            value_type=int,
            greater_than_or_equal_to=0,
            less_than_or_equal_to=100,
        ),
        SingleValueOption(
            name="sleep_time",
            description="Seconds between each agent check-in attempt.",
            required=False,
            default_value=5.0,
            value_type=float,
            greater_than_or_equal_to=0.0,
        ),
        SingleValueOption(
            name="debug",
            description="Enable debug-level logging inside the generated agent.",
            required=False,
            default_value=False,
            value_type=bool,
        ),
        ListValueOption(
            name="fallback_hosts",
            description="Ordered list of fallback C2 hosts the agent cycles through.",
            required=False,
            default_value=[],
            allow_duplicates=False,
            value_type=str,
        ),
        ChoiceValueOption(
            name="format",
            description="Output format: 'script' (Python file) or 'oneliner'.",
            required=False,
            default_value="script",
            available_values={"script", "oneliner"},
        ),
        ToggleableChoicesValueOption(
            name="evasion_modules",
            description="Optional evasion techniques to embed in the agent.",
            required=False,
            default_value={"sleep_obfuscation": False, "process_hollowing": False},
            available_values={"sleep_obfuscation", "process_hollowing", "amsi_bypass"},
        ),
        DictionaryValueOption(
            name="extra_headers",
            description="Extra HTTP headers included in every agent request.",
            required=False,
            default_value={},
            value_type=str,
        ),
    }
