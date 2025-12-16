"""
This module describes all the exceptions that can be raised by the components framework.
These exceptions are distinctly different from the "signalling" exceptions that are
present in the [`consortium.framework.exceptions`][consortium.framework.exceptions]
module. The exceptions here do not serve any message passing or signalling purpose to or
from the framework. Instead, they are raised when an error condition occurs and are also
meant to be used by the REST API layer.

Exception hierarchy for the components framework:

- [`BaseFrameworkException`][consortium.server.exceptions.framework_exceptions.base_framework_exception.BaseFrameworkException]
    - [`ComponentsFrameworkError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentsFrameworkError]
        - [`ComponentConfigurationError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentConfigurationError]
            - [`InvalidComponentConfigurationParameterTypeError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.InvalidComponentConfigurationParameterTypeError]
            - [`MissingComponentConfigurationParameterError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.MissingComponentConfigurationParameterError]
            - [`EmptyComponentLabelError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.EmptyComponentLabelError]
            - [`DuplicateComponentLabelError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.DuplicateComponentLabelError]
            - [`InvalidComponentVersionError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.InvalidComponentVersionError]
            - [`InvalidFrameworkVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.InvalidFrameworkVersionSpecifierError]
            - [`InvalidThirdPartyDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.InvalidThirdPartyDependencyVersionSpecifierError]
            - [`InvalidComponentDependencyVersionSpecifierError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.InvalidComponentDependencyVersionSpecifierError]
        - [`ComponentOperationError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentOperationError]
            - [`ComponentNotRunningError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentNotRunningError]
            - [`ComponentAlreadyRunningError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentAlreadyRunningError]
            - [`ComponentStartError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentStartError]
            - [`ComponentRuntimeError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentRuntimeError]
            - [`ComponentStopError`][consortium.server.exceptions.framework_exceptions.components_framework_exceptions.ComponentStopError]
"""

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ComponentsFrameworkError(BaseFrameworkException):
    """
    Base exception for all errors that occur within the components framework.
    """

    code = "COMPONENTS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "component"
    _MESSAGE_TEMPLATE = ""  # Holds the pure template string
    # Holds the template string that has the $C_LOWER$ and $C_CAPITAL$ replaced by the
    # particular component type.
    _MESSAGE = ""

    def __init__(self, message: str | None = None, detail: Any = None, **kwargs):
        self._kwargs = kwargs
        if message:
            super().__init__(message=message, detail=detail)
        else:
            super().__init__(message=self._MESSAGE.format(**kwargs), detail=detail)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        component_lower = cls._COMPONENT_TYPE.lower()
        component_capital = cls._COMPONENT_TYPE.capitalize()
        cls._MESSAGE = cls._MESSAGE_TEMPLATE.replace(
            "$C_LOWER$",
            component_lower,
        ).replace(
            "$C_CAPITAL$",
            component_capital,
        )


class ComponentConfigurationError(ComponentsFrameworkError):
    """
    Base exception for all errors that occur during the configuration of a particular
    component.
    """

    code = "COMPONENT_CONFIGURATION_ERROR"


class InvalidComponentConfigurationParameterTypeError(ComponentConfigurationError):
    """
    An error that is raised when a component's configuration parameter is of an invalid
    type.
    """

    code = "INVALID_COMPONENT_CONFIGURATION_PARAMETER_TYPE_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ '{component_str}'. The parameter "
        "`{parameter_name}` must be of type `{parameter_type}` in the $C_LOWER$'s "
        "definition. Modify the $C_LOWER$'s `{parameter_name}` class variable to be of "
        "the proper type."
    )

    def __init__(
        self,
        component_str: str,
        parameter_name: str,
        parameter_type: str,
    ):
        super().__init__(
            component_str=component_str,
            parameter_name=parameter_name,
            parameter_type=parameter_type,
        )


class MissingComponentConfigurationParameterError(ComponentConfigurationError):
    """
    An error that is raised when a parameter is not declared in a component's definition.
    """

    code = "MISSING_COMPONENT_CONFIGURATION_PARAMETER_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ '{component_str}'. The parameter "
        "`{parameter_name}` was not declared in the $C_LOWER$'s definition. Modify the "
        "$C_LOWER$ to include `{parameter_name}` as a class variable of the proper "
        "type."
    )

    def __init__(self, component_str: str, parameter_name: str):
        super().__init__(
            component_str=component_str,
            parameter_name=parameter_name,
        )


