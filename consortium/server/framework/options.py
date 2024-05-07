import copy
import re
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Callable, Type

from consortium.server.utils.string_processing_utils import (
    docstring_to_single_line_formatter,
)

SimpleType = str | int | float | bool

# TODO:
#  - Figure out a more aesthetic __str__
#  - Add type validation in __init__ at instantiation time


class OptionType(StrEnum):
    SINGLE_VALUE_OPTION = "SINGLE_VALUE_OPTION"
    LIST_VALUE_OPTION = "LIST_VALUE_OPTION"
    CHOICE_VALUE_OPTION = "CHOICE_VALUE_OPTION"
    TOGGLEABLE_CHOICES_VALUE_OPTION = "TOGGLEABLE_CHOICES_VALUE_OPTION"
    DICTIONARY_VALUE_OPTION = "DICTIONARY_VALUE_OPTION"


class _BaseOption(ABC):
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: Any | None = None,
    ):
        self.name = name
        self.description = description
        self.required = required

        self._value = None
        if default_value is not None:
            try:
                self.validate_value(default_value)
            except ValueError as exc:
                raise ValueError(
                    f'Default value "{default_value}" for option "{self.name}" failed '
                    f"validation: {exc}",
                )
        self.default_value = default_value

    def get_option_value(self) -> Any:
        if self._value is None:
            if self.default_value is None:
                raise ValueError(
                    f'No value was not set for the option "{self.name}" while the '
                    f"default value was also not set",
                )
            return self.default_value
        return self._value

    def set_option_value(self, value: Any) -> None:
        try:
            self.validate_value(value)
            self._value = value
        except ValueError as exc:
            raise exc

    def clear_option_value(self) -> None:
        self._value = None

    @abstractmethod
    def validate_value(self, value: Any) -> None: ...

    @abstractmethod
    def to_json(self) -> dict[str, Any]: ...


