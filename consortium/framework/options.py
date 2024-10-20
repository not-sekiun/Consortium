import copy
import re
import sys
from abc import ABC, abstractmethod
from enum import StrEnum
from inspect import signature
from typing import Any, Callable, Type

from consortium.framework.exceptions.options_framework_exceptions import (
    OptionValueValidationError,
)
from consortium.server.exceptions.framework_exceptions.options_framework_exceptions import (
    EmptyAvailableValuesError,
    EmptyOptionNameError,
    InvalidDefaultValueError,
    InvalidValidatingRegexError,
    OptionConfigurationError,
    OptionConfigurationParameterTypeError,
    OptionValueValidationError as OptionValueValidationFrameworkError,
    RequiredOptionValueNotSetError,
)
from consortium.server.utils.formatter_utils import format_docstring_to_single_line

SimpleType = str | int | float | bool


def _validate_value_type_argument(
    option_name: str,
    value_type: Type[SimpleType],
) -> None:
    if value_type not in {str, int, float, bool}:
        raise OptionConfigurationParameterTypeError(
            error_message=(
                f"The parameter 'value_type' must be of type 'str', 'int', 'float', or "
                f"'bool' for option '{option_name}'."
            ),
        )


def _validate_validating_regex_argument(
    option_name: str,
    validating_regex: str,
) -> None:
    if not isinstance(validating_regex, str):
        raise OptionConfigurationParameterTypeError(
            parameter_name="validating_regex",
            parameter_type="str",
            option_name=option_name,
        )
    try:
        re.compile(validating_regex)
    except re.error as exc:
        raise InvalidValidatingRegexError(
            option_name=option_name,
            validating_regex=validating_regex,
            regex_error_message=str(exc),
        )


def _validate_validating_function_argument(
    option_name: str,
    validating_function_name: str,
    validating_function: Callable[[Any], None],
) -> None:
    if not isinstance(validating_function, Callable):
        raise OptionConfigurationParameterTypeError(
            option_name=option_name,
            parameter_name=validating_function_name,
            parameter_type="callable",
        )
    function_signature = signature(validating_function)
    if len(function_signature.parameters) != 1:
        raise OptionConfigurationParameterTypeError(
            error_message=(
                f"Failed to configure option. The parameter "
                f"'{validating_function_name}' must be a callable that accepts exactly"
                f"one argument for option '{option_name}'."
            ),
        )


def _resolve_validating_function_string(
    validating_function: Callable[[Any], None],
) -> str | None:
    # If a `validating_function` function is present, we want to display the docstring
    # of the function in the JSON output. If the function does not have a docstring, we
    # will display an empty string.
    if validating_function:
        if validating_function.__doc__:
            return format_docstring_to_single_line(
                docstring=validating_function.__doc__,
            )
        else:
            return ""
    # If no `validating_function` function is present, we will return `None` for the
    # corresponding JSON output.
    else:
        return None


# TODO: Add greater than, less than, greater than equal to, lesser than equal to,
#  maximum length and minimum length parameters/utility functions to streamline
#  standard.
class _BaseOption(ABC):
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
        self.description = description
        self.required = required
        self.default_value = default_value

        self._value = None

        try:
            self._validate_option_arguments()
        except OptionValueValidationFrameworkError as exc:
            raise OptionConfigurationError()

    @abstractmethod
    def validate_value(self, value: Any) -> None: ...

    @abstractmethod
    def to_json(self) -> dict[str, Any]: ...

    def get_option_value(self) -> Any:
        if self._value is None:
            if self.default_value is None:
                if self.required:
                    raise RequiredOptionValueNotSetError(
                        option_name=self.name,
                    )
                else:
                    return None
            return self.default_value
        return self._value

    def set_option_value(self, value: Any) -> None:
        self.validate_value(value)
        self._value = value

    def clear_option_value(self) -> None:
        self._value = None

    def _validate_option_arguments(self):
        if not isinstance(self.name, str):
            raise OptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="name",
                parameter_type="str",
            )
        if not self.name:
            raise EmptyOptionNameError(
                option_filepath=sys.modules[self.__module__].__file__,
            )
        if not isinstance(self.description, str):
            raise OptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(self.required, bool):
            raise OptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="required",
                parameter_type="bool",
            )
        if self.default_value is not None:
            try:
                self.validate_value(self.default_value)
            except OptionValueValidationFrameworkError as exc:
                raise InvalidDefaultValueError(
                    option_name=self.name,
                    default_value=self.default_value,
                    option_value_validation_error_message=str(exc),
                ) from None


