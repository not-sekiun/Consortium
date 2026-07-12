# AgentGenerator and Build Steps

The generator orchestrates a pipeline of `BaseAgentGeneratorBuildStep` classes that
each perform one discrete stage of a build: writing a source template, compiling it,
signing the binary, registering the output artifact. Steps execute sequentially and
share state through a common `environment` `SimpleNamespace`.

## Build steps

Each step subclasses `BaseAgentGeneratorBuildStep` and implements one method: `build()`.
All lifecycle hooks (`on_started`, `on_running`, etc.) are `@final` on build steps and
cannot be overridden. `build()` is the only customisation point.

```python
from consortium.framework.agents import BaseAgentGeneratorBuildStep
from consortium.framework.signal_exceptions import AgentGeneratorBuildStepRuntimeError


class BuildScript(BaseAgentGeneratorBuildStep):
    name = "Build Script"
    description = "Configure and write the agent Python script."

    async def build(self, parameters: dict) -> None:
        # self.working_directory is a pathlib.Path to this source file's parent
        template_path = self.working_directory / "agent_source" / "agent.py"
        source = template_path.read_text()

        source = source.replace(
            'REMOTE_HOST = "127.0.0.1"',
            f'REMOTE_HOST = {repr(parameters["remote_host"])}',
        ).replace(
            "REMOTE_PORT = 4444",
            f"REMOTE_PORT = {repr(parameters['remote_port'])}",
        )

        if parameters["format"] == "script":
            self.agent_templates_payload_service.create_payload_file(
                build_parameters=parameters,
                content=source,
                name="agent.py",
            )
        elif parameters["format"] == "oneliner":
            self.agent_templates_payload_service.create_payload_file(
                build_parameters=parameters,
                content='python -c "' + repr(source) + '"',
                name="agent.txt",
            )
        else:
            raise AgentGeneratorBuildStepRuntimeError(
                f"Unknown format '{parameters['format']}' specified.",
            )
```

`AgentGeneratorBuildStepRuntimeError` is the signal exception for recoverable build
failures. Raising it transitions the step to `ERRORED` and propagates the error up to
the generator.

### self.working_directory

`self.working_directory` is a `pathlib.Path` pointing to the directory that contains
the build step's source file. Use it to locate sibling files: source templates, signing
certificates, embedded scripts:

```python
template = self.working_directory / "agent_source" / "agent.py"
cert = self.working_directory / "signing" / "cert.pem"
```

The path is resolved via `inspect.getsourcefile` at instance creation, so it always
points to where the step class was defined, regardless of the working directory at
runtime.

### self.agent_templates_payload_service

Use `self.agent_templates_payload_service` to store build artifacts for later retrieval
via the REST API:

| Method                                                 | Description                                                                 |
|--------------------------------------------------------|-----------------------------------------------------------------------------|
| `create_payload_file(build_parameters, content, name)` | Create a new text file in the payload store; `content` is a string          |
| `add_payload_file(build_parameters, path, name)`       | Copy an existing file from `path` (a `pathlib.Path`) into the payload store |

Both methods require `build_parameters` (the full parameters dict) to tag the artifact
with its provenance. Stored artifacts are retrievable via the REST API after the build
completes.

### Passing state between steps

The `environment` namespace is shared across all steps within one generator run. Write
to it in one step and read from it in the next:

```python
class CompileStep(BaseAgentGeneratorBuildStep):
    name = "Compile"
    async def build(self, parameters):
        # ... compile the binary ...
        self.environment.binary_path = output_path   # set for next step

class SignStep(BaseAgentGeneratorBuildStep):
    name = "Sign"
    async def build(self, parameters):
        binary = self.environment.binary_path        # read from previous step
```

## AgentGenerator

`AgentGenerator` declares the ordered list of step classes. The `on_running()` method
is `@final` on `BaseAgentGenerator` and drives the pipeline automatically; do not
override it. Override `on_started()` to run pre-build validation:

```python
import shutil

from consortium.framework.agents import BaseAgentGenerator
from consortium.framework.signal_exceptions import AgentGeneratorStartError

from .build_steps import BuildScript


class AgentGenerator(BaseAgentGenerator):
    agent_generator_build_steps = [BuildScript]

    async def on_started(self) -> None:
        if (
                self.parameters["format"] == "executable"
                and shutil.which("pyinstaller") is None
        ):
            raise AgentGeneratorStartError(
                "format='executable' requires PyInstaller, but it was not found on PATH."
            )

    async def on_completed(self) -> None:
        self.logger.success(
            "Build complete. {} step(s) executed.",
            len(self.agent_generator_build_steps),
        )
```

`AgentGeneratorStartError` transitions the generator back to `INITIALIZED` before any
steps run. Use it to fail fast on missing tools or invalid parameter combinations that
would cause all steps to fail.

### Generator lifecycle hooks

| Hook                           | When it fires                          | Override for                                                    |
|--------------------------------|----------------------------------------|-----------------------------------------------------------------|
| `on_started()`                 | Before build steps begin               | Pre-build validation; fail fast with `AgentGeneratorStartError` |
| `on_running()`                 | **@final** -- do not override          | Drives the step pipeline automatically                          |
| `on_completed()`               | After all steps succeed                | Post-build notifications, cleanup                               |
| `on_stopped()`                 | When stopped before all steps complete | Resource cleanup on early halt                                  |
| `on_cancelled()`               | When cancelled externally              | Resource cleanup on abort                                       |
| `on_errored(error)`            | `AgentGeneratorRuntimeError` raised    | Custom error handling                                           |
| `on_fatal(exc, fatal_context)` | Unhandled exception in any hook        | Last-resort alerting                                            |

## What lives on self

### BaseAgentGeneratorBuildStep

| Attribute                              | Type                            | Description                                              |
|----------------------------------------|---------------------------------|----------------------------------------------------------|
| `self.name`                            | `str`                           | Step name (class attribute); unique within the generator |
| `self.parameters`                      | `dict`                          | Generator parameters forwarded from the owning generator |
| `self.environment`                     | `SimpleNamespace`               | Shared namespace across all steps in one run             |
| `self.working_directory`               | `pathlib.Path`                  | Directory containing this step's source file             |
| `self.agent_templates_payload_service` | `AgentTemplatesPayloadsService` | Storage for build artifacts                              |
| `self.logger`                          | `loguru.Logger`                 | Step-scoped logger                                       |
| `self.datetime_started`                | `datetime \| None`              | Set when the step starts                                 |
| `self.datetime_stopped`                | `datetime \| None`              | Set when the step ends                                   |
| `self.time_elapsed_in_seconds`         | `float \| None`                 | Property: wall-clock duration of the most recent run     |

### BaseAgentGenerator

| Attribute                          | Type                | Description                                            |
|------------------------------------|---------------------|--------------------------------------------------------|
| `self.agent_generator_id`          | `uuid.UUID`         | Unique identifier for this generator instance          |
| `self.name`                        | `str`               | Display name set at creation time                      |
| `self.description`                 | `str`               | Description set at creation time                       |
| `self.parameters`                  | `dict`              | Resolved option values from the template               |
| `self.agent_generator_build_steps` | `list`              | Step class list declared at class level                |
| `self.environment`                 | `SimpleNamespace`   | Shared mutable namespace across all steps              |
| `self.datetime_created`            | `datetime`          | Creation timestamp                                     |
| `self.stop_event`                  | `asyncio.Event`     | Set when `stop()` is called                            |
| `self.status`                      | `Status`            | Lifecycle status                                       |
| `self.logger`                      | `loguru.Logger`     | Generator-scoped logger                                |
| `self.services`                    | namespace           | All framework services                                 |
| `self.creating_agent_template`     | `BaseAgentTemplate` | Template that created this generator (class attribute) |