class EmptyComponentLabelError(ComponentConfigurationError):
    """
    An error that is raised when the label provided in a component's definition during
    configuration is an empty string.
    """

    code = "EMPTY_COMPONENT_LABEL_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ defined at '{component_filepath}'. The "
        "label provided in the $C_LOWER$'s definition during configuration cannot be "
        "an empty string. Redeclare the $C_LOWER$'s `label` class attribute to be a "
        "unique non-empty string."
    )

    def __init__(self, component_filepath: str):
        super().__init__(component_filepath=component_filepath)


class DuplicateComponentLabelError(ComponentConfigurationError):
    """
    An error that is raised when the label provided in the component's definition during
    configuration is already in use by another component.
    """

    code = "DUPLICATE_COMPONENT_LABEL_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ '{component_str}'. The label '{label}' is "
        "already used by another $C_LOWER$. Redeclare the $C_LOWER$'s `label` class "
        "attribute to be unique amongst all loaded $C_LOWER$s."
    )

    def __init__(self, component_str: str, label: str):
        super().__init__(component_str=component_str, label=label)


class InvalidComponentVersionError(ComponentConfigurationError):
    """
    An error that is raised when the component version string provided in the component's
    definition during configuration is not a valid version string according to PEP 440.
    """

    code = "INVALID_COMPONENT_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ '{component_str}'. The $C_LOWER$ version "
        "string provided '{version}' is not a valid versioning string. See PEP"
        " 440 for more details on valid versioning strings."
    )

    def __init__(self, component_str: str, version: str):
        super().__init__(component_str=component_str, version=version)


class InvalidFrameworkVersionSpecifierError(ComponentConfigurationError):
    """
    An error that is raised when the framework version specifier string provided in the
    component's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ '{component_str}'. The framework version "
        "specifier string provided '{framework_version_specifier}' is not a "
        "valid version specifier string. See PEP 440 for details on version "
        "specifier strings."
    )

    def __init__(self, component_str: str, framework_version_specifier: str):
        super().__init__(
            component_str=component_str,
            framework_version_specifier=framework_version_specifier,
        )


class InvalidComponentDependencyVersionSpecifierError(ComponentConfigurationError):
    """
    An error that is raised when the component dependency version specifier string
    provided in the component's definition during configuration is not a valid version
    specifier string as defined in PEP440.
    """

    code = "INVALID_COMPONENT_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ '{component_str}'. The component's "
        "`component_dependencies` configuration parameter contains the invalid "
        "dependency entry '{invalid_dependency_entry}'. Check that the dependency "
        "parameter contains entries conforming to PEP 508."
    )

    def __init__(
        self,
        component_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=component_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class ComponentOperationError(ComponentsFrameworkError):
    """
    Base exception for all errors that occur during the operation of a particular
    component.
    """

    code = "COMPONENT_OPERATION_ERROR"


class ComponentNotRunningError(ComponentOperationError):
    """
    An error that is raised when an operation is attempted on a component that requires
    that component to already be running but the component is not running.
    """

    code = "COMPONENT_NOT_RUNNING_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to perform the requested operation on the $C_LOWER$ "
        "'{component_str}'. The $C_LOWER$ is not running."
    )

    def __init__(
        self,
        component_str: str,
    ):
        super().__init__(component_str=component_str)


class ComponentAlreadyRunningError(ComponentOperationError):
    """
    An error that is raised when an operation is attempted on a component that requires
    that component to not already be started or running but the component is already started
    or running.
    """

    code = "COMPONENT_ALREADY_RUNNING_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to perform the requested operation on the $C_LOWER$ "
        "'{component_str}'. The $C_LOWER$ is already started or running."
    )

    def __init__(
        self,
        component_str: str,
    ):
        super().__init__(component_str=component_str)


class ComponentStartError(ComponentOperationError):
    """
    An error that is raised when a component fails to start.
    """

    code = "COMPONENT_START_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to start the $C_LOWER$ '{component_str}'. {error_message}"
    )

    def __init__(
        self,
        component_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            component_str=component_str,
            error_message=error_message,
            detail=detail,
        )


class ComponentRuntimeError(ComponentOperationError):
    """
    An error that is raised when a component encounters an error at runtime.
    """

    code = "COMPONENT_RUNTIME_ERROR"

    _MESSAGE_TEMPLATE = "Failed to run the $C_LOWER$ '{component_str}'. {error_message}"

    def __init__(
        self,
        component_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            component_str=component_str,
            error_message=error_message,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


class ComponentStopError(ComponentOperationError):
    """
    An error that is raised when a component fails to stop.
    """

    code = "COMPONENT_STOP_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to stop the $C_LOWER$ '{component_str}'. {error_message}"
    )

    def __init__(
        self,
        component_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            component_str=component_str,
            error_message=error_message,
        )
