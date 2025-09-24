from consortium.framework.options._base_option import BaseOption
from consortium.framework.options._option_argument_validators import (
    ArgumentDataTypeCheckParameters,
    validate_arguments_data_types,
)
from consortium.framework.options.exceptions import (
    EmptyAvailableValuesError,
    OptionValueValidationError as OptionValueValidationFrameworkError,
)
from consortium.framework.options.option_types import OptionType

SimpleType = str | int | float | bool


class ChoiceValueOption(BaseOption):
    """
    An option that allows the user to choose from a set of available values. The type of
    each choice is restricted to being a `str`, `int`, `float`, or `bool`. Only one
    choice can be selected at a time.

    Attributes:
        option_type (OptionType):
            The type of the option.
        name (str):
            The human-readable name of the option. The name cannot be an empty string.
        description (str):
            A description of the option.
        required (bool):
            Whether the option is required or not. If True, the option must have a
            value set before it can be retrieved. If False, the option can be retrieved
            without a value being set.
        default_value (SimpleType | None):
            The default value of the option. If `None`, the option has no default value.
        available_values (set[SimpleType]):
            The set of available values that the user can choose from. The type of each
            choice is restricted to being a `str`, `int`, `float`, or `bool`.

    Parameters:
        name (str):
            The human-readable name of the option. The name cannot be an empty string.
        description (str):
            A description of the option.
        required (bool):
            Whether the option is required or not. If True, the option must have a
            value set before it can be retrieved. If False, the option can be retrieved
            without a value being set.
        default_value (SimpleType | None):
            The default value of the option. If `None`, the option has no default value.
        available_values (set[SimpleType]):
            The set of available values that the user can choose from. The type of each
            choice is restricted to being a `str`, `int`, `float`, or `bool`.

    Example: Setting up a `ChoiceValueOption` with string values.
        ```python
        payload_format = ChoiceValueOption(
            name="payload_format",
            description="The output file format of the payload to compile to.",
            required=True,
            default_value="exe",
            available_values={"exe", "dll", "ps1"},
        )
        payload_format.set_option_value("dll")
        payload_format.set_option_value("not_a_valid_format")  # Will raise `OptionValueValidationError`
        ```
    """

    option_type: OptionType = OptionType.CHOICE_VALUE_OPTION
    """The type of the option."""

    def __init__(
        self,
        name: str,
        available_values: set[SimpleType],
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
    ):
        self.available_values = available_values
        """
        The set of available values that the user can choose from. The type of each
        choice is restricted to being a `str`, `int`, `float`, or `bool`.
        """
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

    def validate_value(self, value: SimpleType) -> None:
        """
        Validate the value of the option.

        Args:
            value (Any): The value to validate.

        Raises:
            OptionValueValidationFrameworkError: If the value is invalid.
        """
        if value not in self.available_values:
            raise OptionValueValidationFrameworkError(
                f"Value `{value}` for option `{self.name}` is not one of its available "
                f"choice values {self.available_values}.",
            )

    def to_json(self) -> dict[str, SimpleType | list[SimpleType] | None]:
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
            "available_values": list(self.available_values),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        validate_arguments_data_types(
            self.name,
            ArgumentDataTypeCheckParameters(
                value=self.available_values,
                expected_data_type=set,
            ),
        )
        if not self.available_values:
            raise EmptyAvailableValuesError(
                option_name=self.name,
            )
        for element in self.available_values:
            validate_arguments_data_types(
                self.name,
                ArgumentDataTypeCheckParameters(
                    value=element,
                    expected_data_type={str, int, float, bool},
                ),
            )
