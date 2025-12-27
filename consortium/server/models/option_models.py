from typing import Annotated, Literal

from pydantic import BaseModel, Field

from consortium.framework.options.option_types import OptionType

# Type alias for primitive values in options
type Primitive = str | int | float | bool


class SingleValueOptionModel(BaseModel):
    name: str
    description: str
    required: bool
    default_value: Primitive | None
    value_type: Literal["str", "int", "float", "bool"] | None
    minimum_length: int | None
    maximum_length: int | None
    greater_than: int | float | None
    less_than: int | float | None
    greater_than_or_equal_to: int | float | None
    less_than_or_equal_to: int | float | None
    validating_regex: str | None
    validating_function: str | None
    option_type: Literal[OptionType.SINGLE_VALUE_OPTION]


class ListValueOptionModel(BaseModel):
    name: str
    description: str
    required: bool
    default_value: list[Primitive] | None
    allow_duplicates: bool
    value_type: Literal["str", "int", "float", "bool"] | None
    minimum_length: int | None
    maximum_length: int | None
    greater_than: int | float | None
    less_than: int | float | None
    greater_than_or_equal_to: int | float | None
    less_than_or_equal_to: int | float | None
    minimum_elements: int | None
    maximum_elements: int | None
    validating_regex: str | None
    validating_function: str | None
    option_type: Literal[OptionType.LIST_VALUE_OPTION]


class ChoiceValueOptionModel(BaseModel):
    name: str
    description: str
    required: bool
    default_value: Primitive | None
    available_values: list[Primitive]
    option_type: Literal[OptionType.CHOICE_VALUE_OPTION]


class ToggleableChoicesValueOptionModel(BaseModel):
    name: str
    description: str
    required: bool
    default_value: dict[str, bool] | None
    available_values: list[str]
    option_type: Literal[OptionType.TOGGLEABLE_CHOICES_VALUE_OPTION]


class DictionaryValueOptionModel(BaseModel):
    name: str
    description: str
    required: bool
    default_value: dict[str, Primitive] | None
    key_validating_regex: str | None
    key_validating_function: str | None
    value_type: Literal["str", "int", "float", "bool"] | None
    value_validating_regex: str | None
    value_validating_function: str | None
    validating_function: str | None
    option_type: Literal[OptionType.DICTIONARY_VALUE_OPTION]


# Discriminated union of all option models using the option_type field
OptionModel = Annotated[
    SingleValueOptionModel
    | ListValueOptionModel
    | ChoiceValueOptionModel
    | ToggleableChoicesValueOptionModel
    | DictionaryValueOptionModel,
    Field(discriminator="option_type"),
]