class OptionType(StrEnum):
    SINGLE_VALUE_OPTION = "SINGLE_VALUE_OPTION"
    LIST_VALUE_OPTION = "LIST_VALUE_OPTION"
    CHOICE_VALUE_OPTION = "CHOICE_VALUE_OPTION"
    TOGGLEABLE_CHOICES_VALUE_OPTION = "TOGGLEABLE_CHOICES_VALUE_OPTION"
    DICTIONARY_VALUE_OPTION = "DICTIONARY_VALUE_OPTION"


class SingleValueOption(_BaseOption):
    option_type: OptionType = OptionType.SINGLE_VALUE_OPTION

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
        value_type: Type[SimpleType] | None = None,
        validating_regex: str | None = None,
        validating_function: Callable[[SimpleType], None] | None = None,
    ):
        self.value_type = value_type
        self.validating_regex = validating_regex
        self.validating_function = validating_function
        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __str__(self) -> str:
        try:
            value_display_string = repr(self.get_option_value())
        except RequiredOptionValueNotSetError:
            value_display_string = "UNDEFINED"
        return f"{self.option_type} - Name: {self.name}, Value: {value_display_string}"

    def __repr__(self) -> str:
        return (
            f"SingleValueOption(name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"value_type={self.value_type!r}, validating_regex={self.validating_regex!r}, "
            f"validating_function={self.validating_function!r})"
        )

    def validate_value(self, value: SimpleType) -> None:
        if not isinstance(value, (str, int, float, bool)):
            raise OptionValueValidationFrameworkError(
                f"Value '{value}' for option '{self.name}' must be of type str, int, "
                "float, or bool.",
            )
        if self.value_type:
            if not isinstance(value, self.value_type):
                raise OptionValueValidationFrameworkError(
                    f"Value '{value}' for option '{self.name}' failed against its "
                    f"type validation: {self.value_type}",
                )
        if self.validating_regex:
            if re.match(self.validating_regex, str(value)) is None:
                raise OptionValueValidationFrameworkError(
                    f"Value '{value}' for option '{self.name}' failed to match its "
                    f"validating regex: {self.validating_regex}",
                )
        if self.validating_function:
            try:
                self.validating_function(value)
            except OptionValueValidationError as exc:
                raise OptionValueValidationFrameworkError(
                    f"Value '{value}' for option '{self.name}' failed against its "
                    f"validating function: {exc}",
                ) from None

    def to_json(self) -> dict[str, SimpleType | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "value_type": self.value_type.__name__ if self.value_type else None,
            "validating_regex": self.validating_regex,
            "validating_function": _resolve_validating_function_string(
                validating_function=self.validating_function,
            ),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        if self.value_type:
            _validate_value_type_argument(
                option_name=self.name,
                value_type=self.value_type,
            )
        if self.validating_regex:
            _validate_validating_regex_argument(
                option_name=self.name,
                validating_regex=self.validating_regex,
            )
        if self.validating_function:
            try:
                _validate_validating_function_argument(
                    option_name=self.name,
                    validating_function_name="validating_function",
                    validating_function=self.validating_function,
                )
            except OptionValueValidationError as exc:
                raise OptionValueValidationFrameworkError(
                    message=exc.message,
                    detail=exc.detail,
                ) from None


class ListValueOption(_BaseOption):
    option_type: OptionType = OptionType.LIST_VALUE_OPTION

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: list[SimpleType] | None = None,
        allow_duplicates: bool = True,
        value_type: Type[SimpleType] | None = None,
        validating_regex: str | None = None,
        validating_function: Callable[[Any], None] | None = None,
    ):
        self.allow_duplicates = allow_duplicates
        self.value_type = value_type
        self.validating_regex = validating_regex
        self.validating_function = validating_function
        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __str__(self) -> str:
        try:
            value_display_string = repr(self.get_option_value())
        except RequiredOptionValueNotSetError:
            value_display_string = "UNDEFINED"
        return f"{self.option_type} - Name: {self.name}, Value: {value_display_string}"

    def __repr__(self) -> str:
        return (
            f"ListValueOption(name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"value_type={self.value_type!r}, "
            f"validating_regex={self.validating_regex!r}, "
            f"validating_function={self.validating_function!r})"
        )

    def get_option_value(self) -> list[SimpleType]:
        return copy.deepcopy(super().get_option_value())

    def validate_value(self, value: list[SimpleType]) -> None:
        if not isinstance(value, list):
            raise OptionValueValidationFrameworkError(
                f"Value '{value}' for option '{self.name}' must be a list.",
            )
        for element in value:
            if self.value_type:
                if not isinstance(element, self.value_type):
                    raise OptionValueValidationFrameworkError(
                        f"Element '{element}' in list value for option '{self.name}' "
                        f"failed against its type validation: {self.value_type}",
                    )
            if not isinstance(element, (str, int, float, bool)):
                raise OptionValueValidationFrameworkError(
                    f"Element '{element}' in list value for option '{self.name}' must "
                    "be of type str, int, float, or bool.",
                )
        if self.validating_regex:
            for element in value:
                if re.match(self.validating_regex, str(element)) is None:
                    raise OptionValueValidationFrameworkError(
                        f"Element '{element}' in list value for option '{self.name}' "
                        "failed to match its validating regex: "
                        f"{self.validating_regex}",
                    )
        if self.validating_function:
            for element in value:
                try:
                    self.validating_function(element)
                except OptionValueValidationError as exc:
                    raise OptionValueValidationFrameworkError(
                        message=(
                            f"Element '{element}' in list value for option "
                            f"'{self.name}' failed against its validating function. "
                            f"{exc}"
                        ),
                        detail=exc.detail,
                    ) from None
        if not self.allow_duplicates:
            unique_elements = set()
            for element in value:
                if element in unique_elements:
                    raise OptionValueValidationFrameworkError(
                        f"Element '{element}' in list value for option '{self.name}' "
                        f"contains duplicate copies while the option disallows "
                        "duplicate elements.",
                    )
                unique_elements.add(element)

    def to_json(
        self,
    ) -> dict[str, str | bool | list[SimpleType] | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "allow_duplicates": self.allow_duplicates,
            "value_type": self.value_type.__name__ if self.value_type else None,
            "validating_regex": self.validating_regex,
            "validating_function": _resolve_validating_function_string(
                validating_function=self.validating_function,
            ),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        if not isinstance(self.allow_duplicates, bool):
            raise OptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="allow_duplicates",
                parameter_type="bool",
            )
        if self.value_type:
            _validate_value_type_argument(
                option_name=self.name,
                value_type=self.value_type,
            )
        if self.validating_regex:
            _validate_validating_regex_argument(
                option_name=self.name,
                validating_regex=self.validating_regex,
            )
        if self.validating_function:
            _validate_validating_function_argument(
                option_name=self.name,
                validating_function_name="validating_function",
                validating_function=self.validating_function,
            )


