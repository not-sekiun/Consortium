from collections.abc import Callable
from typing import get_type_hints

from pydantic import BaseModel, ValidationError

from consortium.framework._utils import resolve_validating_function_string
from consortium.framework.framework_types import Primitive, PrimitiveType
from consortium.framework.options._base_option import BaseOption
from consortium.framework.options._option_argument_validators import (
    validate_iterable_length_arguments,
    validate_numeric_range_arguments,
    validate_string_length_arguments,
    validate_validating_function_argument,
    validate_validating_regex_argument,
)
from consortium.framework.options._option_value_validators import (
    validate_iterable_element_duplication,
    validate_iterable_value_length,
    validate_value_data_type,
    validate_value_numeric_range,
    validate_value_on_validating_function,
    validate_value_regex_format,
    validate_value_string_length,
)
from consortium.framework.options.option_types import OptionType
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    InvalidOptionConfigurationParameterTypeError,
)


class _ListValueParametersModel(BaseModel):
    default_value: list[Primitive] | None
    allow_duplicates: bool
    value_type: PrimitiveType | None
    minimum_length: int | None
    maximum_length: int | None
    greater_than: int | float | None
    less_than: int | float | None
    greater_than_or_equal_to: int | float | None
    less_than_or_equal_to: int | float | None
    minimum_elements: int | None
    maximum_elements: int | None
    validating_regex: str | None
    validating_function: Callable[[Primitive], None] | None


