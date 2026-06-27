import sys
from typing import get_type_hints

from pydantic import BaseModel, JsonValue, ValidationError

from consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions import (
    EmptyListenerTypeNameError,
    ListenerTypeConfigurationParameterTypeError,
)


class _BaseListenerTypeModel(BaseModel):
    name: str


class BaseListenerType:
    name: str

    def __init_subclass__(cls, **kwargs):
        cls.registered_compatible_agent_types = set()

        try:
            _BaseListenerTypeModel(
                name=cls.name,
            )
        except ValidationError as exc:
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name=str(exc.errors()[0]["loc"][0]),
                parameter_type=get_type_hints(_BaseListenerTypeModel)[
                    exc.errors()[0]["loc"][0]
                ],
            ) from None

        if not isinstance(cls.name, str):
            raise ListenerTypeConfigurationParameterTypeError(
                listener_type_filepath=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyListenerTypeNameError(
                listener_type_filepath=sys.modules[cls.__module__].__file__,
            )

    def __str__(self) -> str:
        return f"'{self.name}'"

    def __repr__(self) -> str:
        return (
            f"ListenerType("
            f"name={self.name!r}, "
            f"registered_compatible_agent_types={self.registered_compatible_agent_types!r}"
            f")"
        )

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "registered_compatible_agent_types": list(
                self.registered_compatible_agent_types
            ),
        }
