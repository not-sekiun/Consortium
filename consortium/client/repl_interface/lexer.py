from pydantic import BaseModel

from consortium.client.exceptions.client_interpreter_exceptions import (
    UnclosedQuotesError,
)


class TokenizedString(BaseModel):
    tokens: list[str]
    raw_input: str


def tokenize(input_string: str) -> TokenizedString:
    tokens = []

    escape = False
    in_single_quotes = False
    in_double_quotes = False
    token_start_index = None
    token_buffer = ""

    for char_index, char in enumerate(input_string):
        if escape:
            token_buffer += char
            escape = False
        elif char == "\\":
            escape = True
        elif char == "'" and not in_double_quotes:
            in_single_quotes = not in_single_quotes
            if token_start_index is None:
                token_start_index = char_index
        elif char == '"' and not in_single_quotes:
            in_double_quotes = not in_double_quotes
            if token_start_index is None:
                token_start_index = char_index
        elif char == " " and not in_single_quotes and not in_double_quotes:
            if token_buffer:
                tokens.append(token_buffer)
                token_buffer = ""
                token_start_index = None
        else:
            if token_start_index is None:
                token_start_index = char_index
            token_buffer += char

    if in_single_quotes or in_double_quotes:
        raise UnclosedQuotesError

    if token_buffer:
        tokens.append(token_buffer)

    return TokenizedString(
        tokens=tokens,
        raw_input=input_string,
    )