class ChoiceValueOption(_BaseOption):
    option_type: OptionType = OptionType.CHOICE_VALUE_OPTION

    def __init__(
        self,
        name: str,
        available_values: set[SimpleType],
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
    ):
        self.available_values = available_values
        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __str__(self) -> str:
        try:
            value_display_string = repr(self.get_option_value())
        except RequiredOptionValueNotSetError:
            value_display_string = "UNDEFINED"

        return f"{self.option_type} - Name: {self.name}, Value: {value_display_string}"

    def __repr__(self) -> str:
        return (
            f"ChoiceValueOption(name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"available_values={self.available_values!r})"
        )

    def validate_value(self, value: SimpleType) -> None:
        if value not in self.available_values:
            raise OptionValueValidationFrameworkError(
                f"Value '{value}' for option '{self.name}' is not one of its available "
                f"choice values {self.available_values}.",
            )

    def to_json(self) -> dict[str, SimpleType | list[SimpleType] | None]:
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
        if not isinstance(self.available_values, set):
            raise OptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="available_values",
                parameter_type="set",
            )
        if not self.available_values:
            raise EmptyAvailableValuesError(
                option_name=self.name,
            )
        for element in self.available_values:
            if not isinstance(element, (str, int, float, bool)):
                raise OptionConfigurationParameterTypeError(
                    error_message=(
                        f"Failed to configure option. The parameter 'available_values' "
                        "must be a set containing elements of type 'str', 'int', "
                        "'float', or 'bool' "
                    ),
                )


