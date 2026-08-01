# ListenerTemplate

`ListenerTemplate` is the configuration schema and factory for `Listener` instances. It
declares what parameters an operator must supply when creating a listener, validates
them, and derives the listener's network endpoint.

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
}
```

The framework converts the set into a name-keyed dict at class definition time. Options
with `required=True` and no `default_value` must always be supplied by the caller.
Options with a `default_value` are filled in automatically when missing.

Options configure the listener. They do **not** supply its display name or description:
those are separate metadata arguments to `create_listener()`, described in
[Naming a listener](#naming-a-listener) below. A template may still declare an option
called `name` or `description` if that is genuinely a parameter of the listener it
builds, and the framework will treat it as an ordinary option with no special meaning.

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
from consortium.framework.signal_exceptions import OptionValueValidationError


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

## Resolving the endpoint

`resolve_listener_endpoint` is an abstract method that every template must implement:

```python
def resolve_listener_endpoint(self, parameters: dict) -> str:
    return f"tcp://{parameters['local_host']}:{parameters['local_port']}"
```

It is always called when a listener is created, and the returned string becomes
`self.endpoint` on the listener instance. An endpoint uniquely identifies the address
the listener can be reached at, so deriving it from the parameters is the whole point.

## Naming a listener

A listener's name and description are display metadata and are **never** derived from
its parameters. `create_listener()` takes them as arguments in their own right,
separately from `parameters`:

```python
listener = listener_template.create_listener(
    name="Edge TCP listener",          # omit or pass None for a generated name
    description="external perimeter",
    parameters={"local_host": "0.0.0.0", "local_port": 8443},
)
```

When `name` is `None` the listener generates a random human-readable name for itself.
There is no template hook for supplying a default: a name is either explicit or
generated. Consequently, updating a listener's parameters later never changes its name,
and two listeners built from identical parameters are still told apart by their names.

The fully assembled `ListenerTemplate` is shown in
[Complete Listener Profile](complete-listener-profile.md).

Continue to [The Agent-Listener Protocol](listener-protocol.md) to see what the
`Listener` class must accomplish.
