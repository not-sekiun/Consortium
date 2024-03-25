import copy
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Type

SimpleType = str | int | float | bool


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
            self.validate_value(default_value)
        self.default_value = default_value

    def get_option_value(self) -> Any:
        if self._value is None:
            if self.default_value is None:
                raise ValueError(
                    f'No value was not set for the option "{self.name}" while the default value was also not set',
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
        self.value_type = value_type
        self.validating_regex = validating_regex
        self.validating_function = validating_function
        super().__init__(name, description, required, default_value)

    def validate_value(self, value: SimpleType) -> None:
        if self.value_type:
            if not isinstance(value, self.value_type):
                raise ValueError(
                    f'Value "{value}" failed against the option "{self.name}" type validation: {self.value_type}',
                )
        if self.validating_regex:
            if re.match(self.validating_regex, str(value)) is None:
                raise ValueError(
                    f'Value "{value}" failed to match the option "{self.name}" validating regex: {self.validating_regex}',
                )
        if self.validating_function:
            try:
                self.validating_function(value)
            except ValueError as exc:
                raise ValueError(
                    f'Value "{value}" failed against the option "{self.name}" validating function: {exc}',
                )

    def to_json(self) -> dict[str, SimpleType | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "value_type": self.value_type.__name__ if self.value_type else None,
            "validating_regex": self.validating_regex,
            "validating_function": (
                self.validating_function.__doc__ if self.validating_function else None
            ),
        }


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
        self.allow_duplicates = allow_duplicates
        self.value_type = value_type
        self.validating_regex = validating_regex
        self.validating_function = validating_function
        super().__init__(name, description, required, default_value)

    def get_option_value(self) -> list[SimpleType]:
        return copy.deepcopy(super().get_option_value())

    def validate_value(self, value: list[SimpleType]) -> None:
        if self.value_type:
            for element in value:
                if not isinstance(element, self.value_type):
                    raise ValueError(
                        f'Element {element} in value failed against the option "{self.name}" type validation: {self.value_type}',
                    )
        if self.validating_regex:
            for element in value:
                if re.match(self.validating_regex, str(element)) is None:
                    raise ValueError(
                        f'Element {element} in value failed to match the option "{self.name}" validating regex: {self.validating_regex}',
                    )
        if self.validating_function:
            for element in value:
                try:
                    self.validating_function(element)
                except ValueError as exc:
                    raise ValueError(
                        f'Element {element} in value failed against the option "{self.name}" validating function: {exc}',
                    )
        if not self.allow_duplicates:
            unique_elements = set()
            for element in value:
                if element in unique_elements:
                    raise ValueError(
                        f'Element {element} in value is contains duplicate copies for option "{self.name}" while the option disallows duplicate elements',
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
            "validating_function": (
                self.validating_function.__doc__ if self.validating_function else None
            ),
        }


class ChoiceValueOption(_BaseOption):
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: SimpleType | None = None,
        available_values: list[SimpleType] = None,
    ):
        self.available_values = available_values
        super().__init__(name, description, required, default_value)

    def validate_value(self, value: SimpleType) -> None:
        if value not in self.available_values:
            raise ValueError(
                f'Value "{value}" is not one of the available choice values {self.available_values}',
            )

    def to_json(self) -> dict[str, SimpleType | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "available_values": self.available_values,
        }


class DictionaryValueOption(_BaseOption):
    def __init__(
        self,
        name: str,
        description: str = "",
        required: bool = True,
        default_value: dict[str, SimpleType] | None = None,
        key_type: Type[SimpleType] | None = None,
        key_validating_regex: str | None = None,
        key_validating_function: Callable[[Any], None] | None = None,
        value_type: Type[SimpleType] | None = None,
        value_validating_regex: str | None = None,
        value_validating_function: Callable[[Any], None] | None = None,
    ):
        self.value_type = value_type
        self.value_validating_regex = value_validating_regex
        self.value_validating_function = value_validating_function
        self.key_type = key_type
        self.key_validating_regex = key_validating_regex
        self.key_validating_function = key_validating_function
        super().__init__(name, description, required, default_value)

    def get_option_value(self) -> dict[str, SimpleType]:
        return copy.deepcopy(super().get_option_value())

    def validate_value(self, value: dict[str, SimpleType]) -> None:
        for dict_key, dict_value in value.items():
            if self.key_type:
                if not isinstance(dict_key, self.key_type):
                    raise ValueError(
                        f'Key {dict_key} in value failed against the option "{self.name}" type validation: {self.key_type}',
                    )
            if self.key_validating_regex:
                if re.match(self.key_validating_regex, str(dict_key)) is None:
                    raise ValueError(
                        f'Key {dict_key} in value failed to match the option "{self.name}" validating regex: {self.key_validating_regex}',
                    )
            if self.key_validating_function:
                try:
                    self.key_validating_function(dict_key)
                except ValueError as exc:
                    raise ValueError(
                        f'Key {dict_key} in value failed against the option "{self.name}" validating function: {exc}',
                    )
            if self.value_type:
                if not isinstance(dict_value, self.value_type):
                    raise ValueError(
                        f'Value {dict_value} in value failed against the option "{self.name}" type validation: {self.value_type}',
                    )
            if self.value_validating_regex:
                if re.match(self.value_validating_regex, str(dict_value)) is None:
                    raise ValueError(
                        f'Value {dict_value} in value failed to match the option "{self.name}" validating regex: {self.value_validating_regex}',
                    )
            if self.value_validating_function:
                try:
                    self.value_validating_function(dict_value)
                except ValueError as exc:
                    raise ValueError(
                        f'Value {dict_value} in value failed against the option "{self.name}" validating function: {exc}',
                    )

    def to_json(
        self,
    ) -> dict[str, str | bool | dict[str, SimpleType] | None]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "key_type": self.key_type.__name__,
            "key_validating_regex": self.key_validating_regex,
            "key_validating_function": (
                self.key_validating_function.__doc__
                if self.key_validating_function
                else None
            ),
            "value_type": self.value_type.__name__ if self.value_type else None,
            "value_validating_regex": self.value_validating_regex,
            "value_validating_function": (
                self.value_validating_function.__doc__
                if self.value_validating_function
                else None
            ),
        }
