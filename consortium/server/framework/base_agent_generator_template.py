import uuid
from typing import Any, Callable, Type

from consortium.server.framework.base_agent_generator import BaseAgentGenerator
from consortium.server.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
)
from consortium.server.framework.types import AgentType


class BaseAgentGeneratorTemplate:
    def __init__(
        self,
        agent_generator: Type[BaseAgentGenerator],
        agent_type: AgentType,
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
        options_validation_function: Callable | None = None,
    ):
        self.agent_type = agent_type
        self.agent_generator = agent_generator
        self.name = name
        self.description = description
        self.authors = authors
        names = []
        for option in options:
            if option.name in names:
                raise ValueError(
                    f"The option being registered with name {option.name} could not be registered because an option of the same name has already been registered. Duplicate named options are not allowed",
                )
            names.append(option.name)
        if options is None:
            options = []
        self.options = {option.name: option for option in options}
        self.options_validation_function = options_validation_function

        self.agent_template_id = uuid.uuid4().hex

    def set_option_value(self, name: str, value: Any) -> None:
        if option := self.options.get(name):
            option.set_option_value(value)
            return
        raise ValueError(f"Invalid option name: {name}")

    def clear_option_value(self, name: str) -> None:
        if option := self.options.get(name):
            option.clear_option_value()
            return
        raise ValueError(f"Invalid option name: {name}")

    def clear_all_options_values(self):
        for option in self.options.values():
            option.clear_option_value()

    def create_agent_generator(self) -> BaseAgentGenerator:
        if self.options_validation_function:
            self.options_validation_function(self.options)

        return self.agent_generator(options=self.options)

    def to_json(self):
        agent_template_json = {
            "agent_template_id": self.agent_template_id,
            "agent_type": self.agent_type.to_json(),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "options_validation_function_present": (
                True if self.options_validation_function else False
            ),
            "options_validation_function_description": (
                self.options_validation_function.__doc__
                if self.options_validation_function
                else None
            ),
            "options": {
                option_name: option.to_json()
                for option_name, option in self.options.items()
            },
        }
        return agent_template_json
