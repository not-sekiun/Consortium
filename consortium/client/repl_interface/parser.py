from pydantic import BaseModel

from consortium.client.repl_interface.lexer import TokenizedString


class ParsedCommand(BaseModel):
    command: str
    arguments: list[str]
    raw_input: str


def parse(tokenized_string: TokenizedString) -> ParsedCommand:
    if tokenized_string.raw_input.strip() != "" and tokenized_string.tokens:
        return ParsedCommand(
            command=tokenized_string.tokens[0],
            arguments=tokenized_string.tokens[1:],
            raw_input=tokenized_string.raw_input,
        )
    else:
        return ParsedCommand(command="", arguments=[], raw_input="")