class ListValueOption(BaseOption[list[Primitive]]):
    """
    An option that can hold multiple values. Each element of the option can only be
    of type `str`, `int`, `float`, or `bool`. This type of the elements may be
    either homogeneous or heterogeneous.

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
        value_type: The type of the elements that the option can accept for the list
            value. If `None`, the list's content type is heterogeneous and each element
            can be any of `str`, `int`, `float`, or `bool` otherwise its content type is
            homogeneous and the content type of its elements can only be one of `str`,
            `int`, `float`, or `bool`.
        minimum_length: If `value_type` is of type `str`, this parameter specifies the
            minimum max_length of each string element that the option can accept.  If
            `None`, there is no minimum max_length.
        maximum_length: If `value_type` is of type `str`, this parameter specifies the
            maximum max_length of each string element that the option can accept. If
            `None`, there is no maximum max_length.
        greater_than: If `value_type` is of type `int` or `float`, the numeric value of
            each element of the option must be greater than this value.
        less_than: If `value_type` is of type `int` or `float`, the numeric value of
            each element of the option must be less than this value.
        greater_than_or_equal_to: If `value_type` is of type `int` or `float`, the
            numeric value of each element of the option must be greater than or equal
            to this value.
        less_than_or_equal_to: If `value_type` is of type `int` or `float`, the numeric
            value of each element of the option must be less than or equal to this
            value.
        minimum_elements: The minimum number of elements that the option can hold. If
            `None`, there is no minimum number of elements.
        maximum_elements: The maximum number of elements that the option can hold. If
            `None`, there is no maximum number of elements.
        validating_regex: If `value_type` is of type `str`, this parameter specifies a
            regex pattern that each element of the option must match.
        validating_function: A function that accepts a single argument, the value of the
            option, and raises an exception, `OptionValueValidationError` if the value
            is invalid. If `None`, no additional validation is performed.

    Parameters:
        name: The human-readable name of the option. The name cannot be an empty
            string.
        description: A description of the option.
        required: Whether the option is required or not. If True, the option must have
            a value set before it can be retrieved. If False, the option can be
            retrieved without a value being set.
        default_value: The default value of the option. If `None`, the option has no
            default value.
        value_type: The type of the elements that the option can accept for the list
            value. If `None`, the list's content type is heterogeneous and each element
            can be any of `str`, `int`, `float`, or `bool` otherwise its content type is
            homogeneous and the content type of its elements can only be one of `str`,
            `int`, `float`, or `bool`.
        minimum_length: If `value_type` is of type `str`, this parameter specifies the
            minimum max_length of each string element that the option can accept.  If
            `None`, there is no minimum max_length.
        maximum_length: If `value_type` is of type `str`, this parameter specifies the
            maximum max_length of each string element that the option can accept. If
            `None`, there is no maximum max_length.
        greater_than: If `value_type` is of type `int` or `float`, the numeric value of
            each element of the option must be greater than this value.
        less_than: If `value_type` is of type `int` or `float`, the numeric value of
            each element of the option must be less than this value.
        greater_than_or_equal_to: If `value_type` is of type `int` or `float`, the
            numeric value of each element of the option must be greater than or equal
            to this value.
        less_than_or_equal_to: If `value_type` is of type `int` or `float`, the numeric
            value of each element of the option must be less than or equal to this
            value.
        minimum_elements: The minimum number of elements that the option can hold. If
            `None`, there is no minimum number of elements.
        maximum_elements: The maximum number of elements that the option can hold. If
            `None`, there is no maximum number of elements.
        validating_regex: If `value_type` is of type `str`, this parameter specifies a
            regex pattern that each element of the option must match.
        validating_function: A function that accepts a single argument, the value of the
            option, and raises an exception, `OptionValueValidationError` if the value
            is invalid. If `None`, no additional validation is performed.

    Example: Setting up a `ListValueOption` with a homogeneous content type.
        ```python
        backup_hosts = ListValueOption(
            name="backup_hosts",
            description=(
                "The list of hosts as IPV4 addresses to attempt to connect to in "
                "case the main host is unreachable."
            ),
            required=True,
            default_value=["1.1.1.1", "2.2.2.2"],
            value_type=str,
            minimum_length=1,
            validating_regex=r"^((25[0-5]|(2[0-4]|1\\d|[1-9]|)\\d)\\.?\\b){4}$",
        )
        backup_hosts.set_option_value(["1.1.1.1", "2.2.2.2", "3.3.3.3"])  # A list of values is passed in to the option.
        backup_hosts.set_option_value(["not_an_ip_address", "2.2.2.2", "3.3.3.3"])  # Will raise `OptionValueValidationError`
        ```
    """

    option_type: OptionType = OptionType.LIST_VALUE_OPTION

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: list[Primitive] | None = None,
        allow_duplicates: bool = True,
        value_type: PrimitiveType | None = None,
        minimum_length: int | None = None,
        maximum_length: int | None = None,
        greater_than: int | float | None = None,
        less_than: int | float | None = None,
        greater_than_or_equal_to: int | float | None = None,
        less_than_or_equal_to: int | float | None = None,
        minimum_elements: int | None = None,
        maximum_elements: int | None = None,
        validating_regex: str | None = None,
        validating_function: Callable[[Primitive], None] | None = None,
    ):
        self.allow_duplicates = allow_duplicates
        self.value_type = value_type
        self.minimum_length = minimum_length
        self.maximum_length = maximum_length
        self.greater_than = greater_than
        self.less_than = less_than
        self.greater_than_or_equal_to = greater_than_or_equal_to
        self.less_than_or_equal_to = less_than_or_equal_to
        self.minimum_elements = minimum_elements
        self.maximum_elements = maximum_elements
        self.validating_regex = validating_regex
        self.validating_function = validating_function

        try:
            _ListValueParametersModel(
                default_value=default_value,
                allow_duplicates=allow_duplicates,
                value_type=value_type,
                minimum_length=minimum_length,
                maximum_length=maximum_length,
                greater_than=greater_than,
                less_than=less_than,
                greater_than_or_equal_to=greater_than_or_equal_to,
                less_than_or_equal_to=less_than_or_equal_to,
                minimum_elements=minimum_elements,
                maximum_elements=maximum_elements,
                validating_regex=validating_regex,
                validating_function=validating_function,
            )
        except ValidationError as exc:
            parameter_name = exc.errors()[0]["loc"][0]
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=name,
                parameter_name=parameter_name,
                parameter_type=str(
                    get_type_hints(_ListValueParametersModel)[parameter_name]
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
            f"ListValueOption(name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"value_type={self.value_type!r}, minimum_length={self.minimum_length!r}, "
            f"maximum_length={self.maximum_length!r}, "
            f"greater_than={self.greater_than!r}, less_than={self.less_than!r}, "
            f"greater_than_or_equal_to={self.greater_than_or_equal_to!r}, "
            f"less_than_or_equal_to={self.less_than_or_equal_to!r}, "
            f"minimum_elements={self.minimum_elements!r}, "
            f"maximum_elements={self.maximum_elements!r}, "
            f"validating_regex={self.validating_regex!r}, "
            f"validating_function={self.validating_function!r})"
        )

    def validate_value(self, value: list[Primitive]) -> None:
        validate_value_data_type(
            self.name,
            value,
            list,
        )
        validate_iterable_element_duplication(
            option_name=self.name,
            option_value=value,
            allow_duplicates=self.allow_duplicates,
        )
        validate_iterable_value_length(
            option_name=self.name,
            option_value=value,
            minimum_elements=self.minimum_elements,
            maximum_elements=self.maximum_elements,
        )

        for element in value:
            validate_value_data_type(
                self.name,
                element,
                *([self.value_type] if self.value_type else [str, int, float, bool]),
            )
            validate_value_numeric_range(
                option_name=self.name,
                option_value=element,
                greater_than=self.greater_than,
                less_than=self.less_than,
                greater_than_or_equal_to=self.greater_than_or_equal_to,
                less_than_or_equal_to=self.less_than_or_equal_to,
            )
            validate_value_string_length(
                option_name=self.name,
                option_value=element,
                minimum_length=self.minimum_length,
                maximum_length=self.maximum_length,
            )
            validate_value_regex_format(
                option_name=self.name,
                option_value=element,
                validating_regex=self.validating_regex,
            )
            validate_value_on_validating_function(
                option_name=self.name,
                option_value=element,
                validating_function=self.validating_function,
            )

    def to_json(
        self,
    ) -> dict[str, str | bool | list[Primitive] | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "allow_duplicates": self.allow_duplicates,
            "value_type": self.value_type.__name__ if self.value_type else None,
            "minimum_length": self.minimum_length,
            "maximum_length": self.maximum_length,
            "greater_than": self.greater_than,
            "less_than": self.less_than,
            "greater_than_or_equal_to": self.greater_than_or_equal_to,
            "less_than_or_equal_to": self.less_than_or_equal_to,
            "minimum_elements": self.minimum_elements,
            "maximum_elements": self.maximum_elements,
            "validating_regex": self.validating_regex,
            "validating_function": resolve_validating_function_string(
                validating_function=self.validating_function,
            ),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
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
            less_than=self.less_than,
            greater_than_or_equal_to=self.greater_than_or_equal_to,
            less_than_or_equal_to=self.less_than_or_equal_to,
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
        validate_iterable_length_arguments(
            option_name=self.name,
            minimum_elements=self.minimum_elements,
            maximum_elements=self.maximum_elements,
        )