class SingleValueOption(_BaseOption):
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
        value_type: Type[SimpleType] | None = None,
        validating_regex: str | None = None,
        validating_function: Callable[[Any], None] | None = None,
    ):
        self.option_type = OptionType.SINGLE_VALUE_OPTION
        self.value_type = value_type
        self.validating_regex = validating_regex
        self.validating_function = validating_function
        super().__init__(name, description, required, default_value)

    def validate_value(self, value: SimpleType) -> None:
        if self.value_type:
            if not isinstance(value, self.value_type):
                raise ValueError(
                    f'Value "{value}" for option "{self.name}" failed against its '
                    f"type validation: {self.value_type}",
                )
        if self.validating_regex:
            if re.match(self.validating_regex, str(value)) is None:
                raise ValueError(
                    f'Value "{value}" for option "{self.name}" failed to match its '
                    f"validating regex: {self.validating_regex}",
                )
        if self.validating_function:
            try:
                self.validating_function(value)
            except ValueError as exc:
                raise ValueError(
                    f'Value "{value}" for option "{self.name}" failed against its '
                    f"validating function: {exc}",
                )

    def to_json(self) -> dict[str, SimpleType | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "value_type": self.value_type.__name__ if self.value_type else None,
            "validating_regex": self.validating_regex,
            "validating_function": docstring_to_single_line_formatter(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
            "option_type": str(self.option_type),
        }

    def __str__(self) -> str:
        return (
            f"{self.option_type} - Name: {self.name}, Value: {self.get_option_value()}"
        )

    def __repr__(self) -> str:
        return (
            f"SingleValueOption(name={self.name}, description={self.description}, "
            f"required={self.required}, default_value={self.default_value}, "
            f"value_type={self.value_type}, validating_regex={self.validating_regex}, "
            f"validating_function={self.validating_function})"
        )


class ListValueOption(_BaseOption):
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
        self.option_type = OptionType.LIST_VALUE_OPTION
        self.allow_duplicates = allow_duplicates
        self.value_type = value_type
        self.validating_regex = validating_regex
        self.validating_function = validating_function
        super().__init__(name, description, required, default_value)

    def get_option_value(self) -> list[SimpleType]:
        return copy.deepcopy(super().get_option_value())

    def validate_value(self, value: list[SimpleType]) -> None:
        if not isinstance(value, list):
            raise ValueError(
                f'Value "{value}" for option "{self.name}" must be a list.',
            )

        if self.value_type:
            for element in value:
                if not isinstance(element, self.value_type):
                    raise ValueError(
                        f'Element "{element}" in list value for option "{self.name}" '
                        f"failed against its type validation: {self.value_type}",
                    )
        if self.validating_regex:
            for element in value:
                if re.match(self.validating_regex, str(element)) is None:
                    raise ValueError(
                        f'Element "{element}" in list value for option "{self.name}" '
                        "failed to match its validating regex: "
                        f"{self.validating_regex}",
                    )
        if self.validating_function:
            for element in value:
                try:
                    self.validating_function(element)
                except ValueError as exc:
                    raise ValueError(
                        f'Element "{element}" in list value for option "{self.name}" '
                        f"failed against its validating function: {exc}",
                    )
        if not self.allow_duplicates:
            unique_elements = set()
            for element in value:
                if element in unique_elements:
                    raise ValueError(
                        f'Element "{element}"" in list value for option "{self.name}" '
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
            "validating_function": docstring_to_single_line_formatter(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
            "option_type": str(self.option_type),
        }

    def __str__(self) -> str:
        return (
            f"{self.option_type} - Name: {self.name}, Value: {self.get_option_value()}"
        )

    def __repr__(self) -> str:
        return (
            f"ListValueOption(name={self.name}, description={self.description}, "
            f"required={self.required}, default_value={self.default_value}, "
            f"value_type={self.value_type}, validating_regex={self.validating_regex}, "
            f"validating_function={self.validating_function})"
        )


class ChoiceValueOption(_BaseOption):
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
        available_values: set[SimpleType] = None,
    ):
        self.option_type = OptionType.CHOICE_VALUE_OPTION
        self.available_values = available_values
        super().__init__(name, description, required, default_value)

    def validate_value(self, value: SimpleType) -> None:
        if value not in self.available_values:
            raise ValueError(
                f'Value "{value}" for option "{self.name}" is not one of its available '
                f"choice values {self.available_values}.",
            )

    def to_json(self) -> dict[str, SimpleType | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "available_values": list(self.available_values),
            "option_type": str(self.option_type),
        }

    def __str__(self) -> str:
        return (
            f"{self.option_type} - Name: {self.name}, Value: {self.get_option_value()}"
        )

    def __repr__(self) -> str:
        return (
            f"ChoiceValueOption(name={self.name}, description={self.description}, "
            f"required={self.required}, default_value={self.default_value}, "
            f"available_values={self.available_values})"
        )


class ToggleableChoicesValueOption(_BaseOption):
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: dict[str, bool] | None = None,
        available_values: set[str] = None,
    ):
        self.option_type = OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION
        self.available_values = available_values
        super().__init__(name, description, required, default_value)

    def validate_value(self, value: Any) -> None:
        if not isinstance(value, dict):
            raise ValueError(
                f'Value "{value}" for option "{self.name}" must be a dictionary.',
            )

        for key, value in value.items():
            if key not in self.available_values:
                raise ValueError(
                    f'Key "{key}" in dictionary value for option "{self.name}" is not '
                    f"one of its available choice values {self.available_values}.",
                )
            if not isinstance(value, bool):
                raise ValueError(
                    f'Value "{value}" for key "{key}" in dictionary value for option '
                    f'"{self.name}" is not a boolean.',
                )

    def to_json(self) -> dict[str, str | bool | dict[str, bool] | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "available_values": list(self.available_values),
            "option_type": str(self.option_type),
        }

    def __str__(self) -> str:
        return (
            f"{self.option_type} - Name: {self.name}, Value: {self.get_option_value()}"
        )

    def __repr__(self) -> str:
        return (
            f"ToggleableChoicesValueOption(name={self.name}, "
            f"description={self.description}, required={self.required}, "
            f"default_value={self.default_value}, "
            f"available_values={self.available_values})"
        )


