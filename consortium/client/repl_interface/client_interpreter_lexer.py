from typing import Iterator

from consortium.client.exceptions.client_interpreter_exceptions import (
    UnclosedDoubleQuotesError,
    UnclosedSingleQuotesError,
)
from consortium.client.repl_framework.base_lexer import (
    BaseLexer,
    Token,
    TokenizedString,
    TokenType,
)


class ClientInterpreterLexer(BaseLexer):
    class PseudoShellStyleTokenType(TokenType):
        # The client interpreter handles the input as if it were a shell-style command.
        # but crucially ignores pipes, redirections, and other shell features, instead
        # treating the input as a simple space-separated command with shell-style
        # escape features.
        WORD = "WORD"

    class PseudoShellStyleLexerState:
        DEFAULT = "DEFAULT"
        BACKSLASH_ESCAPED = "BACKSLASH_ESCAPED"
        SINGLE_QUOTE_ESCAPED = "SINGLE_QUOTE_ESCAPED"
        DOUBLE_QUOTE_ESCAPED = "DOUBLE_QUOTE_ESCAPED"
        OUTPUT_TOKEN = "OUTPUT_TOKEN"

    def __init__(self):
        # Previous lexer state is only here to help us differentiate between
        # a backslash escape inside a quoted string and a backslash escape
        # outside a quoted string.
        self._previous_lexer_state = None
        self._lexer_state = self.PseudoShellStyleLexerState.DEFAULT
        self._token_buffer = ""
        self._token_start_index = None
        super().__init__()

    def _handle_default(self, char_index: int, char: str) -> None:
        if char == "'":
            self._lexer_state = self.PseudoShellStyleLexerState.SINGLE_QUOTE_ESCAPED
        elif char == '"':
            self._lexer_state = self.PseudoShellStyleLexerState.DOUBLE_QUOTE_ESCAPED
        elif char == "\\":
            self._previous_lexer_state = self._lexer_state
            self._lexer_state = self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED
        elif char == " " and self._token_buffer:
            self._lexer_state = self.PseudoShellStyleLexerState.OUTPUT_TOKEN
        # Ignore additional whitespaces.
        elif char == " " and not self._token_buffer:
            pass
        else:
            self._add_char_to_token_buffer(char_index=char_index, char=char)

    def _handle_single_quote_escaped(self, char_index: int, char: str) -> None:
        if char == "'":
            self._lexer_state = self.PseudoShellStyleLexerState.DEFAULT
        elif char == "\\":
            self._previous_lexer_state = self._lexer_state
            self._lexer_state = self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED
        else:
            self._add_char_to_token_buffer(char_index=char_index, char=char)

    def _handle_double_quote_escape(self, char_index: int, char: str) -> None:
        if char == '"':
            self._lexer_state = self.PseudoShellStyleLexerState.DEFAULT
        elif char == "\\":
            self._previous_lexer_state = self._lexer_state
            self._lexer_state = self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED
        else:
            self._add_char_to_token_buffer(char_index=char_index, char=char)

    def _handle_backslash_escaped(self, char_index: int, char: str) -> None:
        self._add_char_to_token_buffer(char_index=char_index, char=char)

        self._lexer_state = self._previous_lexer_state

    def _add_char_to_token_buffer(self, char_index: int, char: str) -> None:
        if self._token_start_index is None:
            if self._lexer_state == self.PseudoShellStyleLexerState.DEFAULT:
                self._token_start_index = char_index
            elif self._lexer_state in (
                self.PseudoShellStyleLexerState.SINGLE_QUOTE_ESCAPED,
                self.PseudoShellStyleLexerState.DOUBLE_QUOTE_ESCAPED,
                self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED,
            ):
                self._token_start_index = char_index - 1
        self._token_buffer += char

    def _flush_token_buffer(self, current_char_index: int) -> Token:
        # All tokens are of type WORD because the client interpreter does not simulate
        # pipes, redirections, or other shell features.
        token = Token(
            token_type=self.PseudoShellStyleTokenType.WORD,
            token=self._token_buffer,
            start_index=self._token_start_index,
            end_index=current_char_index - 1,  # -1 to exclude the space
        )
        self._token_buffer = ""
        self._token_start_index = None
        return token

    def _yield_token(self, input_string: str) -> Iterator[Token]:
        for char_index, char in enumerate(input_string):
            if self._lexer_state == self.PseudoShellStyleLexerState.DEFAULT:
                self._handle_default(char_index=char_index, char=char)
            elif (
                self._lexer_state
                == self.PseudoShellStyleLexerState.SINGLE_QUOTE_ESCAPED
            ):
                self._handle_single_quote_escaped(char_index=char_index, char=char)
            elif (
                self._lexer_state
                == self.PseudoShellStyleLexerState.DOUBLE_QUOTE_ESCAPED
            ):
                self._handle_double_quote_escape(char_index=char_index, char=char)
            elif self._lexer_state == self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED:
                self._handle_backslash_escaped(char_index=char_index, char=char)
            if self._lexer_state == self.PseudoShellStyleLexerState.OUTPUT_TOKEN:
                self._lexer_state = self.PseudoShellStyleLexerState.DEFAULT
                yield self._flush_token_buffer(current_char_index=char_index)

        if self._lexer_state == self.PseudoShellStyleLexerState.DOUBLE_QUOTE_ESCAPED:
            raise UnclosedDoubleQuotesError
        elif self._lexer_state == self.PseudoShellStyleLexerState.SINGLE_QUOTE_ESCAPED:
            raise UnclosedSingleQuotesError

        # Flush the buffer if there is anything left in it.
        if self._token_buffer:
            # We add 1 to the current_char_index to account for the fact that at the
            # very end no space is present to denote the end of the token. While the
            # _flush_token_buffer assumes it is present. This is equivalent to adding a
            # space at the end of the input string to signify a form of EOF.
            yield self._flush_token_buffer(
                current_char_index=(len(input_string) - 1) + 1,
            )

    def tokenize(self, input_string: str) -> TokenizedString:
        # TODO: Prevent states from interfering.
        # Reset lexer state to its default state since incomplete quotes (while raising
        # the appropriate errors) can cause the state to not be initialized to its
        # default state when _yield_token() is called again.
        self._lexer_state = self.PseudoShellStyleLexerState.DEFAULT
        self._previous_lexer_state = None
        self._token_buffer = ""
        self._token_start_index = None

        tokens = []
        for token in self._yield_token(input_string.strip()):
            tokens.append(token)

        return TokenizedString(
            tokens=tokens,
            original_string=input_string,
        )
