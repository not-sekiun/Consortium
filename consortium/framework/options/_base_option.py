from abc import ABC, abstractmethod
from typing import get_type_hints

from pydantic import BaseModel, JsonValue, ValidationError

from consortium.framework._core.framework_exceptions.options_framework_exceptions import (
    EmptyOptionNameError,
    InvalidDefaultValueError,
    InvalidOptionConfigurationParameterTypeError,
    OptionValueValidationError,
)
from consortium.framework._core.utils import (
    resolve_component_filepath,
    resolve_validation_error_parameter,
)
from consortium.framework.options.option_types import OptionType


# Ignore validating the default value type here because each option type will
# have its own specific validation logic for the default value.
class _BaseOptionParametersModel(BaseModel):
    name: str
    description: str
    required: bool


class BaseOption[ValueType](ABC):
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
        self.name: str = name
        self.description: str = description
        self.required: bool = required
        self.default_value: ValueType | None = default_value

        self._value: ValueType | None = None

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

    # Every concrete option type carries a different set of parameters, so each one
    # builds its own representation rather than inheriting one from here.
    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def validate_value(self, value: ValueType) -> None:
        """
        Validate the value of the option.

        Args:
            value: The value to validate.

        Raises:
            OptionValueValidationError: If the value is invalid.
        """

    @abstractmethod
    def to_json(self) -> dict[str, JsonValue]:
        """
        Convert the option to a JSON serializable dictionary.

        Returns:
            The JSON serializable dictionary representation of the option.
        """

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
                option_filepath=resolve_component_filepath(type(self)),
            )

        try:
            _BaseOptionParametersModel(
                name=self.name,
                description=self.description,
                required=self.required,
            )
        except ValidationError as exc:
            parameter_name, parameter_type = resolve_validation_error_parameter(
                exc=exc,
                parameter_types=get_type_hints(_BaseOptionParametersModel),
            )
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=self.name,
                parameter_name=parameter_name,
                parameter_type=parameter_type,
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
