import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable, Type

from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.framework_types import ListenerType
from consortium.server.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
)


class BaseListenerTemplate(ABC):
    def __init__(
        self,
        listener: Type[BaseListener],
        listener_type: ListenerType,
        name: str = "",
        description: str = "",
        authors: list[str] | None = None,
        options: (
            list[
                SingleValueOption
                | ListValueOption
                | ChoiceValueOption
                | DictionaryValueOption
            ]
            | None
        ) = None,
        validating_function: Callable | None = None,
    ):
        self.name = name
        self.description = description
        self.listener_type = listener_type
        if authors is None:
            self.authors = []
        else:
            self.authors = authors
        names = []
        for option in options:
            if option.name in names:
                raise ValueError(
                    f"The option being registered with name {option.name} could not be registered because an option of the same name has already been registered. Duplicate named options are not allowed",
                )
            names.append(option.name)
        if options is None:
            self.options = {}
        else:
            self.options = {option.name: option for option in options}
        self.listener_template_id = uuid.uuid4()
        self.validating_function = validating_function
        self.listener = listener

    @abstractmethod
    def resolve_listener_name(self) -> str:
        """
        Function that resolves the name of the listener. The name typically should be
        provided as an SingleOption object within the options list parameter of
        __init__() but it can be generated in any other way.
        """

    @abstractmethod
    def resolve_listener_endpoint(self) -> str:
        """
        Function that resolves the endpoint of the listener. The endpoint is a
        human-readable string that uniquely represents the network node that the
        listener is on. This is typically (but not always) the socket address of the
        listener as provided within the options list parameter of __init__()
        """

    def set_option_value(self, option_name: str, option_value: Any) -> None:
        self.options[option_name].set_option_value(option_value)

    def clear_option_value(self, option_name: str) -> None:
        self.options[option_name].clear_option_value()

    def clear_all_options_values(self):
        for option in self.options.values():
            option.clear_option_value()

    def create_listener(self) -> BaseListener:
        if self.validating_function:
            self.validating_function(self.options)

        return self.listener(
            name=self.resolve_listener_name(),
            endpoint=self.resolve_listener_endpoint(),
            listener_type=self.listener_type,
            options=self.options,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "listener_type": self.listener_type.to_json(),
            "authors": self.authors,
            "options": {
                option_name: option.to_json()
                for option_name, option in self.options.items()
            },
            "listener_template_id": str(self.listener_template_id),
            "validating_function": (
                self.validating_function.__doc__ if self.validating_function else None
            ),
        }
