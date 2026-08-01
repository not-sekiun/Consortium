# Complete Agent Profile

Bringing all profile files together for the Recon Agent. This is the full source for a
minimal but complete agent profile.

## agent_type.py

```python
from consortium.framework.agents import (
    BaseAgentCapability,
    BaseAgentType,
    Failure,
    Success,
)
from consortium.framework.options import SingleValueOption

class InfoCapability(BaseAgentCapability):
    name = "info"
    description = "Return basic system information from the agent."
    authors = {"Your Name"}


class ShellCapability(BaseAgentCapability):
    name = "shell"
    description = "Execute a shell command on the agent."
    authors = {"Your Name"}
    options = {
        SingleValueOption(
            name="command",
            description="Shell command to execute.",
            required=True,
            value_type=str,
        ),
    }


class DownloadCapability(BaseAgentCapability):
    name = "download"
    description = "Download a file from the agent."
    authors = {"Your Name"}
    options = {
        SingleValueOption(
            name="source",
            description="Path on the agent to download.",
            required=True,
            value_type=str,
        ),
    }

    async def on_execute(self) -> Success | Failure | None:
        header = await self.recv_from_agent()
        if not header.success:
            return Failure(task_output_message=header)
        chunks = []
        while True:
            msg = await self.recv_from_agent()
            if not msg.success:
                return Failure(task_output_message=msg)
            if msg.data.get("type") == "chunk":
                chunks.append(msg.payload.data)
            elif msg.data.get("type") == "end_of_transfer":
                break
        self.event_logger.artifact(message=f"Downloaded '{header.data['path']}'")
        return Success(message="Download complete.")


class AgentType(BaseAgentType):
    name = "recon_agent"
    agent_capabilities = {
        InfoCapability,
        ShellCapability,
        DownloadCapability,
    }
```

## agent_generator.py

```python
from consortium.framework.agents import BaseAgentGenerator, BaseAgentGeneratorBuildStep
from consortium.framework.signal_exceptions import AgentGeneratorBuildStepRuntimeError


class BuildScript(BaseAgentGeneratorBuildStep):
    name = "Build Script"
    description = "Write the configured agent Python script."

    async def build(self, parameters: dict) -> None:
        template = (self.root_directory / "agent_source" / "agent.py").read_text()
        source = template.replace(
            'REMOTE_HOST = "127.0.0.1"',
            f'REMOTE_HOST = {repr(parameters["remote_host"])}',
        ).replace(
            "REMOTE_PORT = 4444",
            f"REMOTE_PORT = {repr(parameters['remote_port'])}",
        )
        await self.agent_templates_payload_service.create_payload_file(
            build_parameters=parameters,
            content=source,
            name="agent.py",
        )


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [BuildScript]
```

## agent_template.py

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
    agent_type = AgentType
    compatible_listener_types = {"tcp_json"}

    options = {
        SingleValueOption(
            name="remote_host",
            description="Listener host address.",
            required=False,
            default_value="127.0.0.1",
            value_type=str,
        ),
        SingleValueOption(
            name="remote_port",
            description="Listener port.",
            required=False,
            default_value=4444,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=65535,
        ),
    }
```

## Further examples

`consortium/components/agents/consortium/http/` is the most complete reference
implementation. Beyond the basic pattern above, it demonstrates:

- Multiple factory-generated capabilities with custom `task_handler`, `result_handler`,
  and `timeout_handler` functions
- `DownloadCapability` and `UploadCapability` as custom `BaseAgentCapability` subclasses
  with multi-message `on_execute()` and streaming binary payloads
- Using `asyncio.create_subprocess_exec` inside a build step to invoke PyInstaller for
  compiling an executable, with proper error handling
- `on_started()` in the generator to check for required external tools before the
  pipeline begins
- `on_launch()` stripping server-side arguments before they reach the agent
