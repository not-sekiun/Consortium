"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`ListenersServiceError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenersServiceError]
        - [`ListenerNotFoundError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerNotFoundError]
        - [`ListenerAlreadyExistsError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerAlreadyExistsError]
        - [`ListenerParameterUpdateError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.ListenerParameterUpdateError]
            - [`InvalidListenerParameterNameError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.InvalidListenerParameterNameError]
            - [`InvalidListenerParameterValueError`][consortium.server.exceptions.consortium_exceptions.listeners_consortium_exceptions.InvalidListenerParameterValueError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class ListenersServiceError(BaseConsortiumError):
    """Base exception for all errors that occur within the listeners service."""

    code = "LISTENERS_SERVICE_ERROR"


class ListenerNotFoundError(ListenersServiceError):
    """Raised when the requested listener with the provided listener ID was not found in
    the listeners service.
    """

    code = "LISTENER_NOT_FOUND_ERROR"

    def __init__(self, listener_id: str):
        super().__init__(
            f"Failed to find the requested listener. No listener was found with the "
            f"provided listener ID '{listener_id}'.",
        )


class ListenerAlreadyExistsError(ListenersServiceError):
    """Raised when attempting to create a listener with a listener ID that already exists
    in the listeners service.
    """

    code = "LISTENER_ALREADY_EXISTS_ERROR"

    def __init__(self, listener_id: str):
        super().__init__(
            message=(
                f"Failed to add the specified listener. A listener already exists with "
                f"the listener ID '{listener_id}'."
            ),
        )


class ListenerParameterUpdateError(ListenersServiceError):
    """Base exception for all errors that occur when updating a listener parameter through
    the listeners service.
    """

    code = "LISTENER_PARAMETER_UPDATE_ERROR"


class InvalidListenerParameterNameError(ListenerParameterUpdateError):
    """Raised when an invalid parameter name is provided when attempting to update a
    listener parameter through the listeners service.
    """

    code = "INVALID_LISTENER_PARAMETER_NAME_ERROR"

    def __init__(self, listener_str: str, parameter_name: str):
        super().__init__(
            message=(
                f"Failed to update the listener parameter for listener "
                f"'{listener_str}'. The provided parameter name '{parameter_name}' was "
                f"not found for the listener."
            ),
        )


class InvalidListenerParameterValueError(ListenerParameterUpdateError):
    """Raised when an invalid parameter value is provided when attempting to update a
    listener parameter through the listeners service.
    """

    code = "INVALID_LISTENER_PARAMETER_VALUE_ERROR"

    def __init__(
        self,
        listener_str: str,
        parameter_name: str,
        parameter_value: str,
        error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to update the listener parameter for listener "
                f"'{listener_str}'. The value provided '{parameter_value}' for the "
                f"parameter '{parameter_name}' is invalid. {error_message}"
            ),
        )
