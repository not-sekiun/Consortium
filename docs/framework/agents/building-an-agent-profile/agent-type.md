# AgentType

`AgentType` groups all capabilities belonging to a single agent family under one name.
It is what the framework uses to resolve which capabilities are available when an agent
of that type connects and receives tasks.

## Declaring an agent type

```python
from consortium.framework.agents import BaseAgentType

from .agent_type import (   # in practice, declared in the same file
    info_capability,
    shell_capability,
    ping_capability,
    DownloadCapability,
)


class AgentType(BaseAgentType):
    name = "recon_agent"
    agent_capabilities = {
        info_capability,
        shell_capability,
        ping_capability,
        DownloadCapability,
    }
```

`name` is the type identifier used during agent registration. An agent binary that
self-identifies by type passes `agent_type="recon_agent"` in its registration message.
Agents generated from a payload use their `payload_id` instead, which the framework
resolves to the correct type automatically.

`agent_capabilities` is declared as a set of capability classes (or instances returned
by `request_response_capability`). The framework converts it to a name-keyed dict at
class definition time, keyed by each capability's `name` attribute. Task dispatch looks
up capabilities by name from this dict.

## Required attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Unique type identifier across the installation |
| `agent_capabilities` | `set` | Yes | All capabilities this agent type supports |

`name` must be non-empty and unique. The framework validates this at class definition
time.
