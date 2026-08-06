import pathlib
import uuid
from collections.abc import Callable
from inspect import signature
from typing import get_type_hints

from pydantic import ConfigDict, JsonValue

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentMetadata,
    ComponentMetadataExceptions,
    ComponentMetadataModel,
)
from consortium.framework._core.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplateOptionNotFoundError,
    AgentTemplateOptionValueValidationError,
    AgentTemplateValidatingFunctionError,
    DuplicateAgentTemplateOptionNameError,
    EmptyAgentTemplateLabelError,
    InvalidAgentTemplateConfigurationParameterTypeError,
    InvalidAgentTemplateDependencyVersionSpecifierError,
    InvalidAgentTemplateVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingAgentTemplateConfigurationParameterError,
    MissingRequiredAgentTemplateOptionError,
)
from consortium.framework._core.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError as OptionValueValidationFrameworkError,
)
from consortium.framework._core.utils import (
    format_docstring_to_single_line,
    resolve_component_filepath,
)
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
from consortium.framework.signal_exceptions.options_signal_exceptions import (
    OptionValueValidationError as OptionValueValidationSignalError,
)
from consortium.server.utils import construct_services_dataclass

type Options = (
    SingleValueOption
    | ChoiceValueOption
    | ListValueOption
    | DictionaryValueOption
    | ToggleableChoicesValueOption
)


class _AgentTemplateMetadataModel(ComponentMetadataModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_generator: type[BaseAgentGenerator]
    # A `str` is an agent type reference: the name of an agent type declared by another
    # agent profile, resolved to that profile's agent type instance after all profiles
    # are loaded. Declaring the type as a class only would reject the reference here, at
    # class definition time, long before there is anything to resolve it against.
    agent_type: type[BaseAgentType] | str
    compatible_listener_types: set[str]
    options: set[Options]
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    )


class BaseAgentTemplate(ComponentMetadata):
    """Abstract base class for agent templates that govern agent generator creation.

    An agent template declares the configuration schema (options, validating function),
    the generator class, agent type, and compatible listener types for a family of
    agent generators. It validates and constructs BaseAgentGenerator instances from
    user-supplied parameters, filling in defaults and running cross-field validation
    before instantiation.

    Attributes:
        agent_generator: The generator class that this template instantiates when
            creating a new agent generator.
        agent_type: The agent type that identifies which capabilities the generated
            agent supports. Either the agent type class, or the name of an agent type
            declared by another agent profile as a string reference to it. Both forms
            are resolved to a shared agent type instance once every agent profile is
            loaded, so this always reads back as a `BaseAgentType` instance at runtime.
        compatible_listener_types: Names of listener types that agents generated from
            this template can connect through.
        options: Configuration options accepted when creating a generator from this
            template. Converted to a name-keyed dict at class definition time.
        validating_function: Optional single-argument callable that validates the full
            set of resolved option values before generator creation.
    """

    _component_metadata_model = _AgentTemplateMetadataModel
    # Raise agent template framework exceptions directly from the shared metadata validation
    # instead of raising generic component exceptions and remapping them in __init_subclass__.
    _component_metadata_exceptions = ComponentMetadataExceptions(
        missing_configuration_parameter=MissingAgentTemplateConfigurationParameterError,
        invalid_configuration_parameter_type=InvalidAgentTemplateConfigurationParameterTypeError,
        empty_label=EmptyAgentTemplateLabelError,
        invalid_version=InvalidAgentTemplateVersionError,
        invalid_framework_version_specifier=InvalidFrameworkVersionSpecifierError,
        invalid_dependency_version_specifier=InvalidAgentTemplateDependencyVersionSpecifierError,
    )

    agent_generator: type[BaseAgentGenerator]
    agent_type: type[BaseAgentType] | str
    compatible_listener_types: set[str] | None = None
    options: set[Options] | None = None
    validating_function: Callable[[dict[str, Options]], None] | None = None

    def __init_subclass__(cls, **kwargs):
        cls.options = cls.options or set()
        cls.root_directory = pathlib.Path(
            resolve_component_filepath(cls),
        ).parents[0]
        cls.compatible_listener_types = cls.compatible_listener_types or set()
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

        cls._validate_metadata()

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
                    component_str=cls.name,
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

    def create_agent_generator(
        self,
        name: str | None = None,
        description: str = "",
        parameters: dict[str, Primitive | PrimitiveCollection] | None = None,
    ) -> BaseAgentGenerator:
        """Create an agent generator instance from this template using the given configuration.

        Validates all supplied parameters against the declared options, fills in defaults
        for omitted optional options, runs the optional validating_function, then
        instantiates the agent generator.

        Args:
            name: Display name for the new generator. If None, a random human-readable
                name is generated. A generator's name is display metadata only: it is
                never derived from `parameters`, and updating parameters later never
                changes it.
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
            AgentTemplateValidatingFunctionError: If the template validating function
                rejects the resolved options.
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
            except OptionValueValidationFrameworkError as exc:
                raise AgentTemplateOptionValueValidationError(
                    option_name=option_name,
                    option_value=value,
                    agent_template_str=str(self),
                    error_message=str(exc),
                ) from None

        # Run validation function on the entire set of parameters if one was provided.
        if self.validating_function:
            try:
                self.validating_function(parameters)
            except OptionValueValidationSignalError as exc:
                raise AgentTemplateValidatingFunctionError(
                    agent_template_str=str(self),
                    error_message=exc.message,
                    detail=exc.detail,
                ) from None

        # Create agent generator instance. The name is passed straight through and the
        # generator generates a random one when it is `None`; it is never resolved from
        # the parameters.
        return self.agent_generator(
            name=name,
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

    def to_json_reference(self) -> dict[str, JsonValue]:
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
