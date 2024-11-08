from enum import StrEnum


class OptionType(StrEnum):
    """
    An enum representing the different types of options that can be created. Every
    option object will have an `option_type` class attribute that is set to one of the
    variants of this enum.

    Attributes:
        SINGLE_VALUE_OPTION: This type of option can only hold a single value at once.
            The type of this value is restricted to being a `str`, `int`, `float`, or
            `bool`.
        LIST_VALUE_OPTION: This type of option can hold multiple values at once. The
            type of each element in the list is restricted to being a `str`, `int`,
            `float`, or `bool`. The type of the elements may be either heterogeneous
            or homogeneous.
        CHOICE_VALUE_OPTION: This type of option presents a set of choices that the
            user can select from. The type of each choice is restricted to being a
            `str`, `int`, `float`, or `bool`. Only one choice can be selected at a
            time.
        TOGGLEABLE_CHOICES_VALUE_OPTION: This type of option presents a set of choices
            that the user can select from. The type of each choice is restricted to
            being only a `str` which maps to a `bool`. Multiple choices can be selected
            at a time and their values are restricted to toggling the value of the
            `bool`.
        DICTIONARY_VALUE_OPTION: This type of option can hold multiple key-value pairs
            at once. The type of the key is restricted to being only a `str`. The type
            of the value is restricted to being a `str`, `int`, `float`, or `bool`. The
            type of the values may be either heterogeneous or homogeneous.
    """

    SINGLE_VALUE_OPTION = "SINGLE_VALUE_OPTION"
    """
    This type of option can only hold a single value at once. The type of this value is
    restricted to being a `str`, `int`, `float`, or `bool`.
    """
    LIST_VALUE_OPTION = "LIST_VALUE_OPTION"
    """
    This type of option can hold multiple values at once. The type of each element in
    the list is restricted to being a `str`, `int`, `float`, or `bool`. The type of the
    elements may be either heterogeneous or homogeneous.
    """
    CHOICE_VALUE_OPTION = "CHOICE_VALUE_OPTION"
    """
    This type of option presents a set of choices that the user can select from. The
    type of each choice is restricted to being a `str`, `int`, `float`, or `bool`. Only
    one choice can be selected at a time.
    """
    TOGGLEABLE_CHOICES_VALUE_OPTION = "TOGGLEABLE_CHOICES_VALUE_OPTION"
    """
    This type of option presents a set of choices that the user can select from. The
    type of each choice is restricted to being only a `str`. Multiple choices can be
    selected at a time.
    """
    DICTIONARY_VALUE_OPTION = "DICTIONARY_VALUE_OPTION"
    """
    This type of option can hold multiple key-value pairs at once. The type of the key
    is restricted to being only a `str`. The type of the value is restricted to being a
    `str`, `int`, `float`, or `bool. The type of the values may be either heterogeneous
    or homogeneous.
    """
