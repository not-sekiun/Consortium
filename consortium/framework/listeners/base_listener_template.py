import pathlib
import sys
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from inspect import signature
from types import NotImplementedType
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
from consortium.framework._core.framework_exceptions.listener_templates_framework_exceptions import (
    DuplicateListenerTemplateOptionNameError,
    EmptyListenerTemplateLabelError,
    InvalidFrameworkVersionSpecifierError,
    InvalidListenerTemplateConfigurationParameterTypeError,
    InvalidListenerTemplateDependencyVersionSpecifierError,
    InvalidListenerTemplateVersionError,
    ListenerTemplateOptionNotFoundError,
    ListenerTemplateOptionValueValidationError,
    MissingListenerTemplateConfigurationParameterError,
    MissingRequiredListenerTemplateOptionError,
)
from consortium.framework._core.framework_exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework._core.utils import (
    format_docstring_to_single_line,
    remap_exception,
)
from consortium.framework.framework_types import (
    Primitive,
    PrimitiveCollection,
)
from consortium.framework.listeners.base_listener import BaseListener
from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.server.utils import construct_services_dataclass

Options = (
    SingleValueOption
    | ChoiceValueOption
    | ListValueOption
    | DictionaryValueOption
    | ToggleableChoicesValueOption
)


class _ListenerTemplateModel(ComponentMetadataModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    listener: type[BaseListener]
    listener_type: type[BaseListenerType]
    options: set[Options] | None = None
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    ) = None


