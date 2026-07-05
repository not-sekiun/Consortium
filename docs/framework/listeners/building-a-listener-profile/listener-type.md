# ListenerType

`ListenerType` is the simplest class in a listener profile. Its only job is to name the
transport family, so the framework can match this listener with the agents allowed to
connect through it.

## Declaring a listener type

`listener_type.py` declares the transport family name:

```python
from consortium.framework.listeners import BaseListenerType


class ListenerType(BaseListenerType):
    name = "tcp_json"
```

`name` is the only required attribute. It must be a non-empty string that is unique
across all listener types in your installation. The framework validates `name` at class
definition time, so a missing or duplicate name fails at import rather than at runtime.

## Linking agents to this listener

Agent templates reference this name in their `compatible_listener_types` set to declare
which listeners they are allowed to connect through:

```python
# In an agent template -- links back to the listener type by name
class AgentTemplate(BaseAgentTemplate):
    compatible_listener_types = {"tcp_json"}
```

At load time the framework populates `ListenerType.registered_compatible_agent_types`
with every agent type that named this listener as compatible. This set is managed
entirely by the framework; do not write to it manually.

Continue to [ListenerTemplate](listener-template.md) to declare the configuration schema.
