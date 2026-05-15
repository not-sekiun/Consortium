from typing import Any

from prompt_toolkit.completion import Completer, NestedCompleter


# `prompt_toolkit` creates a `NestedCompleter` object from the `.from_nested_dict()`
# factory class method. `NestedCompleters` have an options attribute that is a nested
# dictionary of completions. However, if the completion is nested, then the parent
# completion will have as its value another instance of a NestedCompleter. This
# function extracts the original dictionary of completions from a NestedCompleter
# object.
def extract_nested_completer_dict_from_nested_completer(
    nested_completer: NestedCompleter,
) -> dict[str, Any]:
    def traverse_nested_completers(
        completer: Completer,
    ) -> dict[str, Any] | Completer:
        # Some other types of Completer might be present like PathCompleter for commands
        # that operate on file paths, do not further attempt to process those
        if not isinstance(completer, NestedCompleter):
            return completer

        completion_dict = {}
        for key, value in completer.options.items():
            if value is None:
                completion_dict[key] = None
            else:
                completion_dict[key] = traverse_nested_completers(completer=value)
        return completion_dict

    result = traverse_nested_completers(completer=nested_completer)
    # This should never happen
    if not isinstance(result, dict):
        raise ValueError(
            "The provided NestedCompleter has an unexpected structure and cannot be "
            "processed.",
        )
    return result
