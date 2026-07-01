# Agents

An agent profile defines everything the framework needs to generate an agent payload and
handle its commands once deployed. A profile is made up of four cooperating classes that
cover two distinct concerns: how to **build** the agent (the generator and its build
steps), and what the agent can **do** once running (the agent type and its capabilities).

## Agent profile components

| Class | Base | Role |
|---|---|---|
| `AgentType` | `BaseAgentType` | Names the agent family; groups all its executable capabilities |
| `AgentCapability` | `BaseAgentCapability` | A single command the agent can execute |
| `AgentTemplate` | `BaseAgentTemplate` | Configuration schema and factory; creates `AgentGenerator` instances |
| `AgentGenerator` | `BaseAgentGenerator` | Orchestrates a pipeline of `AgentGeneratorBuildStep` classes to produce the deployable agent payload |
| `AgentGeneratorBuildStep` | `BaseAgentGeneratorBuildStep` | One discrete stage in the build pipeline |

The template links everything together:

```python
class AgentTemplate(BaseAgentTemplate):
    ...
    agent_generator = AgentGenerator   # class that builds the payload
    agent_type      = AgentType        # capabilities the generated agent exposes
    compatible_listener_types = {"tcp_json"}  # listener types it can connect through
```

## How agent and listener profiles are linked

`compatible_listener_types` on the agent template is a set of listener type `name`
strings. The framework uses this set to:

1. Validate that an agent generator can be registered against a given listener type.
2. Resolve which agent types a particular listener type can serve.

```python
# Listener type (from listener profile)
class ListenerType(BaseListenerType):
    name = "tcp_json"

# Agent template (from agent profile) -- links to the listener type by name
class AgentTemplate(BaseAgentTemplate):
    compatible_listener_types = {"tcp_json"}
```

## Project structure

Each agent profile lives in its own directory under `consortium/components/agents/`:

```
consortium/components/agents/my_agent/
    manifest.json
    agent_type.py      (declares capabilities and the AgentType)
    agent_template.py  (declares the AgentTemplate)
    agent_generator.py (declares the AgentGenerator and its build steps)
```

`manifest.json` points the loader at the entry class:

```json
{
    "entry_point": "agent_template:AgentTemplate",
    "enabled": true
}
```

The entry point class must be named `AgentTemplate` by convention. Capabilities are
typically declared in the same file as `AgentType` or in a dedicated
`agent_capabilities/` subdirectory.

## Capability dispatch

When an operator tasks an agent with a command, the framework resolves the capability
by matching the task's `command` field against `AgentType.agent_capabilities` (a
name-keyed dict after class definition). The matching `BaseAgentCapability` subclass is
instantiated and its `execute()` method is called. This calls `on_launch()` to send the
task message and `on_execute()` to await and process the agent's response.

## The generator pipeline

An `AgentGenerator` does not define custom `on_running()` behaviour. Instead it
declares an ordered list of `BaseAgentGeneratorBuildStep` classes. The framework drives
each step in sequence, passing the same `parameters` dict and a shared `environment`
`SimpleNamespace` between all steps. Steps communicate through `self.environment`:

```
AgentGenerator.on_started()
  -> step 1: BuildAgent.build(parameters)   # e.g. write script
  -> step 2: SignPayload.build(parameters)  # e.g. sign the binary
  -> step 3: UploadPayload.build(parameters)
AgentGenerator.on_completed()
```

Each build step calls `self.agent_templates_payload_service` to store build artifacts
for later retrieval via the REST API.

## Real-world examples

`consortium/components/agents/consortium/http/` is the canonical reference
implementation. It demonstrates:

- Multiple capabilities using `request_response_capability` with custom `task_handler`
  and `result_handler` callables
- Custom `BaseAgentCapability` subclasses with multi-message `on_execute()` for
  streaming (file download/upload)
- A single-step generator that reads a Python source template, performs string
  replacements for configuration, and outputs a script, oneliner, or PyInstaller
  executable
- `on_started()` on the generator to pre-validate that required tools are present
- `AgentGeneratorStartError` to abort a build before steps execute
