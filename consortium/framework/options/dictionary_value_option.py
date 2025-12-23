import re
from collections.abc import Callable
from typing import get_type_hints

from pydantic import BaseModel, ValidationError

from consortium.framework._utils import resolve_validating_function_string
from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.framework.framework_types import Primitive, PrimitiveType
from consortium.framework.options._base_option import BaseOption
from consortium.framework.options._option_argument_validators import (
    validate_validating_function_argument,
    validate_validating_regex_argument,
)
from consortium.framework.options.option_types import OptionType
from consortium.server.exceptions.consortium_exceptions.options_consortium_exceptions import (
    InvalidOptionConfigurationParameterTypeError,
    OptionValueValidationError as OptionValueValidationFrameworkError,
)


class _DictionaryValueParametersModel(BaseModel):
    default_value: dict[str, Primitive] | None
    key_validating_regex: str | None
    key_validating_function: Callable[[str], None] | None
    value_type: PrimitiveType | None
    value_validating_regex: str | None
    value_validating_function: Callable[[Primitive], None] | None
    validating_function: Callable[[dict[str, Primitive]], None] | None


class DictionaryValueOption(BaseOption[dict[str, Primitive]]):
    """
    An option that contains a mapping of keys of type `str` to values of type
    `str`, `int`, `float`, or `bool`.

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
        key_validating_regex: This parameter specifies a regex pattern that each of the
            keys in the dictionary, which can only be of type `str`, must match.
        key_validating_function: A function that accepts a single argument, the keys of
            the dictionary, and raises an exception, `OptionValueValidationError`, if
            the value is invalid. If `None`, no additional validation is performed.
        value_type: The type of the value in the dictionary that the option can accept.
            If `None`, the dictionary can have values of type `str`, `int`, `float`, or
            `bool`.
        value_validating_regex: This parameter specifies a regex pattern that each of
            the values in the dictionary must match.
        value_validating_function: A function that accepts a single argument, the values
            of the dictionary, and raises an exception, `OptionValueValidationError`, if
            the value is invalid. If `None`, no additional validation is performed.
        validating_function: A function that accepts a single argument, the entire
            dictionary value of the option, and raises an exception,
            `OptionValueValidationError`, if the value is invalid. If `None`, no
            additional validation is performed.

    Parameters:
        name: The human-readable name of the option. The name cannot be an empty
            string.
        description: A description of the option.
        required: Whether the option is required or not. If True, the option must have
            a value set before it can be retrieved. If False, the option can be
            retrieved without a value being set.
        default_value: The default value of the option. If `None`, the option has no
            default value.
        key_validating_regex: This parameter specifies a regex pattern that each of the
            keys in the dictionary, which can only be of type `str`, must match.
        key_validating_function: A function that accepts a single argument, the keys of
            the dictionary, and raises an exception, `OptionValueValidationError`, if
            the value is invalid. If `None`, no additional validation is performed.
        value_type: The type of the value in the dictionary that the option can accept.
            If `None`, the dictionary can have values of type `str`, `int`, `float`, or
            `bool`.
        value_validating_regex: This parameter specifies a regex pattern that each of
            the values in the dictionary must match.
        value_validating_function: A function that accepts a single argument, the values
            of the dictionary, and raises an exception, `OptionValueValidationError`, if
            the value is invalid. If `None`, no additional validation is performed.
        validating_function: A function that accepts a single argument, the entire
            dictionary value of the option, and raises an exception,
            `OptionValueValidationError`, if the value is invalid. If `None`, no
            additional validation is performed.

    Example:
        ```python
        extra_headers = DictionaryValueOption(
            name="extra_headers",
            description=(
                "Extra headers to include in the HTTP request made by the agent when "
                "checking in with the listener."
            ),
            required=False,
            default_value={"User-Agent": "Mozilla/5.0"},
            value_type=str,
        )
        ```
    """

    option_type: OptionType = OptionType.DICTIONARY_VALUE_OPTION
    """
    The type of the option.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: dict[str, Primitive] | None = None,
        key_validating_regex: str | None = None,
        key_validating_function: Callable[[str], None] | None = None,
        value_type: PrimitiveType | None = None,
        value_validating_regex: str | None = None,
        value_validating_function: Callable[[Primitive], None] | None = None,
        validating_function: Callable[[dict[str, Primitive]], None] | None = None,
    ):
        self.key_validating_regex = key_validating_regex
        self.key_validating_function = key_validating_function
        self.value_type = value_type
        self.value_validating_regex = value_validating_regex
        self.value_validating_function = value_validating_function
        self.validating_function = validating_function

        try:
            _DictionaryValueParametersModel(
                default_value=default_value,
                key_validating_regex=key_validating_regex,
                key_validating_function=key_validating_function,
                value_type=value_type,
                value_validating_regex=value_validating_regex,
                value_validating_function=value_validating_function,
                validating_function=validating_function,
            )
        except ValidationError as exc:
            parameter_name = exc.errors()[0]["loc"][0]
            raise InvalidOptionConfigurationParameterTypeError(
                option_str=name,
                parameter_name=parameter_name,
                parameter_type=str(
                    get_type_hints(_DictionaryValueParametersModel)[parameter_name]
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
            f"DictionaryValueOption("
            f"name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"key_validating_regex={self.key_validating_regex!r}, "
            f"key_validating_function={self.key_validating_function!r}, "
            f"value_type={self.value_type!r}, "
            f"value_validating_regex={self.value_validating_regex!r}, "
            f"value_validating_function={self.value_validating_function!r}, "
            f"validating_function={self.validating_function!r}"
            f")"
        )

    def validate_value(self, value: dict[str, Primitive]) -> None:
        if not isinstance(value, dict):
            raise OptionValueValidationFrameworkError(
                f"Value '{value}' for option '{self.name}' must be a dictionary.",
            )

        for dict_key, dict_value in value.items():
            # The value of keys in DictionaryValueOption is always a string.
            if not isinstance(dict_key, str):
                raise OptionValueValidationFrameworkError(
                    f"Key '{dict_key}' in dictionary value for option '{self.name}' "
                    "failed against its key type validation: str",
                )
            if self.key_validating_regex:
                if re.match(self.key_validating_regex, str(dict_key)) is None:
                    raise OptionValueValidationFrameworkError(
                        f"Key '{dict_key}' in dictionary value for option "
                        f"'{self.name}' failed against its key validating regex: "
                        f"{self.key_validating_regex}",
                    )
            if self.key_validating_function:
                try:
                    self.key_validating_function(dict_key)
                except OptionValueValidationError as exc:
                    raise OptionValueValidationFrameworkError(
                        message=(
                            f"Key '{dict_key}' in dictionary value for option "
                            f"'{self.name}' failed against its key validating "
                            f"function: {exc}"
                        ),
                        detail=exc.detail,
                    ) from None
            if self.value_type:
                if not isinstance(dict_value, self.value_type):
                    raise OptionValueValidationFrameworkError(
                        f"Value '{dict_value}' in dictionary value for option "
                        f"'{self.name}' failed to match its value type validation: "
                        f"{self.value_type}",
                    )
            if self.value_validating_regex:
                if re.match(self.value_validating_regex, str(dict_value)) is None:
                    raise OptionValueValidationFrameworkError(
                        f"Value '{dict_value}' in dictionary value for option "
                        f"'{self.name}' failed to match its value validating regex: "
                        f"{self.value_validating_regex}",
                    )
            if self.value_validating_function:
                try:
                    self.value_validating_function(dict_value)
                except OptionValueValidationError as exc:
                    raise OptionValueValidationFrameworkError(
                        message=(
                            f"Value '{dict_value}' in dictionary value for option "
                            f"'{self.name}' failed against its value validating "
                            f"function: {exc}"
                        ),
                        detail=exc.detail,
                    ) from None
        if self.validating_function:
            try:
                self.validating_function(value)
            except OptionValueValidationError as exc:
                raise OptionValueValidationFrameworkError(
                    message=(
                        f"Value '{value}' in dictionary value for option '{self.name}' "
                        f"failed against its validating function: {exc}"
                    ),
                    detail=exc.detail,
                ) from None

    def to_json(
        self,
    ) -> dict[str, str | bool | dict[str, Primitive] | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "key_validating_regex": self.key_validating_regex,
            "key_validating_function": resolve_validating_function_string(
                validating_function=self.key_validating_function,
            ),
            "value_type": self.value_type.__name__ if self.value_type else None,
            "value_validating_regex": self.value_validating_regex,
            "value_validating_function": resolve_validating_function_string(
                validating_function=self.value_validating_function,
            ),
            "validating_function": resolve_validating_function_string(
                validating_function=self.validating_function,
            ),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        validate_validating_regex_argument(
            option_name=self.name,
            validating_regex=self.key_validating_regex,
            validating_regex_parameter_name="key_validating_regex",
        )
        validate_validating_function_argument(
            option_name=self.name,
            validating_function=self.key_validating_function,
            validating_function_parameter_name="key_validating_function",
        )
        validate_validating_regex_argument(
            option_name=self.name,
            validating_regex=self.value_validating_regex,
            validating_regex_parameter_name="value_validating_regex",
        )
        validate_validating_function_argument(
            option_name=self.name,
            validating_function=self.value_validating_function,
            validating_function_parameter_name="value_validating_function",
        )
        validate_validating_function_argument(
            option_name=self.name,
            validating_function=self.validating_function,
        )