class DictionaryValueOption(_BaseOption):
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
        if value_type is not None and not issubclass(
            value_type,
            (str, int, float, bool),
        ):
            raise ValueError(
                f'Value type {value_type} for option "{self.name}" is not a valid '
                "type (str, int, float, bool).",
            )

        self.value_type = value_type
        self.key_validating_regex = key_validating_regex
        self.key_validating_function = key_validating_function
        self.value_validating_regex = value_validating_regex
        self.value_validating_function = value_validating_function
        self.validating_function = validating_function
        self.option_type = OptionType.DICTIONARY_VALUE_OPTION
        super().__init__(name, description, required, default_value)

    def get_option_value(self) -> dict[str, SimpleType]:
        return copy.deepcopy(super().get_option_value())

    def validate_value(self, value: dict[str, SimpleType]) -> None:
        if not isinstance(value, dict):
            raise ValueError(
                f'Value "{value}" for option "{self.name}" must be a dictionary.',
            )

        for dict_key, dict_value in value.items():
            # The value of keys in DictionaryValueOption is always a string.
            if not isinstance(dict_key, str):
                raise ValueError(
                    f'Key "{dict_key}" in dictionary value for option "{self.name}" '
                    "failed against its key type validation: str",
                )
            if self.key_validating_regex:
                if re.match(self.key_validating_regex, str(dict_key)) is None:
                    raise ValueError(
                        f'Key "{dict_key}" in dictionary value for option '
                        f'"{self.name}" failed against its key validating regex: '
                        f"{self.key_validating_regex}",
                    )
            if self.key_validating_function:
                try:
                    self.key_validating_function(dict_key)
                except ValueError as exc:
                    raise ValueError(
                        f'Key "{dict_key}" in dictionary value for option '
                        f'"{self.name}" failed against its key validating function: '
                        f"{exc}",
                    )
            if self.value_type:
                if not isinstance(dict_value, self.value_type):
                    raise ValueError(
                        f'Value "{dict_value}" in dictionary value for option '
                        f'"{self.name}" failed to match its value type validation: '
                        f"{self.value_type}",
                    )
            if self.value_validating_regex:
                if re.match(self.value_validating_regex, str(dict_value)) is None:
                    raise ValueError(
                        f'Value "{dict_value}" in dictionary value for option '
                        f'"{self.name}" failed to match its value validating regex: '
                        f"{self.value_validating_regex}",
                    )
            if self.value_validating_function:
                try:
                    self.value_validating_function(dict_value)
                except ValueError as exc:
                    raise ValueError(
                        f'Value "{dict_value}" in dictionary value for option '
                        '"{self.name}" failed against its value validating function: '
                        f"{exc}",
                    )
        if self.validating_function:
            try:
                self.validating_function(value)
            except ValueError as exc:
                raise ValueError(
                    f'Value "{value}" in dictionary value for option "{self.name}" '
                    f"failed against its validating function: {exc}",
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
            "key_validating_function": docstring_to_single_line_formatter(
                self.key_validating_function.__doc__,
            )
            if self.key_validating_function and self.key_validating_function.__doc__
            else None,
            "value_type": self.value_type.__name__ if self.value_type else None,
            "value_validating_regex": self.value_validating_regex,
            "value_validating_function": docstring_to_single_line_formatter(
                self.value_validating_function.__doc__,
            )
            if self.value_validating_function and self.value_validating_function.__doc__
            else None,
            "validating_function": docstring_to_single_line_formatter(
                self.validating_function.__doc__,
            )
            if self.validating_function and self.validating_function.__doc__
            else None,
            "option_type": str(self.option_type),
        }

    def __str__(self) -> str:
        return (
            f"{self.option_type} - Name: {self.name}, Value: {self.get_option_value()}"
        )

    def __repr__(self) -> str:
        return (
            f"DictionaryValueOption("
            f"name={self.name}, description={self.description}, "
            f"required={self.required}, default_value={self.default_value}, "
            f"key_validating_regex={self.key_validating_regex}, "
            f"key_validating_function={self.key_validating_function}, "
            f"value_type={self.value_type}, "
            f"value_validating_regex={self.value_validating_regex}, "
            f"value_validating_function={self.value_validating_function})"
            f"validating_function={self.validating_function})"
        )
