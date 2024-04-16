from typing import Iterator

from prompt_toolkit import ANSI, HTML, PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_connection import ClientConnection
from consortium.client.framework.base_command import BaseCommand, CommandContext
from consortium.client.framework.base_interpreter import BaseInterpreter
from consortium.client.framework.base_lexer import (
    BaseLexer,
    Token,
    TokenizedString,
    TokenType,
)
from consortium.client.framework.base_parser import ParsedCommand
from consortium.client.utils.printer_utils import print_error, print_info


# TODO: Replace the calls to the environment variable with this
class ClientCommandContext(CommandContext):
    client_connection: ClientConnection | None


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
        super().__init__()

    def _handle_default(self, character: str) -> None:
        if character == "'":
            self._lexer_state = self.PseudoShellStyleLexerState.SINGLE_QUOTE_ESCAPED
        elif character == '"':
            self._lexer_state = self.PseudoShellStyleLexerState.DOUBLE_QUOTE_ESCAPED
        elif character == "\\":
            self._previous_lexer_state = self._lexer_state
            self._lexer_state = self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED
        elif character == " " and self._token_buffer:
            self._lexer_state = self.PseudoShellStyleLexerState.OUTPUT_TOKEN
        # Ignore additional whitespaces.
        elif character == " " and not self._token_buffer:
            pass
        else:
            self._token_buffer += character

    def _handle_single_quote_escaped(self, character: str) -> None:
        if character == "'":
            self._lexer_state = self.PseudoShellStyleLexerState.OUTPUT_TOKEN
        elif character == "\\":
            self._previous_lexer_state = self._lexer_state
            self._lexer_state = self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED
        else:
            self._token_buffer += character

    def _handle_double_quote_escape(self, character: str) -> None:
        if character == '"':
            self._lexer_state = self.PseudoShellStyleLexerState.OUTPUT_TOKEN
        elif character == "'":
            self._token_buffer += character
        elif character == "\\":
            self._previous_lexer_state = self._lexer_state
            self._lexer_state = self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED
        else:
            self._token_buffer += character

    def _handle_backslash_escaped(self, character: str) -> None:
        # Handle special escape sequences.
        if character in ["n", "t", "r", "b", "f", "v", "a", "e"]:
            self._token_buffer += "\\" + character
        else:
            self._token_buffer += character

        self._lexer_state = self._previous_lexer_state

    def _flush_token_buffer(self) -> Token:
        # All tokens are of type WORD because the client interpreter does not simulate
        # pipes, redirections, or other shell features.
        token = Token(
            token_type=self.PseudoShellStyleTokenType.WORD,
            token=self._token_buffer,
        )
        self._token_buffer = ""
        return token

    def _yield_token(self, input_string: str) -> Iterator[Token]:
        for char in input_string:
            if self._lexer_state == self.PseudoShellStyleLexerState.DEFAULT:
                self._handle_default(char)
            elif (
                self._lexer_state
                == self.PseudoShellStyleLexerState.SINGLE_QUOTE_ESCAPED
            ):
                self._handle_single_quote_escaped(char)
            elif (
                self._lexer_state
                == self.PseudoShellStyleLexerState.DOUBLE_QUOTE_ESCAPED
            ):
                self._handle_double_quote_escape(char)
            elif self._lexer_state == self.PseudoShellStyleLexerState.BACKSLASH_ESCAPED:
                self._handle_backslash_escaped(char)

            if self._lexer_state == self.PseudoShellStyleLexerState.OUTPUT_TOKEN:
                self._lexer_state = self.PseudoShellStyleLexerState.DEFAULT
                yield self._flush_token_buffer()

        # Flush the buffer if there is anything left in it.
        if self._token_buffer:
            yield self._flush_token_buffer()

    def tokenize(self, input_string: str) -> TokenizedString:
        tokens = []
        for token in self._yield_token(input_string.strip()):
            tokens.append(token)

        return TokenizedString(
            tokens=tokens,
            original_string=input_string,
        )


class ClientInterpreter(BaseInterpreter):
    def __init__(
        self,
        prompt: ANSI | HTML | str,
        commands: list[BaseCommand],
        client_connection: ClientConnection,
    ):
        super().__init__(
            prompt_session=PromptSession(
                message=prompt,
                completer=NestedCompleter.from_nested_dict(
                    {command.name: None for command in commands},
                ),
                auto_suggest=AutoSuggestFromHistory(),
            ),
            commands=commands,
            ignore_keyboard_interrupt=True,
            environment={
                "client_connection": client_connection,
                "commands": {command.name: command for command in commands},
            },
            lexer=ClientInterpreterLexer(),
        )

    async def on_command_not_found(self, parsed_command: ParsedCommand) -> None:
        print_error(f"Command not found: {parsed_command.command}")

    async def on_interrupt(self) -> None:
        if self.ignore_keyboard_interrupt:
            print_error(
                "Keyboard interrupt ignored. Use 'exit' to exit the interpreter.",
            )
        else:
            print_info("Keyboard interrupt received. Exiting interpreter.")

    # TODO: Provide more comprehensive error handling in the commands.
    # In general, when an error is raised on the REST API side we simply print the error
    # message to the console.
    async def on_interpreter_errored(self, exc: Exception) -> None:
        print_error(f"Error: {exc}")
