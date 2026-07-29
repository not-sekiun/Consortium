from collections.abc import Mapping


def replace_all(value: str, replacements: Mapping[str, str]) -> str:
    """Replace multiple substrings in a string in mapping iteration order.

    Args:
        value: Original string in which to replace substrings.
        replacements: Substrings and their replacement values.

    Returns:
        The string after all replacements have been applied.
    """
    for old_substring, new_substring in replacements.items():
        value = value.replace(old_substring, new_substring)
    return value