class ToggleableChoicesValueOption(_BaseOption):
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
        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __str__(self) -> str:
        try:
            value_display_string = repr(self.get_option_value())
        except RequiredOptionValueNotSetError:
            value_display_string = "UNDEFINED"
        return f"{self.option_type} - Name: {self.name}, Value: {value_display_string}"

    def __repr__(self) -> str:
        return (
            f"ToggleableChoicesValueOption(name={self.name!r}, "
            f"description={self.description!r}, required={self.required!r}, "
            f"default_value={self.default_value!r}, "
            f"available_values={self.available_values!r})"
        )

    def validate_value(self, value: Any) -> None:
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
        if not isinstance(self.available_values, set):
            raise OptionConfigurationParameterTypeError(
                option_name=self.name,
                parameter_name="available_values",
                parameter_type="set",
            )
        if not self.available_values:
            raise EmptyAvailableValuesError(
                option_name=self.name,
            )
        for element in self.available_values:
            if not isinstance(element, (str, int, float, bool)):
                raise OptionConfigurationParameterTypeError(
                    error_message=(
                        "Failed to configure option. The parameter 'available_values' "
                        "must be a set containing elements of type 'str', 'int', "
                        "'float', or 'bool' "
                    ),
                )


class DictionaryValueOption(_BaseOption):
    option_type: OptionType = OptionType.DICTIONARY_VALUE_OPTION

    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: dict[str, SimpleType] | None = None,
        key_validating_regex: str | None = None,
        key_validating_function: Callable[[Any], None] | None = None,
        value_type: Type[SimpleType] | None = None,
        value_validating_regex: str | None = None,
        value_validating_function: Callable[[Any], None] | None = None,
        validating_function: Callable[[Any], None] | None = None,
    ):
        self.value_type = value_type
        self.key_validating_regex = key_validating_regex
        self.key_validating_function = key_validating_function
        self.value_validating_regex = value_validating_regex
        self.value_validating_function = value_validating_function
        self.validating_function = validating_function

        super().__init__(
            name=name,
            description=description,
            required=required,
            default_value=default_value,
        )

    def __str__(self) -> str:
        try:
            value_display_string = repr(self.get_option_value())
        except RequiredOptionValueNotSetError:
            value_display_string = "UNDEFINED"
        return f"{self.option_type} - Name: {self.name}, Value: {value_display_string}"

    def __repr__(self) -> str:
        return (
            f"DictionaryValueOption("
            f"name={self.name!r}, description={self.description!r}, "
            f"required={self.required!r}, default_value={self.default_value!r}, "
            f"key_validating_regex={self.key_validating_regex!r}, "
            f"key_validating_function={self.key_validating_function!r}, "
            f"value_type={self.value_type!r}, "
            f"value_validating_regex={self.value_validating_regex!r}, "
            f"value_validating_function={self.value_validating_function!r})"
            f"validating_function={self.validating_function!r})"
        )

    def get_option_value(self) -> dict[str, SimpleType]:
        return copy.deepcopy(super().get_option_value())

    def validate_value(self, value: dict[str, SimpleType]) -> None:
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
                    )
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
                    )
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
                )

    def to_json(
        self,
    ) -> dict[str, str | bool | dict[str, SimpleType] | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "key_validating_regex": self.key_validating_regex,
            "key_validating_function": _resolve_validating_function_string(
                validating_function=self.key_validating_function,
            ),
            "value_type": self.value_type.__name__ if self.value_type else None,
            "value_validating_regex": self.value_validating_regex,
            "value_validating_function": _resolve_validating_function_string(
                validating_function=self.value_validating_function,
            ),
            "validating_function": _resolve_validating_function_string(
                validating_function=self.validating_function,
            ),
            "option_type": str(self.option_type),
        }

    def _validate_option_arguments(self):
        super()._validate_option_arguments()
        if self.value_type:
            _validate_value_type_argument(
                option_name=self.name,
                value_type=self.value_type,
            )
        if self.key_validating_regex:
            _validate_validating_regex_argument(
                option_name=self.name,
                validating_regex=self.key_validating_regex,
            )
        if self.key_validating_function:
            _validate_validating_function_argument(
                option_name=self.name,
                validating_function_name="key_validating_function",
                validating_function=self.key_validating_function,
            )
        if self.value_validating_regex:
            _validate_validating_regex_argument(
                option_name=self.name,
                validating_regex=self.value_validating_regex,
            )
        if self.value_validating_function:
            _validate_validating_function_argument(
                option_name=self.name,
                validating_function_name="value_validating_function",
                validating_function=self.value_validating_function,
            )
        if self.validating_function:
            _validate_validating_function_argument(
                option_name=self.name,
                validating_function_name="validating_function",
                validating_function=self.validating_function,
            )
