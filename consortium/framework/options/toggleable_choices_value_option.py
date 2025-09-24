from consortium.framework.options import OptionType
from consortium.framework.options._base_option import BaseOption
from consortium.framework.options._option_argument_validators import (
    ArgumentDataTypeCheckParameters,
    validate_arguments_data_types,
)
from consortium.framework.options.exceptions import (
    EmptyAvailableValuesError,
    OptionValueValidationError as OptionValueValidationFrameworkError,
)


class ToggleableChoicesValueOption(BaseOption):
    """
    An option that allows the user to toggle on (`True`) or off (`False`) a set of
    available values. The type of each toggleable choice is restricted to being a
    `str`. Multiple choices can be toggled on at the same time. The value set must be a
    dictionary with the keys being the available values and the values being a boolean
    indicating whether the choice is toggled on or off.

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
        default_value (dict[str, bool] | None):
            The default value of the option. If `None`, the option has no default value.
        available_values (set[str]):
            The set of available values that the user can toggle on or off. The type of
            each choice is restricted to being a `str`.

    Parameters:
        name (str):
            The human-readable name of the option. The name cannot be an empty string.
        description (str):
            A description of the option.
        required (bool):
            Whether the option is required or not. If True, the option must have a
            value set before it can be retrieved. If False, the option can be retrieved
            without a value being set.
        default_value (dict[str, bool] | None):
            The default value of the option. If `None`, the option has no default value.
        available_values (set[str]):
            The set of available values that the user can toggle on or off. The type of
            each choice is restricted to being a `str`.
    """

    option_type: OptionType = OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION

    def __init__(
        self,
        name: str,
        available_values: set[str],
        description: str = "",
        required: bool = True,
        default_value: dict[str, bool] | None = None,
    ):
        self.available_values = available_values
        """
        The set of available values that the user can toggle on or off. The type of
        each choice is restricted to being a `str`.
        """
        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __repr__(self) -> str:
        return (
            f"ToggleableChoicesValueOption(name={self.name!r}, "
            f"description={self.description!r}, required={self.required!r}, "
            f"default_value={self.default_value!r}, "
            f"available_values={self.available_values!r})"
        )

    def validate_value(self, value: dict[str, bool]) -> None:
        """
        Validate the value of the option.

        Args:
            value (Any): The value to validate.

        Raises:
            OptionValueValidationFrameworkError: If the value is invalid.
        """
        if not isinstance(value, dict):
            raise OptionValueValidationFrameworkError(
                f"Value '{value}' for option '{self.name}' must be a dictionary.",
            )

        for key, value in value.items():
            if key not in self.available_values:
                raise OptionValueValidationFrameworkError(
                    f"Key '{key}' in dictionary value for option '{self.name}' is not "
                    f"one of its available choice values {self.available_values}.",
                )
            if not isinstance(value, bool):
                raise OptionValueValidationFrameworkError(
                    f"Value '{value}' for key '{key}' in dictionary value for option "
                    f"'{self.name}' is not a boolean.",
                )

    def to_json(self) -> dict[str, str | bool | dict[str, bool] | list[str] | None]:
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
