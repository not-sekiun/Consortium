from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class TokenType(StrEnum): ...


@dataclass
class Token:
    token_type: TokenType
    token: str


@dataclass
class TokenizedString:
    tokens: list[Token]
    original_string: str


class BaseLexer(ABC):
    def __init__(self, environment: dict = None):
        if environment is None:
            environment = {}

        self.environment = environment

    @abstractmethod
    def tokenize(self, input_string: str) -> TokenizedString: ...


class SimpleLexer(BaseLexer):
    class SimpleLexerTokenType(TokenType):
        WORD = "WORD"

    def tokenize(self, input_string: str) -> TokenizedString:
        tokens = []

        for word in input_string.split():
            tokens.append(Token(self.SimpleLexerTokenType.WORD, word))

        return TokenizedString(tokens=tokens, original_string=input_string)
