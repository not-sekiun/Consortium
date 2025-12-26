from typing import Any

from prompt_toolkit.completion import NestedCompleter


# `prompt_toolkit` creates a `NestedCompleter` object from the `.from_nested_dict()`
# factory class method. `NestedCompleters` have an options attribute that is a nested
# dictionary of completions. However, if the completion is nested, then the parent
# completion will have as its value another instance of a NestedCompleter. This
# function extracts the original dictionary of completions from a NestedCompleter
# object.
def extract_nested_completer_dict_from_nested_completer(
    nested_completer: NestedCompleter,
) -> dict[str, Any]:
    completion_dict = {}
    for key, value in nested_completer.options.items():
        if value is None:
            completion_dict[key] = None
        else:
            completion_dict[key] = extract_nested_completer_dict_from_nested_completer(
                value,
            )
    return completion_dict
