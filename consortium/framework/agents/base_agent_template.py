import pathlib
import sys
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from inspect import signature
from typing import get_type_hints

from pydantic import ConfigDict

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
from consortium.framework._components import ComponentMetadata, ComponentMetadataModel
from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.framework_types import (
    JSONObject,
    Primitive,
    PrimitiveCollection,
)
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.framework.options.exceptions import OptionValueValidationError
from consortium.framework.utils.exception_utils import remap_exception
from consortium.server.exceptions.framework_exceptions.agent_templates_framework_exceptions import (  # AgentTemplateConfigurationParameterTypeError,; EmptyAgentTemplateNameError,; RequiredAgentTemplateConfigurationParameterNotDeclaredError,
    AgentTemplateOptionNotFoundError,
    AgentTemplateOptionValueError,
    DuplicateAgentTemplateOptionNameError,
    EmptyAgentTemplateLabelError,
    InvalidAgentTemplateConfigurationParameterTypeError,
    InvalidAgentTemplateDependencyVersionSpecifierError,
    InvalidAgentTemplateVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingAgentTemplateConfigurationParameterError,
)
from consortium.server.utils.formatter_utils import format_docstring_to_single_line

Options = (
    SingleValueOption
    | ChoiceValueOption
    | ListValueOption
    | DictionaryValueOption
    | ToggleableChoicesValueOption
)


class _AgentTemplateModel(ComponentMetadataModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_generator: type[BaseAgentGenerator]
    agent_type: BaseAgentType
    options: set[Options] | None = None
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    ) = None


class BaseAgentTemplate(ComponentMetadata, ABC):
    _METADATA_MODEL = _AgentTemplateModel
    _EXCEPTION_MAP = {
        comp_excs.MissingComponentConfigurationParameterError: MissingAgentTemplateConfigurationParameterError,
        comp_excs.EmptyComponentLabelError: EmptyAgentTemplateLabelError,
        comp_excs.InvalidComponentVersionError: InvalidAgentTemplateVersionError,
        comp_excs.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        comp_excs.InvalidComponentDependencyVersionSpecifierError: InvalidAgentTemplateDependencyVersionSpecifierError,
        comp_excs.InvalidComponentConfigurationParameterTypeError: InvalidAgentTemplateConfigurationParameterTypeError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_str": "agent_template_str",
        "component_filepath": "agent_template_filepath",
    }

    agent_generator: type[BaseAgentGenerator]
    agent_type: BaseAgentType
    options: set[Options] | None = None
    validating_function: Callable[[dict[str, Options]], None] | None = None

    def __init_subclass__(cls, **kwargs):
        cls.options = cls.options or set()
        cls.agent_project_folder = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]

        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=cls._EXCEPTION_MAP,
                exception_kwargs_map=cls._EXCEPTION_KWARGS_MAP,
            ) from None

        # Check that options do not have duplicate names.
        option_names = []
        for option in cls.options:
            if option.name in option_names:
                raise DuplicateAgentTemplateOptionNameError(
                    option_name=option.name,
                    agent_template_str=cls.name,
                )
            option_names.append(option.name)

        # Check that signature of function is minimally valid.
        if cls.validating_function:
            function_signature = signature(cls.validating_function)
            if len(function_signature.parameters) != 1:
                raise InvalidAgentTemplateConfigurationParameterTypeError(
                    agent_template_str=cls.name,
                    parameter_name="validating_function",
                    parameter_type=get_type_hints(cls)["validating_function"],
                )
            # We need to convert the validating function to a static method so that the
            # validating function class attribute is considered as just an ordinary
            # function rather than an actual method of the agent template.
            cls.validating_function = staticmethod(cls.validating_function)

        cls.agent_template_id = uuid.uuid4()
        # Remap options set to a dictionary for easier access by name.
        cls.options = {option.name: option for option in cls.options}
        # TODO: Remove this same stupid fuckass hack as the listener template
        cls.agent_generator.creating_agent_template = cls()
        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.agent_template_id)})"

    def __repr__(self) -> str:
        options_string = "{" + ", ".join(repr(option) for option in self.options) + "}"
        return (
            f"AgentTemplate("
            f"agent_template_id={self.agent_template_id!r}, "
            f"label={self.label!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"version={self.version!r}, "
            f"compatible_framework_version={self.compatible_framework_version!r}, "
            f"authors={self.authors!r}, "
            f"component_dependencies={self.component_dependencies!r}, "
            f"agent_generator={self.agent_generator!r}, "
            f"options={options_string}, "
            f"validating_function={self.validating_function!r}"
            f")"
        )

    @abstractmethod
    def resolve_agent_generator_name(
        self,
        parameters: dict[str, Primitive | PrimitiveCollection],
    ) -> str:
        """
        Function to resolve the name of a newly created agent generator.

        This name can be a default hard-coded value, randomly generated or computed
        from its provided set of parameters (typically from a 'name' parameter).
        """

    def create_agent_generator(
        self,
        name: str | None = None,
        description: str = "",
        parameters: dict[str, Primitive | PrimitiveCollection] | None = None,
    ) -> BaseAgentGenerator:
        """
        Create an agent generator instance from this agent template using the provided
        `name`, `description` and configuration `parameters`.

        If a name is not provided, it will be resolved from the agent template's
        `resolve_name_endpoint` method.
        """
        if parameters is None:
            parameters = {}

        # Fill in default option values for options that were not provided in the
        # parameters dictionary.
        for option_name, option in self.options.items():
            if option_name not in parameters:
                parameters[option_name] = option.default_value

        # Validate entire constructed parameter set before creating the agent generator.
        for option_name, value in parameters.items():
            if option_name not in self.options:
                raise AgentTemplateOptionNotFoundError(
                    agent_template_str=str(self),
                    option_name=option_name,
                )
            try:
                self.options[option_name].validate_value(value)
            except OptionValueValidationError as exc:
                raise AgentTemplateOptionValueError(
                    option_name=option_name,
                    option_value=value,
                    agent_template_str=str(self),
                    error_message=str(exc),
                ) from None

        # Check for missing required options.
        for option_name, option in self.options.items():
            if option.required and option_name not in parameters:
                raise MissingAgentTemplateConfigurationParameterError(
                    agent_template_str=str(self),
                    parameter_name=option_name,
                )

        # Run validation function on the entire set of parameters if one was provided.
        if self.validating_function:
            self.validating_function(parameters)

        # Create agent generator instance. Resolving the name from the parameters only if one
        # was not provided.
        return self.agent_generator(
            name=self.resolve_agent_generator_name(parameters=parameters)
            if name is None
            else name,
            description=description,
            parameters=parameters,
        )

    def to_json(self) -> JSONObject:
        """
        Convert the agent template metadata to a JSON serializable dictionary.
        """
        return {
            "agent_template_id": str(self.agent_template_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": self.authors,
            "component_dependencies": list(map(str, self.component_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "agent_type": self.agent_generator.agent_type.to_json(),
            "options": {
                name: option.to_json() for name, option in self.options.items()
            },
            "validating_function": format_docstring_to_single_line(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
        }
