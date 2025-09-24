import copy
import sys
from typing import Any

from consortium.framework.options._option_argument_validators import (
    ArgumentDataTypeCheckParameters,
    validate_arguments_data_types,
)
from consortium.framework.options.exceptions import (
    EmptyOptionNameError,
    InvalidDefaultValueError,
    InvalidOptionConfigurationParameterTypeError,
    OptionValueValidationError as OptionValueValidationFrameworkError,
    RequiredOptionValueNotSetError,
)
from consortium.framework.options.option_types import OptionType


class BaseOption:
    option_type: OptionType

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: Any | None = None,
    ):
        # Assign all values to self before performing validation because the validation
        # function might make reference to the provided parameters by accessing them
        # through self.
        self.name = name
        """The human-readable name of the option. The name cannot be an empty string."""
        self.description = description
        """A description of the option."""
        self.required = required
        """
        Whether the option is required or not. If True, the option must have a value set
        before it can be retrieved. If False, the option can be retrieved without a
        value being set.
        """
        self.default_value = default_value
        """
        The default value of the option. If `None`, the option has no default value.
        """

        self._value = None

        self._validate_option_configuration()

    def __str__(self) -> str:
        try:
            value_display_string = repr(self.get_option_value())
        except RequiredOptionValueNotSetError:
            value_display_string = "UNDEFINED"
        return f"{self.option_type} - Name: {self.name}, Value: {value_display_string}"

    def validate_value(self, value: Any) -> None:
        """
        Validate the value of the option.

        Args:
            value (Any): The value to validate.

        Raises:
            OptionValueValidationFrameworkError: If the value is invalid.
        """
        pass

    def to_json(self) -> dict[str, Any]:
        """
        Convert the option to a JSON serializable dictionary.

        Returns:
            The JSON serializable dictionary representation of the option.
        """
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "value": self._value,
        }

    def get_option_value(self) -> Any:
        """
        Get the value of the option. If the value is not set and the option is required,
        a `RequiredOptionValueNotSetError` will be raised. If the value is not set and
        the option is not required, `None` will be returned. The value returned has been
        deeply copied so you can safely modify it without affecting the option.

        Returns:
            Any: The value of the option.

        Raises:
            RequiredOptionValueNotSetError: If the value is not set and the option is
                required.
        """
        if self._value is None:
            if self.default_value is None:
                if self.required:
                    raise RequiredOptionValueNotSetError(
                        option_name=self.name,
                    )
                else:
                    return None
            return copy.deepcopy(self.default_value)
        return copy.deepcopy(self._value)

    def set_option_value(self, value: Any) -> None:
        """
        Set the value of the option.

        Args:
            value (Any): The value to set the option to.

        Raises:
            OptionValueValidationError: If the value is invalid.
        """
        self.validate_value(value)
        self._value = value

    def clear_option_value(self) -> None:
        """
        Clear the value of the option.
        """
        self._value = None

    def _validate_option_arguments(self) -> None:
        # if `option_type` is not set, then it is a programmer fault.
        assert hasattr(
            self,
            "option_type",
        ), "The option type must be set for the option to be valid."
        assert isinstance(self.option_type, OptionType), (
            f"The option type must be set to a valid option type for option "
            f"'{self.name}'."
        )

        # We manually check the `self.name` parameter first because every other error
        # message that arises from the validation of the other parameters will reference
        # the option name.
        if not isinstance(self.name, str):
            raise InvalidOptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="name",
                expected_parameter_type_string="str",
            )
        if not self.name:
            raise EmptyOptionNameError(
                option_filepath=sys.modules[self.__module__].__file__,
            )
        validate_arguments_data_types(
            self.name,
            ArgumentDataTypeCheckParameters(
                value=self.description,
                expected_data_type=str,
            ),
            ArgumentDataTypeCheckParameters(
                value=self.required,
                expected_data_type=bool,
            ),
        )

    def _validate_option_configuration(self):
        # Validate that all the arguments provided to the option are valid first.
        self._validate_option_arguments()

        # Validate the default value if it is provided after doing all the initial
        # argument validation.
        if self.default_value is not None:
            try:
                self.validate_value(self.default_value)
            except OptionValueValidationFrameworkError as exc:
                raise InvalidDefaultValueError(
                    option_name=self.name,
                    default_value=self.default_value,
                    option_value_validation_error_message=str(exc),
                ) from None
