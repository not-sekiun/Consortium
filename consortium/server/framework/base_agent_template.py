import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable, Type

from consortium.server.framework.base_agent_generator import BaseAgentGenerator
from consortium.server.framework.c2_types import AgentType
from consortium.server.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
)
from consortium.server.utils.formatter_utils import format_docstring_to_single_line


class BaseAgentTemplate(ABC):
    def __init__(
        self,
        agent_generator: Type[BaseAgentGenerator],
        agent_type: AgentType,
        name: str = "",
        description: str = "",
        authors: list[str] | None = None,
        options: list[
            SingleValueOption
            | ListValueOption
            | ChoiceValueOption
            | DictionaryValueOption
        ]
        | None = None,
        validating_function: Callable | None = None,
    ):
        self.name = name
        self.description = description
        self.agent_type = agent_type
        if authors is None:
            self.authors = []
        else:
            self.authors = authors
        names = []
        for option in options:
            if option.name in names:
                raise ValueError(
                    f"The option being registered with name {option.name} could not be "
                    f"registered because an option of the same name has already been "
                    f"registered. Duplicate named options are not allowed",
                )
            names.append(option.name)
        if options is None:
            self.options = {}
        else:
            self.options = {option.name: option for option in options}
        self.agent_template_id = uuid.uuid4()
        self.validating_function = validating_function
        self.agent_generator = agent_generator

    @abstractmethod
    def resolve_agent_generator_name(self) -> str:
        """
        Function that resolves the name of the agent generator. The name typically
        should be provided as an SingleOption object within the options list parameter
        of the __init__ method of the agent template.
        """

    def set_option_value(self, option_name: str, option_value: Any) -> None:
        self.options[option_name].set_option_value(option_value)

    def clear_option_value(self, option_name: str) -> None:
        self.options[option_name].clear_option_value()

    def clear_all_option_values(self) -> None:
        for option in self.options.values():
            option.clear_option_value()

    def create_agent_generator(self) -> BaseAgentGenerator:
        if self.validating_function:
            self.validating_function(self.options)
        created_agent_generator = self.agent_generator(
            agent_type=self.agent_type,
            agent_template=self,
            name=self.resolve_agent_generator_name(),
            parameters={
                option_name: option.get_option_value()
                for option_name, option in self.options.items()
            },
        )
        return created_agent_generator

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.to_json(),
            "authors": self.authors,
            "options": {
                option_name: option.to_json()
                for option_name, option in self.options.items()
            },
            "agent_template_id": str(self.agent_template_id),
            "validating_function": format_docstring_to_single_line(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.agent_template_id)})'

    def __repr__(self) -> str:
        return (
            f"AgentTemplate(agent_generator={self.agent_generator!r}, "
            f"agent_type={self.agent_type!r}, name={self.name!r}, "
            f"description={self.description!r}, authors={self.authors!r}, "
            f"options={self.options!r}, "
            f"validating_function={self.validating_function!r})"
        )
