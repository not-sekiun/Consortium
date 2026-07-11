import pathlib
import sys
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from inspect import signature
from typing import get_type_hints

from pydantic import ConfigDict, JsonValue

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentMetadata,
    ComponentMetadataModel,
)
from consortium.framework._core.framework_exceptions import (
    components_framework_exceptions,
)
from consortium.framework._core.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplateOptionNotFoundError,
    AgentTemplateOptionValueValidationError,
    DuplicateAgentTemplateOptionNameError,
    EmptyAgentTemplateLabelError,
    InvalidAgentTemplateConfigurationParameterTypeError,
    InvalidAgentTemplateDependencyVersionSpecifierError,
    InvalidAgentTemplateVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingAgentTemplateConfigurationParameterError,
    MissingRequiredAgentTemplateOptionError,
)
from consortium.framework._utils import format_docstring_to_single_line, remap_exception
from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.framework_types import (
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
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    OptionValueValidationError,
)
from consortium.server.utils import construct_services_dataclass

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
    agent_type: type[BaseAgentType]
    compatible_listener_types: set[str]
    options: set[Options]
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    )


class BaseAgentTemplate(ComponentMetadata, ABC):
    """Abstract base class for agent templates that govern agent generator creation.

    An agent template declares the configuration schema (options, validating function),
    the generator class, agent type, and compatible listener types for a family of
    agent generators. It validates and constructs BaseAgentGenerator instances from
    user-supplied parameters, filling in defaults and running cross-field validation
    before instantiation.

    Attributes:
        agent_generator (type[BaseAgentGenerator]): The generator class that this
            template instantiates when creating a new agent generator.
        agent_type (type[BaseAgentType]): The agent type that identifies which
            capabilities the generated agent supports.
        compatible_listener_types (set[str]): Names of listener types that agents
            generated from this template can connect through.
        options (set[Options]): Configuration options accepted when creating a generator
            from this template. Converted to a name-keyed dict at class definition time.
        validating_function: Optional single-argument callable that validates the full
            set of resolved option values before generator creation.
    """

    _METADATA_MODEL = _AgentTemplateModel

    _COMPONENT_METADATA_EXCEPTION_MAP = {
        components_framework_exceptions.MissingComponentConfigurationParameterError: MissingAgentTemplateConfigurationParameterError,
        components_framework_exceptions.EmptyComponentLabelError: EmptyAgentTemplateLabelError,
        components_framework_exceptions.InvalidComponentVersionError: InvalidAgentTemplateVersionError,
        components_framework_exceptions.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        components_framework_exceptions.InvalidComponentDependencyVersionSpecifierError: InvalidAgentTemplateDependencyVersionSpecifierError,
        components_framework_exceptions.InvalidComponentConfigurationParameterTypeError: InvalidAgentTemplateConfigurationParameterTypeError,
    }
    _COMPONENT_METADATA_EXCEPTION_KWARGS_MAP = {
        "component_str": "agent_template_str",
        "component_filepath": "agent_template_filepath",
    }

    agent_generator: type[BaseAgentGenerator]
    agent_type: type[BaseAgentType]
    compatible_listener_types: set[str] | None = None
    options: set[Options] | None = None
    validating_function: Callable[[dict[str, Options]], None] | None = None

    def __init_subclass__(cls, **kwargs):
        cls.options = cls.options or set()
        cls.agent_project_folder = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]
        cls.compatible_listener_types = cls.compatible_listener_types or set()
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

        try:
            cls._validate_metadata()
        except components_framework_exceptions.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc._kwargs,
                exception_map=cls._COMPONENT_METADATA_EXCEPTION_MAP,
                exception_kwargs_map=cls._COMPONENT_METADATA_EXCEPTION_KWARGS_MAP,
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
            f"agent_type={self.agent_type!r}, "
            f"compatible_listener_types={self.compatible_listener_types!r}, "
            f"options={options_string}, "
            f"validating_function={self.validating_function!r}"
            f")"
        )

    @abstractmethod
    def resolve_agent_generator_name(
        self,
        parameters: dict[str, Primitive | PrimitiveCollection],
    ) -> str:
        """Resolve the display name for a newly created agent generator.

        The name may be a hard-coded default, randomly generated, or derived from one
        of the provided parameters (for example, a dedicated 'name' option).

        Args:
            parameters: The resolved option values provided at generator creation time,
                keyed by option name.

        Returns:
            The display name to assign to the new agent generator instance.
        """

    def create_agent_generator(
        self,
        name: str | None = None,
        description: str = "",
        parameters: dict[str, Primitive | PrimitiveCollection] | None = None,
    ) -> BaseAgentGenerator:
        """Create an agent generator instance from this template using the given configuration.

        Validates all supplied parameters against the declared options, fills in defaults
        for omitted optional options, runs the optional validating_function, then
        instantiates the agent generator. If name is not provided it is resolved via
        resolve_agent_generator_name.

        Args:
            name: Display name for the new generator. If None, the name is derived from
                the parameters using resolve_agent_generator_name.
            description: Optional human-readable description for this generator run.
            parameters: Option values that configure the generator, keyed by option name.
                Missing required options raise an error; missing optional options are
                filled with their declared default values.

        Returns:
            A new BaseAgentGenerator instance configured with the provided parameters.

        Raises:
            MissingRequiredAgentTemplateOptionError: If a required option is absent
                from parameters.
            AgentTemplateOptionNotFoundError: If parameters contains an unknown option name.
            AgentTemplateOptionValueValidationError: If an option value fails type or
                constraint validation.
        """
        if parameters is None:
            parameters = {}

        # Check for missing required options before filling in defaults, so that
        # a required option with default_value=None is caught rather than silently
        # accepted.
        for option_name, option in self.options.items():
            if option.required and option_name not in parameters:
                raise MissingRequiredAgentTemplateOptionError(
                    agent_template_str=str(self),
                    option_name=option_name,
                )

        # Fill in default option values for options that were not provided in the
        # parameters dictionary. For options that do not have a default value
        # they fill in as `None`
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
                option = self.options[option_name]
                # Allow `None` for non-required options
                if value is None and not option.required:
                    continue
                option.validate_value(value)
            except OptionValueValidationError as exc:
                raise AgentTemplateOptionValueValidationError(
                    option_name=option_name,
                    option_value=value,
                    agent_template_str=str(self),
                    error_message=str(exc),
                ) from None

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

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the agent template's full metadata to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the template ID, label, name, description, version,
            framework compatibility, authors, dependencies, agent type, compatible
            listener types, options, and any validating function documentation.
        """
        return {
            "agent_template_id": str(self.agent_template_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": list(self.authors),
            "component_dependencies": list(map(str, self.component_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "agent_type": self.agent_generator.agent_type.to_json(),
            "compatible_listener_types": list(self.compatible_listener_types),
            "options": {
                name: option.to_json() for name, option in self.options.items()
            },
            "validating_function": format_docstring_to_single_line(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
        }

    def to_json_reference(self) -> dict[str, str]:
        """Serialize a compact reference to this agent template.

        Returns:
            A dictionary containing only the template ID, label, and name, suitable
            for embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "agent_template_id": str(self.agent_template_id),
            "label": self.label,
            "name": self.name,
        }