class BaseListenerTemplate(ComponentMetadata, ABC):
    """Abstract base class for listener templates that govern listener creation.

    A listener template declares the configuration schema (options, validating function),
    the listener class, and the listener type for a family of listeners. It validates
    and constructs BaseListener instances from user-supplied parameters, filling in
    defaults and running cross-field validation before instantiation.

    Attributes:
        listener: The listener class this template instantiates when creating a new
            listener.
        listener_type: The listener type that identifies which agent types are
            compatible with listeners created from this template.
        options: Configuration options accepted when creating a listener from this
            template. Converted to a name-keyed dict at class definition time.
        validating_function: Optional single-argument callable that validates the full
            set of resolved option values before listener creation.
    """

    _METADATA_MODEL = _ListenerTemplateModel

    _COMPONENT_METADATA_EXCEPTION_MAP = {
        components_framework_exceptions.MissingComponentConfigurationParameterError: MissingListenerTemplateConfigurationParameterError,
        components_framework_exceptions.EmptyComponentLabelError: EmptyListenerTemplateLabelError,
        components_framework_exceptions.InvalidComponentVersionError: InvalidListenerTemplateVersionError,
        components_framework_exceptions.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        components_framework_exceptions.InvalidComponentDependencyVersionSpecifierError: InvalidListenerTemplateDependencyVersionSpecifierError,
        components_framework_exceptions.InvalidComponentConfigurationParameterTypeError: InvalidListenerTemplateConfigurationParameterTypeError,
    }
    _COMPONENT_METADATA_EXCEPTION_KWARGS_MAP = {
        "component_str": "listener_template_str",
        "component_filepath": "listener_template_filepath",
    }

    listener: type[BaseListener]
    listener_type: type[BaseListenerType]
    options: set[Options] | None = None
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    ) = None

    def __init_subclass__(cls, **kwargs):
        cls.options = cls.options or set()
        cls.listener_project_folder = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]
        cls.registered_compatible_agent_types = set()
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
                raise DuplicateListenerTemplateOptionNameError(
                    option_name=option.name,
                    listener_template_str=cls.name,
                )
            option_names.append(option.name)

        # Check that signature of function is minimally valid.
        if cls.validating_function:
            function_signature = signature(cls.validating_function)
            if len(function_signature.parameters) != 1:
                raise InvalidListenerTemplateConfigurationParameterTypeError(
                    listener_template_str=cls.name,
                    parameter_name="validating_function",
                    parameter_type=get_type_hints(cls)["validating_function"],
                )
            # We need to convert the validating function to a static method so that the
            # validating function class attribute is considered as just an ordinary
            # function rather than an actual method of the listener template.
            cls.validating_function = staticmethod(cls.validating_function)

        cls.listener_template_id = uuid.uuid4()
        # Remap options set to a dictionary for easier access by name.
        cls.options = {option.name: option for option in cls.options}
        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.listener_template_id)})"

    def __repr__(self) -> str:
        options_string = "{" + ", ".join(repr(option) for option in self.options) + "}"
        return (
            f"ListenerTemplate("
            f"listener_template_id={self.listener_template_id!r}, "
            f"label={self.label!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"version={self.version!r}, "
            f"compatible_framework_version={self.compatible_framework_version!r}, "
            f"authors={self.authors!r}, "
            f"component_dependencies={self.component_dependencies!r}, "
            f"listener={self.listener!r}, "
            f"listener_type={self.listener_type!r}, "
            f"registered_compatible_agent_types={self.registered_compatible_agent_types!r}, "
            f"options={options_string}, "
            f"validating_function={self.validating_function!r}"
            f")"
        )

    @abstractmethod
    def resolve_listener_name(
        self,
        parameters: dict[str, Primitive | PrimitiveCollection],
    ) -> str:
        """Resolve the display name for a newly created listener.

        The name may be a hard-coded default, randomly generated, or derived from one
        of the provided parameters (for example, a dedicated 'name' option).

        Args:
            parameters: The resolved option values provided at listener creation time,
                keyed by option name.

        Returns:
            The display name to assign to the new listener instance.
        """

    @abstractmethod
    def resolve_listener_endpoint(
        self,
        parameters: dict[str, Primitive | PrimitiveCollection],
    ) -> str:
        """Resolve the network endpoint for a newly created listener from the given parameters.

        An endpoint is a string that uniquely identifies the address the listener can be
        reached at (for example, "http://127.0.0.1:8000/check-in").

        Args:
            parameters: The resolved option values provided at listener creation time,
                keyed by option name.

        Returns:
            The network endpoint string to assign to the new listener instance.
        """

    # TODO: Implement being able to create agents from a particular listener but only if
    #   this method exists and is overriden otherwise it should be treated as not
    #   possible
    def resolve_agent_parameters_from_listener_parameters(
        self,
        agent_type: str,
        parameters: dict[str, Primitive | PrimitiveCollection],
    ) -> dict[str, Primitive | PrimitiveCollection] | NotImplementedType:
        """Resolve agent parameters from listener parameters.

        Args:
            agent_type: The type of agent for which to resolve parameters.
            parameters: The resolved option values provided at listener creation time,
                keyed by option name.

        Returns:
            A dictionary of agent parameters keyed by parameter name.
        """
        return NotImplemented

    def create_listener(
        self,
        name: str | None = None,
        description: str = "",
        parameters: dict[str, Primitive | PrimitiveCollection] | None = None,
    ) -> BaseListener:
        """Create a listener instance from this template using the given configuration.

        Validates all supplied parameters against the declared options, fills in defaults
        for omitted optional options, runs the optional validating_function, then
        instantiates the listener. If name is not provided it is resolved via
        resolve_listener_name.

        Args:
            name: Display name for the new listener. If None, the name is derived from
                the parameters using resolve_listener_name.
            description: Optional human-readable description for this listener instance.
            parameters: Option values that configure the listener, keyed by option name.
                Missing required options raise an error; missing optional options are
                filled with their declared default values.

        Returns:
            A new BaseListener instance configured with the provided parameters.

        Raises:
            MissingRequiredListenerTemplateOptionError: If a required option is absent
                from parameters.
            ListenerTemplateOptionNotFoundError: If parameters contains an unknown option name.
            ListenerTemplateOptionValueValidationError: If an option value fails type or
                constraint validation.
        """
        if parameters is None:
            parameters = {}

        # Check for missing required options before filling in defaults, so that
        # a required option with default_value=None is caught rather than silently
        # accepted.
        for option_name, option in self.options.items():
            if option.required and option_name not in parameters:
                raise MissingRequiredListenerTemplateOptionError(
                    listener_template_str=str(self),
                    option_name=option_name,
                )

        # Fill in default option values for options that were not provided in the
        # parameters dictionary. For options that do not have a default value
        # they fill in as `None`
        for option_name, option in self.options.items():
            if option_name not in parameters:
                parameters[option_name] = option.default_value

        # Validate entire constructed parameter set before creating the listener.
        for option_name, value in parameters.items():
            if option_name not in self.options:
                raise ListenerTemplateOptionNotFoundError(
                    listener_template_str=str(self),
                    option_name=option_name,
                )
            try:
                option = self.options[option_name]
                # Allow `None` for non-required options
                if value is None and not option.required:
                    continue
                option.validate_value(value)
            except OptionValueValidationError as exc:
                raise ListenerTemplateOptionValueValidationError(
                    option_name=option_name,
                    option_value=value,
                    listener_template_str=str(self),
                    error_message=str(exc),
                ) from None

        # Run validation function on the entire set of parameters if one was provided.
        if self.validating_function:
            self.validating_function(parameters)

        # Create listener instance. Resolving the name from the parameters only if one
        # was not provided.
        return self.listener(
            name=self.resolve_listener_name(parameters=parameters)
            if name is None
            else name,
            description=description,
            endpoint=self.resolve_listener_endpoint(parameters=parameters),
            parameters=parameters,
        )

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the listener template's full metadata to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the template ID, label, name, description, version,
            framework compatibility, authors, dependencies, listener type, options,
            and any validating function documentation.
        """
        return {
            "listener_template_id": str(self.listener_template_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": list(self.authors),
            "component_dependencies": list(map(str, self.component_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "listener_type": self.listener_type.to_json(),
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
        """Serialize a compact reference to this listener template.

        Returns:
            A dictionary containing only the template ID, label, and name, suitable
            for embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "listener_template_id": str(self.listener_template_id),
            "label": self.label,
            "name": self.name,
        }
