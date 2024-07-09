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
      - EmptyListenerNameError: The name provided for the listener is an empty string.
    - ListenerNotRunningError: An error occurred because the requested operation
    could not be completed while the listener is not running.
    - ListenerAlreadyRunningError: An error occurred because the requested
    operation could not be completed while the listener is running.
    - ListenerStartError: An error occurred while starting the listener.
    - ListenerRuntimeError: An error occurred while the listener was running.
    - ListenerStopError: An error occurred while stopping the listener.
"""

from typing import Any

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class ListenersFrameworkError(BaseFrameworkException):
    pass


class ListenerConfigurationError(ListenersFrameworkError):
    pass


class ListenerConfigurationParameterTypeError(ListenerConfigurationError):
    def __init__(
        self,
        listener_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to configure the listener defined at "
                f"'{listener_filepath}'. The parameter '{parameter_name}' must be "
                f"of type '{parameter_type}' in the listener's definition."
            ),
        )


class RequiredListenerConfigurationParameterNotDeclaredError(
    ListenerConfigurationError,
):
    def __init__(self, parameter_name: str, listener_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the listener defined at '{listener_filepath}'. "
                f"The required parameter '{parameter_name}' was not declared in the "
                f"listener's definition."
            ),
        )


class ListenerCreationError(ListenersFrameworkError):
    pass


class ListenerCreationParameterTypeError(ListenerCreationError):
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


class EmptyListenerNameError(ListenerCreationError):
    def __init__(
        self,
        listener_filepath: str,
    ):
        super().__init__(
            message=(
                f"Failed to create the listener defined at '{listener_filepath}'. The "
                f"name provided in the listener's parameters during creation cannot be "
                f"empty."
            ),
        )


class ListenerNotRunningError(ListenersFrameworkError):
    def __init__(
        self,
        listener_str: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the listener '{listener_str}' because "
                f"it is not running. {error_message}"
            ),
        )


class ListenerAlreadyRunningError(ListenersFrameworkError):
    def __init__(
        self,
        listener_str: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"An error occurred with the listener '{listener_str}' because "
                f"it is already running. {error_message}"
            ),
        )


class ListenerStartError(ListenersFrameworkError):
    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=f"Failed to start the listener '{listener_str}'. {error_message}",
            detail=detail,
        )


class ListenerRuntimeError(ListenersFrameworkError):
    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(
                f"The listener '{listener_str}' encountered an error while "
                f"running. {error_message}"
            ),
            detail=detail,
        )


class ListenerStopError(ListenersFrameworkError):
    def __init__(
        self,
        listener_str: str,
        error_message: str,
        detail: Any,
    ):
        super().__init__(
            message=(f"Failed to stop the listener '{listener_str}'. {error_message}"),
            detail=detail,
        )
