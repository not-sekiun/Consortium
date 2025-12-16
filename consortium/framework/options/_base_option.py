# import copy
import sys
from typing import Any

from consortium.framework.options._option_argument_validators import (
    ArgumentDataTypeCheckParameters,
    validate_arguments_data_types,
)
from consortium.framework.options.option_types import OptionType
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (  # RequiredOptionValueNotSetError,
    EmptyOptionNameError,
    InvalidDefaultValueError,
    InvalidOptionConfigurationParameterTypeError,
    OptionValueValidationError,
)


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
        # try:
        #     value_display_string = repr(self.get_option_value())
        # except RequiredOptionValueNotSetError:
        #     value_display_string = "UNDEFINED"
        # return f"Option - {self.option_type}: {self.name}"
        return f"{self.name} ({self.option_type})"

    def validate_value(self, value: Any) -> None:
        """
        Validate the value of the option.

        Args:
            value (Any): The value to validate.

        Raises:
            OptionValueValidationError: If the value is invalid.
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
            except OptionValueValidationError as exc:
                raise InvalidDefaultValueError(
                    option_name=self.name,
                    default_value=self.default_value,
                    option_value_validation_error_message=str(exc),
                ) from None
