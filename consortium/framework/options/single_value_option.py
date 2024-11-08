from typing import Callable, Type

from consortium.framework.options.base_option import BaseOption
from consortium.framework.options.option_argument_validators import (
    validate_numeric_range_arguments,
    validate_string_length_arguments,
    validate_validating_function_argument,
    validate_validating_regex_argument,
    validate_value_type_argument,
)
from consortium.framework.options.option_types import OptionType
from consortium.framework.options.option_value_validators import (
    validate_value_data_type,
    validate_value_numeric_range,
    validate_value_on_validating_function,
    validate_value_regex_format,
    validate_value_string_length,
)
from consortium.framework.options.types import SimpleType, SimpleTypeType
from consortium.framework.options.utils import resolve_validating_function_string


class SingleValueOption(BaseOption):
    """
    An option that can only have a single value. This single value can only be of type
    `str`, `int`, `float`, or `bool`.

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
        default_value (str | int | float | bool | None):
            The default value of the option. If `None`, the option has no default value.
        value_type (Type[str] | Type[int] | Type[float] | Type[bool] | None):
            The type of the value that the option can accept. If `None`, the option can
            accept values of type `str`, `int`, `float`, or `bool`.
        minimum_length (int | None):
            If `value_type` is of type `str`, this parameter specifies the minimum
            length of the string value that the option can accept.  If `None`, there is
            no minimum length.
        maximum_length (int | None):
            If `value_type` is of type `str`, this parameter specifies the maximum
            length of the string value that the option can accept. If `None`, there is
            no maximum length.
        greater_than (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be greater than this value.
        lesser_than (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be lesser than this value.
        greater_than_or_equal_to (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be greater than or equal to this value.
        lesser_than_or_equal_to (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be lesser than or equal to this value.
        validating_regex (str | None):
            If `value_type` is of type `str`, this parameter specifies a regex pattern
            that the string value must match.
        validating_function (Callable[[str | int | float | bool], None] | None):
            A function that accepts a single argument, the value of the option, and
            raises an exception, `OptionValueValidationError`, if the value is invalid.
            If `None`, no additional validation is performed.

    Parameters:
        name (str):
            The human-readable name of the option. The name cannot be an empty string.
        description (str):
            A description of the option.
        required (bool):
            Whether the option is required or not. If True, the option must have a
            value set before it can be retrieved. If False, the option can be retrieved
            without a value being set.
        default_value (str | int | float | bool | None):
            The default value of the option. If `None`, the option has no default value.
        value_type (Type[str] | Type[int] | Type[float] | Type[bool] | None):
            The type of the value that the option can accept. If `None`, the option can
            accept values of type `str`, `int`, `float`, or `bool`.
        minimum_length (int | None):
            If `value_type` is of type `str`, this parameter specifies the minimum
            length of the string value that the option can accept.  If `None`, there is
            no minimum length.
        maximum_length (int | None):
            If `value_type` is of type `str`, this parameter specifies the maximum
            length of the string value that the option can accept. If `None`, there is
            no maximum length.
        greater_than (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be greater than this value.
        lesser_than (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be lesser than this value.
        greater_than_or_equal_to (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be greater than or equal to this value.
        lesser_than_or_equal_to (int | None):
            If `value_type` is of type `int` or `float`, the numeric value of the
            option must be lesser than or equal to this value.
        validating_regex (str | None):
            If `value_type` is of type `str`, this parameter specifies a regex pattern
            that the string value must match.
        validating_function (Callable[[str | int | float | bool], None] | None):
            A function that accepts a single argument, the value of the option, and
            raises an exception, `OptionValueValidationError` if the value is invalid.
            If `None`, no additional validation is performed.

    Example: Setting up a `SingleValueOption` with numeric value constraints
        ```python
        local_port = SingleValueOption(
            name="local_port",
            description="The port that the server listens on.",
            required=True,
            default_value=8080,
            value_type=int,
            greater_than=1024,
            lesser_than=65536,
        )
        local_port.set_option_value(80)  # Will raise `OptionValueValidationError`
        local_port.set_option_value(65535)
        ```

    Example: Setting up a `SingleValueOption` with string value constraints
        ```python
        local_host_address = SingleValueOption(
            name="local_host_address",
            description="The local host as an IPV4 address that the server listens on.",
            required=True,
            default_value="127.0.0.1",
            value_type=str,
            validating_regex=r"^((25[0-5]|(2[0-4]|1\\d|[1-9]|)\\d)\\.?\\b){4}$",
        )
        local_host_address.set_option_value("0.0.0.0")
        local_host_address.set_option_value("not_an_ip_address")  # Will raise `OptionValueValidationError`
        ```
    """

    option_type: OptionType = OptionType.SINGLE_VALUE_OPTION
    """The type of the option."""

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
        value_type: SimpleTypeType | None = None,
        minimum_length: int | None = None,
        maximum_length: int | None = None,
        greater_than: int | None = None,
        lesser_than: int | None = None,
        greater_than_or_equal_to: int | None = None,
        lesser_than_or_equal_to: int | None = None,
        validating_regex: str | None = None,
        validating_function: Callable[[SimpleType], None] | None = None,
    ):
        self.value_type = value_type
        """
        he type of the value that the option can accept. If `None`, the option can
        accept values of type `str`, `int`, `float`, or `bool`.
        """
        self.minimum_length = minimum_length
        """
        If `value_type` is of type `str`, this parameter specifies the minimum
        length of the string value that the option can accept.  If `None`, there is
        no minimum length.
        """
        self.maximum_length = maximum_length
        """
        If `value_type` is of type `str`, this parameter specifies the maximum
        length of the string value that the option can accept. If `None`, there is
        no maximum length.
        """
        self.greater_than = greater_than
        """
        If `value_type` is of type `int` or `float`, the numeric value of the
        option must be greater than this value.
        """
        self.lesser_than = lesser_than
        """
        If `value_type` is of type `int` or `float`, the numeric value of the
        option must be lesser than this value.
        """
        self.greater_than_or_equal_to = greater_than_or_equal_to
        """
        If `value_type` is of type `int` or `float`, the numeric value of the
        option must be greater than or equal to this value.
        """
        self.lesser_than_or_equal_to = lesser_than_or_equal_to
        """
        If `value_type` is of type `int` or `float`, the numeric value of the
        option must be lesser than or equal to this value.
        """
        self.validating_regex = validating_regex
        """
        If `value_type` is of type `str`, this parameter specifies a regex pattern
        that the string value must match.
        """
        self.validating_function = validating_function
        """
        A function that accepts a single argument, the value of the option, and
        raises an exception, `OptionValueValidationError` if the value is invalid.
        If `None`, no additional validation is performed.
        """

        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __repr__(self) -> str:
        return (
            f"SingleValueOption(name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"value_type={self.value_type!r}, minimum_length={self.minimum_length!r}, "
            f"maximum_length={self.maximum_length!r}, "
            f"greater_than={self.greater_than!r}, lesser_than={self.lesser_than!r}, "
            f"greater_than_or_equal_to={self.greater_than_or_equal_to!r}, "
            f"lesser_than_or_equal_to={self.lesser_than_or_equal_to!r}, "
            f"validating_regex={self.validating_regex!r}, "
            f"validating_function={self.validating_function!r})"
        )

    def validate_value(self, value: SimpleType) -> None:
        """
        Validate the value of the option.

        Args:
            value (Any): The value to validate.

        Raises:
            OptionValueValidationFrameworkError: If the value is invalid.
        """
        validate_value_data_type(
            self.name,
            value,
            *([self.value_type] if self.value_type else [str, int, float, bool]),
        )
        validate_value_numeric_range(
            option_name=self.name,
            option_value=value,
            greater_than=self.greater_than,
            lesser_than=self.lesser_than,
            greater_than_or_equal_to=self.greater_than_or_equal_to,
            lesser_than_or_equal_to=self.lesser_than_or_equal_to,
        )
        validate_value_string_length(
            option_name=self.name,
            option_value=value,
            minimum_length=self.minimum_length,
            maximum_length=self.maximum_length,
        )
        validate_value_regex_format(
            option_name=self.name,
            option_value=value,
            validating_regex=self.validating_regex,
        )
        validate_value_on_validating_function(
            option_name=self.name,
            option_value=value,
            validating_function=self.validating_function,
        )

    def to_json(self) -> dict[str, SimpleType | None]:
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
            "value_type": self.value_type.__name__ if self.value_type else None,
            "minimum_length": self.minimum_length,
            "maximum_length": self.maximum_length,
            "greater_than": self.greater_than,
            "lesser_than": self.lesser_than,
            "greater_than_or_equal_to": self.greater_than_or_equal_to,
            "lesser_than_or_equal_to": self.lesser_than_or_equal_to,
            "validating_regex": self.validating_regex,
            "validating_function": resolve_validating_function_string(
                validating_function=self.validating_function,
            ),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        validate_value_type_argument(
            option_name=self.name,
            value_type=self.value_type,
        )
        validate_string_length_arguments(
            option_name=self.name,
            option_value_type=self.value_type,
            minimum_length=self.minimum_length,
            maximum_length=self.maximum_length,
        )
        validate_numeric_range_arguments(
            option_name=self.name,
            option_value_type=self.value_type,
            greater_than=self.greater_than,
            lesser_than=self.lesser_than,
            greater_than_or_equal_to=self.greater_than_or_equal_to,
            lesser_than_or_equal_to=self.lesser_than_or_equal_to,
        )
        validate_validating_regex_argument(
            option_name=self.name,
            validating_regex=self.validating_regex,
        )
        validate_validating_function_argument(
            option_name=self.name,
            validating_function_parameter_name="validating_function",
            validating_function=self.validating_function,
        )
