# ListenerType

`ListenerType` is the simplest class in a listener profile. It names the transport
family so the framework can match this listener with compatible agents.

## Project files

Before writing any code, create the directory and manifest for your profile:

```
consortium/components/listeners/tcp_json/
├── manifest.json
├── listener_type.py
├── listener_template.py
└── listener.py
```

`manifest.json` tells the loader where the profile entry class lives:

```json
{
    "entry_point": "listener_template:ListenerTemplate",
    "enabled": true
}
```

The entry point must always be `listener_template:ListenerTemplate`.

## Declaring a listener type

`listener_type.py` declares the transport family name:

```python
from consortium.framework.listeners import BaseListenerType


class ListenerType(BaseListenerType):
    name = "tcp_json"
```

`name` is the only required attribute. It must be a non-empty string that is unique
across all listener types in your installation. The framework validates `name` at class
definition time.

Agent templates reference this name in their `compatible_listener_types` set to declare
which listeners they can connect through:

```python
# In an agent template -- links back to the listener type by name
class AgentTemplate(BaseAgentTemplate):
    compatible_listener_types = {"tcp_json"}
```

The framework populates `ListenerType.registered_compatible_agent_types` at load time
with every agent type that declared itself compatible with this listener. This set is
managed entirely by the framework; do not write to it manually.
