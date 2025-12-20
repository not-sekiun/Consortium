import sys
from typing import Any, TypeVar, get_type_hints

from pydantic import BaseModel, ValidationError

from consortium.framework.options.option_types import OptionType
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    EmptyOptionNameError,
    InvalidDefaultValueError,
    InvalidOptionConfigurationParameterTypeError,
    OptionValueValidationError,
)

ValueType = TypeVar("ValueType")


# Ignore validating the default value type here because each option type will
# have its own specific validation logic for the default value.
class _BaseOptionParametersModel(BaseModel):
    name: str
    description: str
    required: bool


class BaseOption[ValueType]:
    option_type: OptionType

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: ValueType | None = None,
    ):
        # Assign all values to self before performing validation because the validation
        # function might make reference to the provided parameters by accessing them
        # through self.
        self.name = name
        self.description = description
        self.required = required
        self.default_value = default_value

        self._value = None

        self._validate_option_configuration()

    def __init_subclass__(cls, *args, **kwargs):
        # if `option_type` is not set, then it is a programmer fault.
        assert hasattr(
            cls,
            "option_type",
        ), "The option type must be set for the option to be valid."
        assert isinstance(cls.option_type, OptionType), (
            f"The option type must be set to a valid option type for option "
            f"'{cls.__name__}'."
        )

        super().__init_subclass__(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.option_type})"

    def __repr__(self) -> str: ...

    def validate_value(self, value: ValueType) -> None:
        """
        Validate the value of the option.

        Args:
            value: The value to validate.

        Raises:
            OptionValueValidationError: If the value is invalid.
        """

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
        # We manually check the `self.name` parameter first because every other error
        # message that arises from the validation of the other parameters will reference
        # the option name.
        if not isinstance(self.name, str):
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=self.__class__.__name__,
                parameter_name="name",
                parameter_type="str",
            )
        if not self.name:
            raise EmptyOptionNameError(
                option_filepath=sys.modules[self.__module__].__file__,
            )

        try:
            _BaseOptionParametersModel(
                name=self.name,
                description=self.description,
                required=self.required,
            )
        except ValidationError as exc:
            parameter_name = exc.errors()[0]["loc"][0]
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=self.name,
                parameter_name=parameter_name,
                parameter_type=str(
                    get_type_hints(_BaseOptionParametersModel)[parameter_name]
                ),
            ) from None

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
