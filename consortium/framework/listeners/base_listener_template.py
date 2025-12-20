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
from consortium.framework.framework_types import (
    JSONObject,
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
from consortium.framework.utils.exception_utils import remap_exception
from consortium.framework.utils.formatter_utils import format_docstring_to_single_line
from consortium.server.exceptions.consortium_exceptions.listener_templates_consortium_exceptions import (
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
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    OptionValueValidationError,
)

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
    _METADATA_MODEL = _ListenerTemplateModel
    _EXCEPTION_MAP = {
        comp_excs.MissingComponentConfigurationParameterError: MissingListenerTemplateConfigurationParameterError,
        comp_excs.EmptyComponentLabelError: EmptyListenerTemplateLabelError,
        comp_excs.InvalidComponentVersionError: InvalidListenerTemplateVersionError,
        comp_excs.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        comp_excs.InvalidComponentDependencyVersionSpecifierError: InvalidListenerTemplateDependencyVersionSpecifierError,
        comp_excs.InvalidComponentConfigurationParameterTypeError: InvalidListenerTemplateConfigurationParameterTypeError,
    }
    _EXCEPTION_KWARGS_MAP = {
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

        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc._kwargs,
                exception_map=cls._EXCEPTION_MAP,
                exception_kwargs_map=cls._EXCEPTION_KWARGS_MAP,
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
        """
        Function to resolve the name of a newly created listener.

        This name can be a default hard-coded value, randomly generated or computed
        from its provided set of parameters (typically from a 'name' parameter).
        """

    @abstractmethod
    def resolve_listener_endpoint(
        self,
        parameters: dict[str, Primitive | PrimitiveCollection],
    ) -> str:
        """
        Function to resolve the endpoint of a newly created listener from the provided
        set of parameters.

        An endpoint is a string that uniquely identifies the address that a listener
        can be reached at. E.g. http://127.0.0.1:8000/check-in
        """

    def create_listener(
        self,
        name: str | None = None,
        description: str = "",
        parameters: dict[str, Primitive | PrimitiveCollection] | None = None,
    ) -> BaseListener:
        """
        Create a listener instance from this listener template using the provided
        `name`, `description` and configuration `parameters`.

        If a name is not provided, it will be resolved from the listener template's
        `resolve_name_endpoint` method.
        """

        if parameters is None:
            parameters = {}

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

        # Check for missing required options.
        for option_name, option in self.options.items():
            if option.required and option_name not in parameters:
                raise MissingRequiredListenerTemplateOptionError(
                    listener_template_str=str(self),
                    option_name=option_name,
                )

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

    def to_json(self) -> JSONObject:
        """
        Convert the listener template metadata to a JSON serializable dictionary.
        """
        return {
            "listener_template_id": str(self.listener_template_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": self.authors,
            "component_dependencies": list(map(str, self.component_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "listener_type": self.listener_type.to_json(),
            "registered_compatible_agent_types": list(
                self.registered_compatible_agent_types
            ),
            "options": {
                name: option.to_json() for name, option in self.options.items()
            },
            "validating_function": format_docstring_to_single_line(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
        }
