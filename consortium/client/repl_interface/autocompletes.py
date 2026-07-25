from collections.abc import Iterable, Mapping, Sequence
from enum import Enum, auto

from prompt_toolkit.completion import Completer


# Sentinels standing in for values that are only known at runtime. Commands declare
# them like any other completion token and the interpreter that owns the data expands
# them just before handing the completions dictionary to the completer.
class Autocomplete(Enum):
    COMMANDS = auto()
    CLIENT_SESSION_ID = auto()
    LISTENER_ID = auto()
    # Every listener ID carrying the parameter names of that specific listener
    LISTENER_ID_WITH_PARAMETERS = auto()
    LISTENER_TEMPLATE_ID = auto()
    AGENT_ID = auto()
    AGENT_TASK_ID = auto()
    AGENT_GENERATOR_ID = auto()
    # Every agent generator ID carrying the parameter names of that specific generator
    AGENT_GENERATOR_ID_WITH_PARAMETERS = auto()
    AGENT_TEMPLATE_ID = auto()
    ASSET_ID = auto()
    ARTIFACT_ID = auto()
    PAYLOAD_ID = auto()
    # The options of whichever template the current interpreter is scoped to
    TEMPLATE_OPTION = auto()


# The normalized form: a completion tree whose branches terminate in `None` (or in a
# `Completer` that takes over from that point onwards)
type AutocompleteDict = dict[str | Autocomplete, AutocompleteDict | Completer | None]

# The declarative form a command may use for its `autocompletes` class attribute. A
# bare value completes a single token, a list completes a linear chain of tokens (each
# element being the only completion offered after the previous one) and a dictionary
# describes a full tree with any of the above nested inside it.
type AutocompleteSpec = (
    str
    | Autocomplete
    | list[str | Autocomplete | AutocompleteSpec]
    | dict[str | Autocomplete, AutocompleteSpec]
    | Completer
    | None
)

# Runtime values a sentinel expands into. Either a plain iterable of values, in which
# case every value shares the subtree declared underneath the sentinel, or a mapping of
# value to a per value subtree which is merged in on top of that shared subtree.
type AutocompleteResolutions = Mapping[
    Autocomplete, Iterable[str] | Mapping[str, AutocompleteSpec]
]


# Expand the shorthand a command declares into the nested dictionary form the completer
# expects. Idempotent, so re-normalizing an already normalized tree is a no-op (which
# matters because subclasses inherit an already normalized attribute).
def normalize_autocompletes(autocompletes: AutocompleteSpec) -> AutocompleteDict | None:
    match autocompletes:
        case None | Completer():
            return autocompletes
        case str() | Autocomplete():
            return {autocompletes: None}
        case dict():
            return {
                key: normalize_autocompletes(subtree)
                for key, subtree in autocompletes.items()
            }
        case list() | tuple():
            return _normalize_chain(chain=autocompletes)
        case _:
            raise TypeError(
                f"Unsupported autocomplete declaration '{autocompletes!r}' of type "
                f"'{type(autocompletes).__name__}'",
            )


def _normalize_chain(chain: Sequence[AutocompleteSpec]) -> AutocompleteDict | None:
    normalized = None
    # Built from the tail backwards so that each token in the chain points at the
    # remainder of the chain
    for element in reversed(chain):
        if isinstance(element, str | Autocomplete):
            normalized = {element: normalized}
        elif normalized is None:
            # Anything that isn't a plain token can only be the tail of the chain,
            # there is nothing meaningful to nest underneath it
            normalized = normalize_autocompletes(element)
        else:
            raise TypeError(
                f"Nested autocomplete declaration '{element!r}' is only allowed as the "
                "last element of an autocomplete chain",
            )
    return normalized


# Recursively walk a normalized tree and replace every sentinel key with the runtime
# values it resolves to. Each value points at the same resolved subtree that was
# declared underneath the sentinel, so `[Autocomplete.LISTENER_ID, "--force"]` offers
# `--force` after any listener ID. Sentinels with no resolution expand to nothing,
# which is what allows a completions dictionary to be built before the interpreter has
# fetched anything.
def resolve_autocompletes(
    autocompletes: AutocompleteDict | Completer | None,
    resolutions: AutocompleteResolutions,
) -> AutocompleteDict | Completer | None:
    if not isinstance(autocompletes, dict):
        return autocompletes

    resolved: AutocompleteDict = {}
    for key, subtree in autocompletes.items():
        # Resolved once per sentinel rather than once per value so that every value the
        # sentinel expands into shares the exact same subtree object
        resolved_subtree = resolve_autocompletes(
            autocompletes=subtree,
            resolutions=resolutions,
        )

        if not isinstance(key, Autocomplete):
            resolved[key] = resolved_subtree
            continue

        for value, dependent_subtree in _as_value_map(
            values=resolutions.get(key),
        ).items():
            resolved[value] = _merge_subtrees(
                dependent_subtree=resolve_autocompletes(
                    autocompletes=normalize_autocompletes(dependent_subtree),
                    resolutions=resolutions,
                ),
                declared_subtree=resolved_subtree,
            )

    return resolved


def _as_value_map(
    values: Iterable[str] | Mapping[str, AutocompleteSpec] | None,
) -> Mapping[str, AutocompleteSpec]:
    if values is None:
        return {}
    if isinstance(values, Mapping):
        return values
    return dict.fromkeys(values)


# Completions that a single runtime value brings with it (eg the parameter names of one
# specific listener) are merged underneath that value alongside whatever the command
# declared underneath the sentinel itself
def _merge_subtrees(
    dependent_subtree: AutocompleteDict | Completer | None,
    declared_subtree: AutocompleteDict | Completer | None,
) -> AutocompleteDict | Completer | None:
    if dependent_subtree is None:
        return declared_subtree
    if declared_subtree is None:
        return dependent_subtree
    if not isinstance(dependent_subtree, dict) or not isinstance(
        declared_subtree, dict
    ):
        raise TypeError(
            "Cannot merge a resolved autocomplete subtree with a declared one when "
            "either of them terminates in a completer",
        )
    return dependent_subtree | declared_subtree
