from consortium.client.models.alias_model import Alias
from consortium.client.repl_interface.lexer import tokenize


def expand_aliases(
    tokens: list[str],
    aliases: dict[str, Alias],
    expanded_aliases: set[str] | None = None,
) -> list[str]:
    if expanded_aliases is None:
        expanded_aliases = set()

    expanded_tokens = []
    for index, token in enumerate(tokens):
        if token in aliases and token not in expanded_aliases:
            alias = aliases[token]
            if alias.is_global or index == 0:
                new_expanded_aliases = expanded_aliases.copy()
                new_expanded_aliases.add(token)
                new_tokens = tokenize(alias.command).tokens
                expanded_tokens.extend(
                    expand_aliases(new_tokens, aliases, new_expanded_aliases)
                )
                continue
        expanded_tokens.append(token)
    return expanded_tokens
