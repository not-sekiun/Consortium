# AgentTemplate

`AgentTemplate` is the configuration schema and factory for `AgentGenerator` instances.
Its structure mirrors `ListenerTemplate`: it declares options, validates parameters, and
links the profile's generator and type together. It also declares which listener families
the generated agent can connect through.

## Required class attributes

```python
from consortium.framework.agents import BaseAgentTemplate
from consortium.framework.options import ChoiceValueOption, SingleValueOption

from .agent_generator import AgentGenerator
from .agent_type import AgentType


class AgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.recon_agent"
    name = "Recon Agent"
    description = "..."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}

    agent_generator = AgentGenerator   # class that builds the payload -- not an instance
    agent_type      = AgentType        # capabilities the generated agent exposes
    compatible_listener_types = {"tcp_json"}
```

`agent_generator` and `agent_type` must be the classes themselves, not instances. The
framework sets `creating_agent_template` on the `AgentGenerator` class at load time.

## compatible_listener_types

`compatible_listener_types` is a set of `ListenerType.name` strings. It declares which
listener families the generated agent can connect through. The framework uses this at
load time to:

1. Register the agent type as compatible with those listener types.
2. Make the agent selectable in the REST API when creating generator runs against a
   listener of that type.

```python
compatible_listener_types = {"tcp_json"}
```

If an agent supports multiple transports (e.g. HTTP and raw TCP) and you have separate
implementations, list all listener type names the agent can connect through.

## Options

Options follow exactly the same pattern as `ListenerTemplate`. They declare the
parameters an operator supplies when creating an agent generator:

```python
options = {
    SingleValueOption(
        name="remote_host",
        description="Listener host address the agent connects back to.",
        required=False,
        default_value="127.0.0.1",
        value_type=str,
    ),
    SingleValueOption(
        name="remote_port",
        description="Listener port the agent connects back through.",
        required=False,
        default_value=4444,
        value_type=int,
        greater_than_or_equal_to=1,
        less_than_or_equal_to=65535,
    ),
    ChoiceValueOption(
        name="format",
        description="Output format: 'script' for a .py file, 'oneliner' for a one-line command.",
        required=False,
        default_value="script",
        available_values={"script", "oneliner"},
    ),
    SingleValueOption(
        name="name",
        description="Display name for the generator run.",
        required=False,
        default_value="",
        value_type=str,
    ),
}
```

Cross-field validation uses the same `validating_function` pattern as `ListenerTemplate`.

## resolve_agent_generator_name

`resolve_agent_generator_name` is an abstract method that every template must implement.
It derives the generator's display name from the resolved parameters. It is called when
no explicit name is provided to `create_agent_generator()`:

```python
def resolve_agent_generator_name(self, parameters: dict) -> str:
    return parameters["name"]
```

## Complete template

```python
from consortium.framework.agents import BaseAgentTemplate
from consortium.framework.options import ChoiceValueOption, SingleValueOption

from .agent_generator import AgentGenerator
from .agent_type import AgentType


class AgentTemplate(BaseAgentTemplate):
    label = "consortium.agents.recon_agent"
    name = "Recon Agent"
    description = (
        "A lightweight Python reconnaissance agent that supports shell execution "
        "and file download over a raw TCP JSON protocol."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}

    agent_generator = AgentGenerator
    agent_type      = AgentType
    compatible_listener_types = {"tcp_json"}

    options = {
        SingleValueOption(
            name="remote_host",
            description="Listener host address the agent connects back to.",
            required=False,
            default_value="127.0.0.1",
            value_type=str,
        ),
        SingleValueOption(
            name="remote_port",
            description="Listener port the agent connects back through.",
            required=False,
            default_value=4444,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=65535,
        ),
        ChoiceValueOption(
            name="format",
            description="Output format: 'script' for a .py file, 'oneliner' for a one-line command.",
            required=False,
            default_value="script",
            available_values={"script", "oneliner"},
        ),
        SingleValueOption(
            name="name",
            description="Display name for the generator run.",
            required=False,
            default_value="",
            value_type=str,
        ),
    }

    def resolve_agent_generator_name(self, parameters: dict) -> str:
        return parameters["name"]
```
