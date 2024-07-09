"""
Exception hierarchy for event hooks framework:

- BaseFrameworkException: Base class for all framework exceptions.
  - EventHooksFrameworkError: General error occurred in the event hooks framework.
    - EventHookConfigurationParameterTypeError: The parameter must be of a specific
    type for the event hook.
    - RequiredEventHookConfigurationParameterNotDeclaredError: A required parameter was
    not declared for the event hook.
    - EmptyEventHookNameError: The event hook's name cannot be empty for the specified
    event hook file path.
"""

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class EventHooksFrameworkError(BaseFrameworkException):
    pass


class EventHookConfigurationParameterTypeError(EventHooksFrameworkError):
    def __init__(
        self,
        event_hook_str: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        error_message: str = "",
    ):
        if not error_message:
            super().__init__(
                message=(
                    f"Failed to configure the event hook '{event_hook_str}'. "
                    f"The parameter '{parameter_name}' must be of type "
                    f"'{parameter_type}' in the event hook's definition."
                ),
            )
        else:
            super().__init__(
                message=(
                    f"Failed to configure the event hook '{event_hook_str}'. "
                    f"{error_message}"
                ),
            )


class RequiredEventHookConfigurationParameterNotDeclaredError(EventHooksFrameworkError):
    def __init__(self, parameter_name: str, event_hook_str: str):
        super().__init__(
            message=(
                f"Failed to configure the event hook '{event_hook_str}'. The required "
                f"parameter '{parameter_name}' was not declared in the event hook's "
                f"definition ."
            ),
        )


class EmptyEventHookNameError(EventHooksFrameworkError):
    def __init__(self, event_hook_filepath: str):
        super().__init__(
            message=(
                f"Failed to configure the event hook defined at "
                f"'{event_hook_filepath}'. The name provided in the event hook's "
                f"definition during configuration cannot be empty."
            ),
        )
