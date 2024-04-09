from dataclasses import dataclass
from enum import StrEnum


@dataclass
class TokenizedString:
    tokens: list[str]
    original_string: str


class InterpreterType(StrEnum):
    HOME = "HOME"
    LISTENERS = "LISTENERS"
    AGENTS = "AGENTS"
    GENERATORS = "GENERATORS"
    CREATE_LISTENER = "CREATE_LISTENER"


class LexerState(StrEnum):
    NORMAL = "NORMAL"
    IN_DOUBLE_QUOTES = "IN_DOUBLE_QUOTES"
    IN_SINGLE_QUOTES = "IN_SINGLE_QUOTES"
    ESCAPED = "ESCAPED"
    DELIMITED = "DELIMITED"


class CharacterBuffer:
    def __init__(self):
        self._buffer = None

    def add_character_to_buffer(self, character: str) -> None:
        if self._buffer is None:
            self._buffer = character
        else:
            self._buffer += character

    def is_buffer_empty(self) -> bool:
        return self._buffer is None

    def flush_buffer(self) -> str:
        buffer_contents = self._buffer
        self._buffer = None
        return buffer_contents
