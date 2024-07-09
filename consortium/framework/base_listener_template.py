import sys
import uuid
from abc import ABC, abstractmethod
from inspect import signature
from typing import Any, Callable, Type

from consortium.framework.base_listener import BaseListener
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.server.exceptions.framework_exceptions.listener_template_framework_exceptions import (
    DuplicateListenerTemplateOptionNameError,
    EmptyListenerTemplateNameError,
    ListenerTemplateConfigurationParameterTypeError,
    ListenerTemplateOptionNotFoundError,
    ListenerTemplateOptionValueError,
    RequiredListenerTemplateConfigurationParameterNotDeclaredError,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.utils.formatter_utils import format_docstring_to_single_line

OptionType = (
    SingleValueOption
    | ChoiceValueOption
    | ListValueOption
    | DictionaryValueOption
    | ToggleableChoicesValueOption
)


class BaseListenerTemplate(ABC):
    listener: Type[BaseListener]
    name: str
    description: str = ""
    authors: set[str] | None = None
    options: set[OptionType] | None = None
    validating_function: Callable[[dict[str, OptionType]], None] | None = None

    def __init__(self):
        self.listener_template_id = uuid.uuid4()

    def __init_subclass__(cls, **kwargs):
        # Check the existence of a provided listener template name first so that we can
        # reference the listener template name for every other error message.
        if not hasattr(cls, "name"):
            raise RequiredListenerTemplateConfigurationParameterNotDeclaredError(
                parameter_name="name",
                # Since the listener template cannot be identified by name we identify
                # it by the filepath it was declared in.
                listener_template_str=sys.modules[cls.__module__].__file__,
            )
        if not isinstance(cls.name, str):
            raise ListenerTemplateConfigurationParameterTypeError(
                listener_template_str=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyListenerTemplateNameError(
                listener_template_filepath=sys.modules[cls.__module__].__file__,
            )

        if not hasattr(cls, "listener"):
            raise RequiredListenerTemplateConfigurationParameterNotDeclaredError(
                parameter_name="listener",
                listener_template_str=cls.name,
            )

        if cls.authors is None:
            cls.authors = set()
        if cls.options is None:
            cls.options = set()
        option_names = []
        for option in cls.options:
            if not isinstance(
                option,
                (
                    SingleValueOption,
                    ChoiceValueOption,
                    ListValueOption,
                    DictionaryValueOption,
                    ToggleableChoicesValueOption,
                ),
            ):
                raise ListenerTemplateConfigurationParameterTypeError(
                    error_message=(
                        "The elements of the options set provided must be option "
                        f"objects for listener template '{cls.name}'."
                    ),
                )
            if option.name in option_names:
                raise DuplicateListenerTemplateOptionNameError(
                    option_name=option.name,
                    listener_template_str=cls.name,
                )
            option_names.append(option.name)

        if not isinstance(cls.description, str):
            raise ListenerTemplateConfigurationParameterTypeError(
                listener_template_str=cls.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(cls.authors, set):
            raise ListenerTemplateConfigurationParameterTypeError(
                listener_template_str=cls.name,
                parameter_name="authors",
                parameter_type="set",
            )
        for author in cls.authors:
            if not isinstance(author, str):
                raise ListenerTemplateConfigurationParameterTypeError(
                    error_message=(
                        "The elements in the authors set must be strings for listener "
                        f"template '{cls.name}'."
                    ),
                )
        if cls.validating_function:
            if not isinstance(cls.validating_function, Callable):
                raise ListenerTemplateConfigurationParameterTypeError(
                    "The validating function provided must be a callable function for "
                    f"listener template '{cls.name}'.",
                )
            function_signature = signature(cls.validating_function)
            if len(function_signature.parameters) != 1:
                raise ListenerTemplateConfigurationParameterTypeError(
                    "The validating function provided must accept exactly one "
                    f"parameter for listener template '{cls.name}'.",
                )
            # We need to convert the validating function to a static method so that the
            # validating function class attribute is considered as just an ordinary
            # function rather than an actual method of the listener template.
            cls.validating_function = staticmethod(cls.validating_function)

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({str(self.listener_template_id)})"

    def __repr__(self) -> str:
        options_string = "{" + ", ".join(repr(option) for option in self.options) + "}"
        return (
            f"ListenerTemplate(listener={self.listener!r}, "
            f"name={self.name!r}, description={self.description!r}, "
            f"authors={self.authors!r}, options={options_string}, "
            f"validating_function={self.validating_function!r})"
        )

    @abstractmethod
    def resolve_listener_name(self) -> str:
        """
        Function that resolves the name of the listener. The name typically should be
        provided as an `SingleValueOption` object.
        """

    @abstractmethod
    def resolve_listener_endpoint(self) -> str:
        """
        Function that resolves the endpoint of the listener. The endpoint is a
        human-readable string that uniquely represents the network node that the
        listener is on. This is typically (but not always) the socket address of the
        listener as provided within the options list parameter of __init__().
        """

    def get_option_by_option_name(self, option_name: str) -> OptionType:
        for option in self.options:
            if option.name == option_name:
                return option
        raise ListenerTemplateOptionNotFoundError(
            option_name=option_name,
            listener_template_str=str(self),
        )

    def set_option_value_by_option_name(
        self,
        option_name: str,
        option_value: Any,
    ) -> None:
        option = self.get_option_by_option_name(option_name)

        try:
            option.set_option_value(option_value)
        except OptionValueValidationError as exc:
            raise ListenerTemplateOptionValueError(
                option_name=option_name,
                option_value=option_value,
                listener_template_str=str(self),
                error_message=str(exc),
            )

    def clear_option_value_by_option_name(self, option_name: str) -> None:
        option = self.get_option_by_option_name(option_name)
        option.clear_option_value()

    def clear_all_options_values(self):
        for option in self.options:
            option.clear_option_value()

    def create_listener(
        self,
        name: str | None = None,
        description: str = "",
    ) -> BaseListener:
        if self.validating_function:
            self.validating_function({option.name: option for option in self.options})

        if name is None:
            name = self.resolve_listener_name()

        return self.listener(
            name=name,
            description=description,
            endpoint=self.resolve_listener_endpoint(),
            parameters={
                option.name: option.get_option_value() for option in self.options
            },
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "listener_template_id": str(self.listener_template_id),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "options": {option.name: option.to_json() for option in self.options},
            "validating_function": format_docstring_to_single_line(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
            "listener_type": self.listener.listener_type.to_json(),
        }
