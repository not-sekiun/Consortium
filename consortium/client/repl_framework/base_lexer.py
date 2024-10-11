from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class TokenType(StrEnum): ...


@dataclass
class Token:
    token_type: TokenType
    token: str
    start_index: int
    end_index: int


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

        word = ""
        for char_index, char in enumerate(input_string.strip()):
            if char == " ":
                if word:
                    tokens.append(
                        Token(
                            token_type=self.SimpleLexerTokenType.WORD,
                            token=word,
                            start_index=char_index - len(word),
                            end_index=char_index - 1,  # -1 to exclude the space
                        ),
                    )
                    word = ""
            else:
                word += char

        if word:
            tokens.append(
                Token(
                    token_type=self.SimpleLexerTokenType.WORD,
                    token=word,
                    start_index=len(input_string) - len(word),
                    end_index=len(input_string) - 1,
                ),
            )

        return TokenizedString(tokens=tokens, original_string=input_string)
