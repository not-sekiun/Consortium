def multiple_string_replace(input_string: str, replacements: dict[str, str]) -> str:
    """
    Replaces multiple substrings in the `input string` based on the provided
    `replacements` dictionary.

    Args:
        input_string (str): The original string where replacements will be made.
        replacements (dict): A dictionary where keys are substrings to be replaced and values are
            the substrings to replace them with.

    Returns:
        str: The modified string with all specified replacements made.
    """
    for old_substring, new_substring in replacements.items():
        input_string = input_string.replace(old_substring, new_substring)
    return input_string
