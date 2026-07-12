from consortium.framework.signal_exceptions.base_signal_exception import (
    BaseSignalException,
)


class OptionValueValidationError(BaseSignalException):
    """Raise from a validating function to signal that an option value is invalid."""
