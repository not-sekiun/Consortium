from enum import StrEnum
from typing import get_type_hints

from pydantic import BaseModel, JsonValue, ValidationError

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    EmptyAgentCapabilityChannelNameError,
    InvalidAgentCapabilityChannelConfigurationParameterTypeError,
)
from consortium.framework._core.utils import resolve_validation_error_parameter


class ChannelDirection(StrEnum):
    """Which way bytes travel on a channel, from the client's point of view.

    INPUT carries bytes the client writes towards the capability. OUTPUT carries bytes
    the capability produces towards the client.
    """

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class _ChannelParametersModel(BaseModel):
    name: str
    direction: ChannelDirection
    content_type: str


class Channel:
    """A byte channel a capability declares between itself and an attached client.

    Declared as a class level set on a capability, converted to a name-keyed dict at
    definition time and surfaced through the capability's metadata so a client knows
    what it can attach to. The declaration is inert: it describes a channel rather than
    holding one, and the buffer behind it is created per running task.

    Attributes:
        name: Identifier for the channel, unique within a capability.
        direction: Whether the channel carries bytes towards the capability (INPUT) or
            towards the client (OUTPUT).
        content_type: Hint for how a client should present the bytes. Carried through
            untouched: nothing on the server decodes a channel, so this constrains
            nothing and defaults to `text/plain`.
    """

    def __init__(
        self,
        name: str,
        direction: ChannelDirection,
        content_type: str = "text/plain",
    ):
        """Declare a channel.

        Args:
            name: Identifier for the channel, unique within a capability.
            direction: Whether the channel carries bytes towards the capability (INPUT)
                or towards the client (OUTPUT). Accepted as its string value and
                normalized to the enum.
            content_type: Hint for how a client should present the bytes.

        Raises:
            InvalidAgentCapabilityChannelConfigurationParameterTypeError: If a parameter
                is not of the expected type.
            EmptyAgentCapabilityChannelNameError: If the name is empty.
        """
        try:
            parameters = _ChannelParametersModel(
                name=name,
                direction=direction,
                content_type=content_type,
            )
        except ValidationError as exc:
            parameter_name, parameter_type = resolve_validation_error_parameter(
                exc=exc,
                parameter_types=get_type_hints(_ChannelParametersModel),
            )
            raise InvalidAgentCapabilityChannelConfigurationParameterTypeError(
                channel_str=str(name),
                parameter_name=parameter_name,
                parameter_type=parameter_type,
            ) from None

        if not parameters.name:
            raise EmptyAgentCapabilityChannelNameError()

        self.name = parameters.name
        # Taken off the validated model so a direction given as its string value is
        # normalized: everything downstream only ever sees the enum.
        self.direction = parameters.direction
        self.content_type = parameters.content_type

    def __str__(self) -> str:
        return f"{self.name} ({self.direction})"

    def __repr__(self) -> str:
        return (
            f"Channel("
            f"name={self.name!r}, "
            f"direction={self.direction!r}, "
            f"content_type={self.content_type!r}"
            f")"
        )

    def to_json(self) -> dict[str, JsonValue]:
        """Convert the channel declaration to a JSON serializable dictionary.

        Returns:
            The JSON serializable dictionary representation of the channel.
        """
        return {
            "name": self.name,
            "direction": str(self.direction),
            "content_type": self.content_type,
        }
