import sys
import uuid
from abc import ABC, abstractmethod
from inspect import signature
from typing import Any, Callable, Type

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.framework.options.exceptions import OptionValueValidationError
from consortium.server.exceptions.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplateConfigurationParameterTypeError,
    AgentTemplateOptionNotFoundError,
    AgentTemplateOptionValueError,
    DuplicateAgentTemplateOptionNameError,
    EmptyAgentTemplateNameError,
    RequiredAgentTemplateConfigurationParameterNotDeclaredError,
)
from consortium.server.utils.formatter_utils import format_docstring_to_single_line

OptionType = (
    SingleValueOption
    | ChoiceValueOption
    | ListValueOption
    | DictionaryValueOption
    | ToggleableChoicesValueOption
)


class BaseAgentTemplate(ABC):
    agent_generator: Type[BaseAgentGenerator]
    name: str
    description: str = ""
    authors: set[str] | None = None
    options: set[OptionType] | None = None
    validating_function: Callable[[dict[str, OptionType]], None] | None = None

    def __init_subclass__(cls, **kwargs):
        # Check the existence of a provided agent template name first so that we can
        # reference the agent template name for every other error message.
        if not hasattr(cls, "name"):
            raise RequiredAgentTemplateConfigurationParameterNotDeclaredError(
                parameter_name="name",
                # Since the agent template cannot be identified by name we identify
                # it by the filepath it was declared in.
                agent_template=sys.modules[cls.__module__].__file__,
            )
        if not isinstance(cls.name, str):
            raise AgentTemplateConfigurationParameterTypeError(
                agent_template=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyAgentTemplateNameError(
                agent_template_filepath=sys.modules[cls.__module__].__file__,
            )

        if not hasattr(cls, "agent_generator"):
            raise RequiredAgentTemplateConfigurationParameterNotDeclaredError(
                parameter_name="agent_generator",
                agent_template=cls.name,
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
                raise AgentTemplateConfigurationParameterTypeError(
                    error_message=(
                        "The elements of the options set provided must be option "
                        f"objects for agent template '{cls.name}'."
                    ),
                )
            if option.name in option_names:
                raise DuplicateAgentTemplateOptionNameError(
                    option_name=option.name,
                    agent_template=cls.name,
                )
            option_names.append(option.name)

        if not isinstance(cls.description, str):
            raise AgentTemplateConfigurationParameterTypeError(
                agent_template=cls.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(cls.authors, set):
            raise AgentTemplateConfigurationParameterTypeError(
                agent_template=cls.name,
                parameter_name="authors",
                parameter_type="set",
            )
        for author in cls.authors:
            if not isinstance(author, str):
                raise AgentTemplateConfigurationParameterTypeError(
                    error_message=(
                        "The elements in the authors set must be strings for listener "
                        f"template '{cls.name}'."
                    ),
                )
        if cls.validating_function:
            if not isinstance(cls.validating_function, Callable):
                raise AgentTemplateConfigurationParameterTypeError(
                    "The validating function provided must be a callable function for "
                    f"agent template '{cls.name}'.",
                )
            function_signature = signature(cls.validating_function)
            if len(function_signature.parameters) != 1:
                raise AgentTemplateConfigurationParameterTypeError(
                    "The validating function provided must accept exactly one "
                    f"parameter for agent template '{cls.name}'.",
                )
            # We need to convert the validating function to a static method so that the
            # validating function class attribute is considered as just an ordinary
            # function rather than an actual method of the agent template.
            cls.validating_function = staticmethod(cls.validating_function)

        cls.agent_template_id = uuid.uuid4()
        cls.agent_generator.creating_agent_template = cls

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.agent_template_id)})"

    def __repr__(self) -> str:
        return (
            f"AgentTemplate(agent_generator={self.agent_generator!r}, "
            f"name={self.name!r}, description={self.description!r}, "
            f"authors={self.authors!r}, options={self.options!r}, "
            f"validating_function={self.validating_function!r})"
        )

    @abstractmethod
    def resolve_agent_generator_name(self) -> str:
        """
        Function that resolves the name of the agent generator. The name typically
        should be provided as an SingleOption object within the options list parameter
        of the __init__ method of the agent template.
        """

    def get_option_by_option_name(self, option_name: str) -> OptionType:
        for option in self.options:
            if option.name == option_name:
                return option
        raise AgentTemplateOptionNotFoundError(
            option_name=option_name,
            agent_template=self.name,
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
            raise AgentTemplateOptionValueError(
                option_name=option_name,
                option_value=option_value,
                agent_template=self.name,
                error_message=str(exc),
            )

    def clear_option_value_by_option_name(self, option_name: str) -> None:
        option = self.get_option_by_option_name(option_name)
        option.clear_option_value()

    def clear_all_option_values(self):
        for option in self.options:
            option.clear_option_value()

    def create_agent_generator(
        self,
        name: str | None = None,
        description: str = "",
    ) -> BaseAgentGenerator:
        if self.validating_function:
            self.validating_function({option.name: option for option in self.options})

        if name is None:
            name = self.resolve_agent_generator_name()

        return self.agent_generator(
            name=name,
            description=description,
            parameters={
                option.name: option.get_option_value() for option in self.options
            },
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "agent_template_id": str(self.agent_template_id),
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_generator.agent_type.to_json(),
            "authors": self.authors,
            "options": {option.name: option.to_json() for option in self.options},
            "validating_function": format_docstring_to_single_line(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
        }
