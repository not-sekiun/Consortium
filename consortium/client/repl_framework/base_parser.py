from abc import ABC, abstractmethod
from dataclasses import dataclass

from consortium.client.repl_framework.base_lexer import TokenizedString


@dataclass
class ParsedCommand:
    command: str
    arguments: list[str]
    original_string: str


class BaseParser(ABC):
    def __init__(self, environment: dict = None):
        if environment is None:
            environment = {}

        self.environment = environment

    @abstractmethod
    def parse(self, tokenized_string: TokenizedString) -> ParsedCommand: ...


class SimpleParser(BaseParser):
    def parse(self, tokenized_string: TokenizedString) -> ParsedCommand:
        if tokenized_string.original_string.strip() != "":
            if tokenized_string.tokens:
                return ParsedCommand(
                    command=tokenized_string.tokens[0].token,
                    arguments=[token.token for token in tokenized_string.tokens[1:]],
                    original_string=tokenized_string.original_string,
                )
            else:
                return ParsedCommand(command="", arguments=[], original_string="")
        else:
            return ParsedCommand(command="", arguments=[], original_string="")
