import textwrap
from typing import Any, Dict


def get_dictionary_keys_from_value(dictionary: Dict, target: Any) -> list:
    keys = []
    for key, val in dictionary.items():
        if val == target:
            keys.append(key)
    return keys


# Provides a wrapper around textwrap.dedent to allow for formatting of argparse epilog
# strings in source code without effecting the formatting of the string when it is
# displayed in the help menu. Additionally, a single whitespace character is appended at
# the end to ensure that the epilog is displayed with a newline character at the end,
# else argparse simply ignores that last newline character.
def argparse_epilog_formatter(epilog_string: str) -> str:
    return textwrap.dedent(epilog_string) + " "
