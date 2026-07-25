from collections.abc import Hashable
from typing import Any


def recursively_in(dictionary: dict, key: Hashable) -> list[Hashable] | None:
    def helper(
        dictionary: dict, key: Hashable, key_path: list[Hashable]
    ) -> list[Hashable] | None:
        if key in dictionary:
            return key_path + [key]
        for current_key, value in dictionary.items():
            if isinstance(value, dict):
                result = helper(value, key, key_path + [current_key])
                if result is not None:
                    return result
        return None

    return helper(dictionary=dictionary, key=key, key_path=[])


def replace_by_path(dictionary: dict, key_path: list[Hashable], new_value: Any) -> None:
    if not key_path:
        return

    current_dict = dictionary
    for key in key_path[:-1]:
        current_dict = current_dict[key]

    current_dict[key_path[-1]] = new_value


def get_by_path(dictionary: dict, key_path: list[Hashable]) -> Any:
    if not key_path:
        return dictionary

    current_dict = dictionary
    for key in key_path[:-1]:
        current_dict = current_dict[key]

    return current_dict[key_path[-1]]


def add_none_to_leaf(dictionary: dict):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            add_none_to_leaf(value)
        else:
            dictionary[key] = {key: None}
