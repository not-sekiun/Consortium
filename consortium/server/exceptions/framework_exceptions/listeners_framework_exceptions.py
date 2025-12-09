"""
Exception hierarchy for listeners framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - ListenersFrameworkException: General error occurred in the listeners framework.
    - ListenerConfigurationError: An error occurred while configuring the listener.
      - ListenerConfigurationParameterTypeError: The parameter must be of a specific
      type for the listener defined at the given file path.
      - RequiredListenerConfigurationParameterNotDeclaredError: A required parameter
      was not declared for the listener defined at the given file path.
    - ListenerCreationError: An error occurred while creating the listener.
      - ListenerCreationParameterTypeError: The parameter must be of a specific type for
      the listener being created.
    - ListenerNotRunningError: An error occurred because the requested operation
    could not be completed while the listener is not running.
    - ListenerAlreadyRunningError: An error occurred because the requested
    operation could not be completed while the listener is running.
    - ListenerStartError: An error occurred while starting the listener.
    - ListenerRuntimeError: An error occurred while the listener was running.
    - ListenerStopError: An error occurred while stopping the listener.
"""

from typing import Any

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenersFrameworkError(BaseFrameworkException):
    code = "LISTENERS_FRAMEWORK_ERROR"


class ListenerConfigurationError(
    comp_excs.ComponentConfigurationError,
    ListenersFrameworkError,
):
    """
    Base exception for all errors that occur during the configuration of a particular
    listener.
    """

    code = "LISTENER_CONFIGURATION_ERROR"

    _COMPONENT_TYPE = "listener"


class InvalidListenerConfigurationParameterTypeError(ListenerConfigurationError):
    code = "INVALID_LISTENER_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the listener defined at "
                f"'{listener_str}'. The parameter '{parameter_name}' must be "
                f"of type '{parameter_type}' in the listener's definition."
            ),
        )


class MissingListenerConfigurationParameterError(
    ListenerConfigurationError,
):
    code = "MISSING_LISTENER_CONFIGURATION_PARAMETER_ERROR"

    def __init__(self, listener_str: str, parameter_name: str):
        super().__init__(
            component_str=listener_str,
            parameter_name=parameter_name,
        )
        # super().__init__(
        #     message=(
        #         f"Failed to configure the listener defined at '{listener_str}'. "
        #         f"The required parameter '{parameter_name}' was not declared in the "
        #         f"listener's definition."
        #     ),
        # )


class ListenerOperationError(
    comp_excs.ComponentOperationError,
    ListenersFrameworkError,
):
    """
    Base exception for all errors that occur during the operation of a particular
    listener.
    """

    code = "LISTENER_OPERATION_ERROR"

    _COMPONENT_TYPE = "listener"


class ListenerNotRunningError(
    comp_excs.ComponentNotRunningError,
    ListenerOperationError,
):
    """
    An error that is raised when an operation is attempted on a listener that requires
    that listener to already be running but the listener is not running.
    """

    code = "LISTENER_NOT_RUNNING_ERROR"

    def __init__(
        self,
        listener_str: str,
    ):
        super().__init__(component_str=listener_str)


class ListenerAlreadyStartedError(
    comp_excs.ComponentAlreadyStartedError,
    ListenerOperationError,
):
    """
    An error that is raised when an operation is attempted on a listener that requires
    that listener to not already be started or running but the listener is already started
    or running.
    """

    code = "LISTENER_ALREADY_STARTED_ERROR"

    def __init__(
        self,
        listener_str: str,
    ):
        super().__init__(component_str=listener_str)


class ListenerStartError(comp_excs.ComponentStartError, ListenerOperationError):
    """
    An error that is raised when a listener fails to start.
    """

    code = "LISTENER_START_ERROR"

    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            listener_str=listener_str,
            error_message=error_message,
        )


class ListenerRuntimeError(comp_excs.ComponentRuntimeError, ListenerOperationError):
    """
    An error that is raised when a listener encounters an error at runtime.
    """

    code = "LISTENER_RUNTIME_ERROR"

    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            component_str=listener_str,
            error_message=error_message,
        )


class ListenerStopError(comp_excs.ComponentStopError, ListenerOperationError):
    """
    An error that is raised when a listener fails to stop.
    """

    code = "LISTENER_STOP_ERROR"

    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            detail=detail,
            listener_str=listener_str,
            error_message=error_message,
        )


class ListenerCreationError(ListenersFrameworkError):
    code = "LISTENER_CREATION_ERROR"


class ListenerCreationParameterTypeError(ListenerCreationError):
    code = "LISTENER_CREATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to create the listener '{listener_str}'. The parameter "
                    f"'{parameter_name}' must be of type '{parameter_type}' in the "
                    f"listener's provided parameters."
                ),
            )
        else:
            super().__init__(
                message=(
                    f"Failed to create the listener '{listener_str}'. {error_message}"
                ),
            )


# class ListenerNotRunningError(ListenersFrameworkError):
#     def __init__(
#         self,
#         listener_str: str,
#         error_message: str,
#     ):
#         super().__init__(
#             message=(
#                 f"An error occurred with the listener '{listener_str}' because "
#                 f"it is not running. {error_message}"
#             ),
#         )
#
#
# class ListenerAlreadyRunningError(ListenersFrameworkError):
#     def __init__(
#         self,
#         listener_str: str,
#         error_message: str,
#     ):
#         super().__init__(
#             message=(
#                 f"An error occurred with the listener '{listener_str}' because "
#                 f"it is already running. {error_message}"
#             ),
#         )
#
#
# class ListenerStartError(ListenersFrameworkError):
#     def __init__(
#         self,
#         listener_str: str,
#         error_message: str,
#         detail: Any,
#     ):
#         super().__init__(
#             message=f"Failed to start the listener '{listener_str}'. {error_message}",
#             detail=detail,
#         )
#
#
# class ListenerRuntimeError(ListenersFrameworkError):
#     def __init__(
#         self,
#         listener_str: str,
#         error_message: str,
#         detail: Any,
#     ):
#         super().__init__(
#             message=(
#                 f"The listener '{listener_str}' encountered an error while "
#                 f"running. {error_message}"
#             ),
#             detail=detail,
#         )
#
#
# class ListenerStopError(ListenersFrameworkError):
#     def __init__(
#         self,
#         listener_str: str,
#         error_message: str,
#         detail: Any,
#     ):
#         super().__init__(
#             message=f"Failed to stop the listener '{listener_str}'. {error_message}",
#             detail=detail,
#         )
