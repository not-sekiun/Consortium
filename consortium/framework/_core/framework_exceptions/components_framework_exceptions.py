from pydantic import JsonValue

from consortium.framework._core.framework_exceptions.base_framework_exception import (
    BaseFrameworkError,
)


class ComponentsFrameworkError(BaseFrameworkError):
    """Base exception for all errors that occur within the components framework."""

    code = "COMPONENTS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "component"
    _MESSAGE_TEMPLATE = ""  # Holds the pure template string
    # Holds the template string that has the $C_LOWER$ and $C_CAPITAL$ replaced by the
    # particular component type.
    _MESSAGE = ""

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, JsonValue] | None = None,
        **kwargs,
    ):
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
    """Base exception for all errors that occur during the configuration of a particular
    component.
    """

    code = "COMPONENT_CONFIGURATION_ERROR"


class InvalidComponentConfigurationParameterTypeError(ComponentConfigurationError):
    """Raised when a component's configuration parameter is not of the expected type during
    component configuration.
    """

    code = "INVALID_COMPONENT_CONFIGURATION_PARAMETER_TYPE_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ {component_str}. The parameter "
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
    """Raised when a required parameter is not declared in a component's definition during
    component configuration.
    """

    code = "MISSING_COMPONENT_CONFIGURATION_PARAMETER_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ {component_str}. The parameter "
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
    """Raised when an empty label is provided in a component's definition during component
    configuration.
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


class InvalidComponentVersionError(ComponentConfigurationError):
    """Raised when the component version string provided in the component's definition is not a
    valid version string according to PEP 440 during component configuration.
    """

    code = "INVALID_COMPONENT_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ {component_str}. The $C_LOWER$ version "
        "string provided '{version}' is not a valid versioning string. See PEP"
        " 440 for more details on valid versioning strings."
    )

    def __init__(self, component_str: str, version: str):
        super().__init__(component_str=component_str, version=version)


class InvalidFrameworkVersionSpecifierError(ComponentConfigurationError):
    """Raised when the framework version specifier string provided in the component's
    definition is not a valid version specifier string as defined in PEP 440 during
    component configuration.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ {component_str}. The framework version "
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
    """Raised when a component dependency version specifier string provided in the component's
    definition is not a valid version specifier string as defined in PEP 440 during
    component configuration.
    """

    code = "INVALID_COMPONENT_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to configure the $C_LOWER$ {component_str}. The component's "
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
    """Base exception for all errors that occur during the operation of a particular
    component.
    """

    code = "COMPONENT_OPERATION_ERROR"


class ComponentStartError(ComponentOperationError):
    """Raised when a component fails to start during component operation."""

    code = "COMPONENT_START_ERROR"

    _MESSAGE_TEMPLATE = "Failed to start the $C_LOWER$ {component_str}. {error_message}"

    def __init__(
        self,
        component_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            component_str=component_str,
            error_message=error_message,
            detail=detail,
        )


class ComponentRuntimeError(ComponentOperationError):
    """Raised when a component encounters an unhandled error at runtime during component
    operation.
    """

    code = "COMPONENT_RUNTIME_ERROR"

    _MESSAGE_TEMPLATE = "Failed to run the $C_LOWER$ {component_str}. {error_message}"

    def __init__(
        self,
        component_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            detail=detail,
            component_str=component_str,
            error_message=error_message,
        )


class ComponentStopError(ComponentOperationError):
    """Raised when a component fails to stop during component operation."""

    code = "COMPONENT_STOP_ERROR"

    _MESSAGE_TEMPLATE = "Failed to stop the $C_LOWER$ {component_str}. {error_message}"

    def __init__(
        self,
        component_str: str,
        error_message: str,
        detail: dict[str, JsonValue],
    ):
        super().__init__(
            detail=detail,
            component_str=component_str,
            error_message=error_message,
        )


class ComponentStateError(ComponentsFrameworkError):
    """Base exception for all errors that occur due to invalid component status during
    component operation.
    """

    code = "COMPONENT_STATE_ERROR"


class ComponentNotRunningError(ComponentStateError):
    """Raised when an operation is attempted on a component that requires the component to
    already be running but the component is not running.
    """

    code = "COMPONENT_NOT_RUNNING_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to perform the requested operation on the $C_LOWER$ {component_str}. "
        "The $C_LOWER$ is not running which conflicts with the operation that was "
        "requested."
    )

    def __init__(
        self,
        component_str: str,
    ):
        super().__init__(component_str=component_str)


class ComponentAlreadyRunningError(ComponentStateError):
    """Raised when an operation is attempted on a component that requires the component to not
    already be started or running but the component is already started or running.
    """

    code = "COMPONENT_ALREADY_RUNNING_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to perform the requested operation on the $C_LOWER$ {component_str}. "
        "The $C_LOWER$ is already running which conflicts with the operation that was "
        "requested."
    )

    def __init__(
        self,
        component_str: str,
    ):
        super().__init__(component_str=component_str)
