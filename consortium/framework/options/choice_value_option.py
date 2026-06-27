from typing import get_type_hints

from pydantic import BaseModel, JsonValue, ValidationError

from consortium.framework.framework_types import Primitive
from consortium.framework.options._base_option import BaseOption
from consortium.framework.options.option_types import OptionType
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    EmptyAvailableValuesError,
    InvalidOptionConfigurationParameterTypeError,
    OptionValueValidationError as OptionValueValidationFrameworkError,
)


class _ChoiceValueParametersModel(BaseModel):
    default_value: Primitive | None
    available_values: set[Primitive]


class ChoiceValueOption(BaseOption[Primitive]):
    """
    An option that allows the user to choose from a set of available values. The type of
    each choice is restricted to being a `str`, `int`, `float`, or `bool`. Only one
    choice can be selected at a time.

    Attributes:
        option_type: The type of the option.
        name: The human-readable name of the option. The name cannot be an empty
            string.
        description: A description of the option.
        required: Whether the option is required or not. If True, the option must have
            a value set before it can be retrieved. If False, the option can be
            retrieved without a value being set.
        default_value: The default value of the option. If `None`, the option has no
            default value.
        available_values: The set of available values that the user can choose from. The
            type of each choice is restricted to being a `str`, `int`, `float`, or
            `bool`.

    Parameters:
        name: The human-readable name of the option. The name cannot be an empty
            string.
        description: A description of the option.
        required: Whether the option is required or not. If True, the option must have
            a value set before it can be retrieved. If False, the option can be
            retrieved without a value being set.
        default_value: The default value of the option. If `None`, the option has no
            default value.
        available_values: The set of available values that the user can choose from. The
            type of each choice is restricted to being a `str`, `int`, `float`, or
            `bool`.

    Example: Setting up a `ChoiceValueOption` with string values.
        ```python
        payload_format = ChoiceValueOption(
            name="payload_format",
            description="The output file format of the payload to compile to.",
            required=True,
            default_value="exe",
            available_values={"exe", "dll", "ps1"},
        )
        payload_format.validate_value("dll")
        payload_format.validate_value("not_a_valid_format")  # Will raise `OptionValueValidationError`
        ```
    """

    option_type: OptionType = OptionType.CHOICE_VALUE_OPTION
    """The type of the option."""

    def __init__(
        self,
        name: str,
        available_values: set[Primitive],
        description: str = "",
        required: bool = True,
        default_value: Primitive | None = None,
    ):
        self.available_values = available_values

        try:
            _ChoiceValueParametersModel(
                default_value=default_value,
                available_values=available_values,
            )
        except ValidationError as exc:
            parameter_name = exc.errors()[0]["loc"][0]
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=name,
                parameter_name=parameter_name,
                parameter_type=str(
                    get_type_hints(_ChoiceValueParametersModel)[parameter_name]
                ),
            ) from None

        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __repr__(self) -> str:
        return (
            f"ChoiceValueOption(name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"available_values={self.available_values!r})"
        )

    def validate_value(self, value: Primitive) -> None:
        if value not in self.available_values:
            raise OptionValueValidationFrameworkError(
                f"Value `{value}` for option `{self.name}` is not one of its available "
                f"choice values {self.available_values}.",
            )

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "available_values": list(self.available_values),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        if not self.available_values:
            raise EmptyAvailableValuesError(
                option_name=self.name,
            )
