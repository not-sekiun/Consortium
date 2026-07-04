# ListenerTemplate

`ListenerTemplate` is the configuration schema and factory for `Listener` instances. It
declares what parameters an operator must supply when creating a listener, validates
them, and derives the listener's display name and network endpoint.

## Required class attributes

```python
from consortium.framework.listeners import BaseListenerTemplate

from .listener import Listener
from .listener_type import ListenerType


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.tcp_json"    # unique dotted identifier
    name = "TCP JSON Listener"                 # human-readable display name
    description = "..."
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}

    listener      = Listener      # class to instantiate -- not an instance
    listener_type = ListenerType  # transport family tag -- not an instance
```

`listener` and `listener_type` are the two framework-required class attributes. Both
must be the classes themselves, not instances. The framework sets
`creating_listener_template` on the `Listener` class at load time to link the template
back to the instance that produced it.

## Options

Options declare the parameters an operator must supply when creating a listener
instance.
They are validated when `create_listener()` is called. Declare them as a set assigned
to the `options` class attribute:

```python
from consortium.framework.options import SingleValueOption

options = {
    SingleValueOption(
        name="local_host",
        description="IP address to bind the TCP server to.",
        required=True,
        default_value="0.0.0.0",
        value_type=str,
    ),
    SingleValueOption(
        name="local_port",
        description="TCP port to listen on.",
        required=True,
        default_value=4444,
        value_type=int,
        greater_than_or_equal_to=1,
        less_than_or_equal_to=65535,
    ),
    SingleValueOption(
        name="name",
        description="Display name for this listener instance.",
        required=True,
        default_value="",
        value_type=str,
    ),
}
```

The framework converts the set into a name-keyed dict at class definition time. Options
with `required=True` and no `default_value` must always be supplied by the caller.
Options with a `default_value` are filled in automatically when missing.

### Available option types

| Option class                   | Value type                    | Key constraints                                                                                            |
|--------------------------------|-------------------------------|------------------------------------------------------------------------------------------------------------|
| `SingleValueOption`            | `str`, `int`, `float`, `bool` | `greater_than`, `less_than`, `minimum_length`, `maximum_length`, `validating_regex`, `validating_function` |
| `ListValueOption`              | List of primitive             | `allow_duplicates`, `validating_regex`, `validating_function` per element                                  |
| `ChoiceValueOption`            | One of a set of strings       | `available_values`                                                                                         |
| `DictionaryValueOption`        | `dict[str, primitive]`        | `value_type` for all values                                                                                |
| `ToggleableChoicesValueOption` | Subset of declared choices    | `available_values`                                                                                         |

## Cross-field validation

When validation requires inspecting multiple options together, provide a
`validating_function`. It receives the complete resolved parameters dict after all
individual option validations have passed:

```python
from consortium.framework.exceptions import OptionValueValidationError


def _validate_loopback_warning(parameters: dict) -> None:
    if parameters["local_host"] != "127.0.0.1" and parameters["local_port"] < 1024:
        raise OptionValueValidationError(
            "Ports below 1024 require root on non-loopback interfaces. "
            "Use a port >= 1024 or bind to 127.0.0.1.",
        )


class ListenerTemplate(BaseListenerTemplate):
    ...
    validating_function = _validate_loopback_warning
```

The function takes the full parameters dict and must raise `OptionValueValidationError`
on failure. The framework converts it to a `@staticmethod` automatically.

## Resolving name and endpoint

`resolve_listener_name` and `resolve_listener_endpoint` are abstract methods that every
template must implement:

```python
def resolve_listener_name(self, parameters: dict) -> str:
    return parameters["name"]

def resolve_listener_endpoint(self, parameters: dict) -> str:
    return f"tcp://{parameters['local_host']}:{parameters['local_port']}"
```

`resolve_listener_name` is called when no explicit name is provided to
`create_listener()`. `resolve_listener_endpoint` is always called; the returned string
becomes `self.endpoint` on the listener instance.

## Complete template

```python
from consortium.framework.exceptions import OptionValueValidationError
from consortium.framework.listeners import BaseListenerTemplate
from consortium.framework.options import SingleValueOption

from .listener import Listener
from .listener_type import ListenerType


def _validate_loopback_warning(parameters: dict) -> None:
    if parameters["local_host"] != "127.0.0.1" and parameters["local_port"] < 1024:
        raise OptionValueValidationError(
            "Ports below 1024 require root on non-loopback interfaces. "
            "Use a port >= 1024 or bind to 127.0.0.1.",
        )


class ListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.tcp_json"
    name = "TCP JSON Listener"
    description = (
        "A raw TCP listener that exchanges newline-delimited JSON messages "
        "with connected agents."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Your Name"}

    listener      = Listener
    listener_type = ListenerType
    validating_function = _validate_loopback_warning
    options = {
        SingleValueOption(
            name="local_host",
            description="IP address to bind the TCP server to.",
            required=True,
            default_value="0.0.0.0",
            value_type=str,
        ),
        SingleValueOption(
            name="local_port",
            description="TCP port to listen on.",
            required=True,
            default_value=4444,
            value_type=int,
            greater_than_or_equal_to=1,
            less_than_or_equal_to=65535,
        ),
        SingleValueOption(
            name="name",
            description="Display name for this listener instance.",
            required=True,
            default_value="",
            value_type=str,
        ),
    }

    def resolve_listener_name(self, parameters: dict) -> str:
        return parameters["name"]

    def resolve_listener_endpoint(self, parameters: dict) -> str:
        return f"tcp://{parameters['local_host']}:{parameters['local_port']}"
```
