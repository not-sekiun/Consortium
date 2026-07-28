# AgentType

`AgentType` groups all capabilities belonging to a single agent family under one name.
It is what the framework uses to resolve which capabilities are available when an agent
of that type connects and receives tasks.

## Declaring an agent type

```python
from consortium.framework.agents import BaseAgentType

from .agent_capabilities import (
    DownloadCapability,
    InfoCapability,
    PingCapability,
    ShellCapability,
)


class AgentType(BaseAgentType):
    name = "recon_agent"
    agent_capabilities = {
        InfoCapability,
        ShellCapability,
        PingCapability,
        DownloadCapability,
    }
```

`name` is the type identifier used during agent registration. An agent binary that
self-identifies by type passes `agent_type="recon_agent"` in its registration message.
Agents generated from a payload use their `payload_id` instead, which the framework
resolves to the correct type automatically.

`agent_capabilities` is declared as a set of capability classes. The framework converts
it to a name-keyed dict at class definition time, keyed by each capability's `name`
attribute. Task dispatch looks up capabilities by name from this dict.

## Required attributes

| Attribute            | Type  | Required | Description                                    |
|----------------------|-------|----------|------------------------------------------------|
| `name`               | `str` | Yes      | Unique type identifier across the installation |
| `agent_capabilities` | `set` | Yes      | All capabilities this agent type supports      |

`name` must be non-empty; the framework validates that at class definition time. During
profile loading it also resolves the registered agent types and rejects two distinct
agent type classes that use the same name.
