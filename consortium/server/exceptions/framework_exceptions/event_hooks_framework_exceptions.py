# """
# Exception hierarchy for event hooks framework:
#
# - BaseFrameworkException: Base class for all framework exceptions.
#   - EventHooksFrameworkError: General error occurred in the event hooks framework.
#     - EventHookConfigurationParameterTypeError: The parameter must be of a specific
#     type for the event hook.
#     - RequiredEventHookConfigurationParameterNotDeclaredError: A required parameter was
#     not declared for the event hook.
#     - EmptyEventHookNameError: The event hook's name cannot be empty for the specified
#     event hook file path.
# """
import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)

# class EventHooksFrameworkError(BaseFrameworkException):
#     pass
#
#
# class EventHookConfigurationParameterTypeError(EventHooksFrameworkError):
#     def __init__(
#         self,
#         event_hook: str,
#         parameter_name: str | None = None,
#         parameter_type: str | None = None,
#         error_message: str = "",
#     ):
#         if not error_message:
#             super().__init__(
#                 message=(
#                     f"Failed to configure the event hook '{event_hook}'. "
#                     f"The parameter '{parameter_name}' must be of type "
#                     f"'{parameter_type}' in the event hook's definition."
#                 ),
#             )
#         else:
#             super().__init__(
#                 message=(
#                     f"Failed to configure the event hook '{event_hook}'. "
#                     f"{error_message}"
#                 ),
#             )
#
#
# class RequiredEventHookConfigurationParameterNotDeclaredError(EventHooksFrameworkError):
#     def __init__(self, parameter_name: str, event_hook: str):
#         super().__init__(
#             message=(
#                 f"Failed to configure the event hook '{event_hook}'. The required "
#                 f"parameter '{parameter_name}' was not declared in the event hook's "
#                 f"definition ."
#             ),
#         )
#
#
# class EmptyEventHookNameError(EventHooksFrameworkError):
#     def __init__(self, event_hook_filepath: str):
#         super().__init__(
#             message=(
#                 f"Failed to configure the event hook defined at "
#                 f"'{event_hook_filepath}'. The name provided in the event hook's "
#                 f"definition during configuration cannot be empty."
#             ),
#         )


class EventHooksFrameworkError(
    comp_excs.ComponentsFrameworkError,
    BaseFrameworkException,
):
    """
    Base exception for all errors that occur within the event hooks framework.
    """

    code = "EVENT_HOOKS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "event hook"


class EventHookConfigurationError(
    comp_excs.ComponentConfigurationError,
    EventHooksFrameworkError,
):
    """
    Base exception for all errors that occur during the configuration of a particular
    event hook.
    """

    code = "EVENT_HOOK_CONFIGURATION_ERROR"


class InvalidEventHookConfigurationParameterTypeError(
    comp_excs.InvalidComponentConfigurationParameterTypeError,
    EventHookConfigurationError,
):
    """
    An error that is raised when an event hook's configuration parameter is of an
    invalid type.
    """

    code = "INVALID_EVENT_HOOK_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        parameter_name: str,
        parameter_type: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            parameter_name=parameter_name,
            parameter_type=parameter_type,
        )


class MissingEventHookConfigurationParameterError(
    comp_excs.MissingComponentConfigurationParameterError,
    EventHookConfigurationError,
):
    """
    An error that is raised when a parameter is not declared in an event hook's
    definition.
    """

    code = "MISSING_EVENT_HOOK_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, parameter_name: str, event_hook_str: str):
        super().__init__(
            component_str=event_hook_str,
            parameter_name=parameter_name,
        )


class EmptyEventHookLabelError(
    comp_excs.EmptyComponentLabelError,
    EventHookConfigurationError,
):
    """
    An error that is raised when the label provided in an event hook's definition during
    configuration is an empty string.
    """

    code = "EMPTY_EVENT_HOOK_LABEL_ERROR"

    def __init__(self, event_hook_filepath: str):
        super().__init__(component_filepath=event_hook_filepath)


class DuplicateEventHookLabelError(
    comp_excs.DuplicateComponentLabelError,
    EventHookConfigurationError,
):
    """
    An error that is raised when the label provided in the event hook's definition during
    configuration is already in use by another event hook.
    """

    code = "DUPLICATE_EVENT_HOOK_LABEL_ERROR"

    def __init__(self, event_hook_str: str, label: str):
        super().__init__(
            component_str=event_hook_str,
            label=label,
        )


class InvalidEventHookVersionError(
    comp_excs.InvalidComponentVersionError,
    EventHookConfigurationError,
):
    """
    An error that is raised when the event hook version string provided in the event hook's
    definition during configuration is not a valid version string according to PEP 440.
    """

    code = "INVALID_EVENT_HOOK_VERSION_ERROR"

    def __init__(self, event_hook_str: str, version: str):
        super().__init__(
            component_str=event_hook_str,
            version=version,
        )


class InvalidFrameworkVersionSpecifierError(
    comp_excs.InvalidFrameworkVersionSpecifierError,
    EventHookConfigurationError,
):
    """
    An error that is raised when the framework version specifier string provided in the
    event hook's definition during configuration is not a valid version specifier string as
    defined in PEP440.
    """

    code = "INVALID_FRAMEWORK_VERSION_SPECIFIER_ERROR"

    def __init__(self, event_hook_str: str, framework_version_specifier_str: str):
        super().__init__(
            component_str=event_hook_str,
            framework_version_specifier_str=framework_version_specifier_str,
        )


class InvalidEventHookDependencyVersionSpecifierError(
    comp_excs.InvalidComponentDependencyVersionSpecifierError,
    EventHookConfigurationError,
):
    """
    An error that is raised when the event hook dependency version specifier string
    provided in the event hook's definition during configuration is not a valid version
    specifier string as defined in PEP440.
    """

    code = "INVALID_EVENT_HOOK_DEPENDENCY_VERSION_SPECIFIER_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        invalid_dependency_entry: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            invalid_dependency_entry=invalid_dependency_entry,
        )
