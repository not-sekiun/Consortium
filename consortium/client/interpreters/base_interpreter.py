import json
import queue
import traceback

import prompt_toolkit
from prompt_toolkit.completion import NestedCompleter

from consortium.client.client_config import CONSORTIUM_COMMAND_ALIASES_JSON_FILE_PATH
from consortium.client.client_exceptions import (
    IncompleteDoubleQuoteError,
    IncompleteEscapeError,
    IncompleteSingleQuoteError,
    InvalidCommandError,
    InvalidCommandReturnStatusError,
)
from consortium.client.client_session import ClientSession
from consortium.client.commands.base_command import BaseCommand
from consortium.client.objects.command_objects import (
    CommandReturnStatus,
    ContinueReturnStatus,
    ExitProgramReturnStatus,
    InterpreterCommand,
    SwitchInterpreterReturnStatus,
)
from consortium.client.objects.interpreter_objects import (
    CharacterBuffer,
    LexerState,
    TokenizedString,
)
from consortium.client.utils.standard_io_utils import print_error, print_red


class BaseInterpreter:
    _prompt_session = prompt_toolkit.PromptSession()

    # Resource commands are used to store the commands that are loaded from resource
    # files. These commands are executed in the interpreter in a FIFO manner. Resource
    # commands are shared across all interpreters.
    resource_interpreter_commands = queue.Queue()

    def __init__(
        self,
        prompt: str,
        commands: list[BaseCommand],
        client_session: ClientSession | None = None,
    ) -> None:
        self.prompt = prompt
        self.commands = {command.name: command for command in commands}
        self.client_session = client_session

        with open(CONSORTIUM_COMMAND_ALIASES_JSON_FILE_PATH, "r") as file:
            self.command_aliases = json.load(fp=file)

        self._completer = NestedCompleter.from_nested_dict(
            {command.name: None for command in self.commands.values()},
        )

    async def read_input(self, prompt: str) -> str:
        # read_input() prompts without the autocompleter of the interpreter while the
        # read_input_from_interpreter() method prompts with the autocompleter.
        return await self._prompt_session.prompt_async(prompt_toolkit.ANSI(prompt))

    async def read_input_from_interpreter(self, prompt: str | None = None) -> str:
        if prompt is None:
            return await self._prompt_session.prompt_async(
                prompt_toolkit.ANSI(self.prompt),
                completer=self._completer,
            )
        return await self._prompt_session.prompt_async(
            prompt_toolkit.ANSI(prompt),
            completer=self._completer,
        )

    @staticmethod
    def tokenize_string(input_string: str) -> TokenizedString:
        # lexer_state_before_escaped_state is used to store the parser state before
        # entering the ESCAPED state. This is used to determine the parser state to
        # return to after the ESCAPED state is exited which could be either the NORMAL,
        # IN_DOUBLE_QUOTES, or IN_SINGLE_QUOTES state.
        lexer_state_before_escaped_state = None
        lexer_state = LexerState.NORMAL
        character_buffer = CharacterBuffer()
        tokens = []

        for character in input_string:
            if lexer_state == LexerState.NORMAL:
                if character == " ":
                    lexer_state = LexerState.DELIMITED
                    # If we encounter the delimiting character, in the NORMAL state and
                    # the buffer is not empty, we store the word and flush the buffer.
                    # The buffer being empty at this point signifies that we are at the
                    # beginning of the string, and that the whitespace delimiter is
                    # leading which we ignore.
                    if not character_buffer.is_buffer_empty():
                        tokens.append(character_buffer.flush_buffer())
                elif character == '"':
                    lexer_state = LexerState.IN_DOUBLE_QUOTES
                    # This is to set up for if we encounter another quote character
                    # immediately after the first one. This signifies an empty quoted
                    # string.
                    character_buffer.add_character_to_buffer("")
                elif character == "'":
                    lexer_state = LexerState.IN_SINGLE_QUOTES
                    character_buffer.add_character_to_buffer("")
                elif character == "\\":
                    lexer_state_before_escaped_state = lexer_state
                    lexer_state = LexerState.ESCAPED
                else:
                    character_buffer.add_character_to_buffer(character)
            elif lexer_state == LexerState.IN_DOUBLE_QUOTES:
                if character == '"':
                    lexer_state = LexerState.NORMAL
                elif character == "\\":
                    lexer_state_before_escaped_state = lexer_state
                    lexer_state = LexerState.ESCAPED
                else:
                    character_buffer.add_character_to_buffer(character)
            elif lexer_state == LexerState.IN_SINGLE_QUOTES:
                if character == "'":
                    lexer_state = LexerState.NORMAL
                elif character == "\\":
                    lexer_state_before_escaped_state = lexer_state
                    lexer_state = LexerState.ESCAPED
                else:
                    character_buffer.add_character_to_buffer(character)
            elif lexer_state == LexerState.ESCAPED:
                if character in (
                    "n",
                    "t",
                    "r",
                    "b",
                    "f",
                ) and lexer_state_before_escaped_state in (
                    LexerState.IN_DOUBLE_QUOTES,
                    LexerState.IN_SINGLE_QUOTES,
                ):
                    character_map = {
                        "n": "\n",
                        "t": "\t",
                        "r": "\r",
                        "b": "\b",
                        "f": "\f",
                    }
                    character_buffer.add_character_to_buffer(character_map[character])
                else:
                    if lexer_state_before_escaped_state in (
                        LexerState.IN_DOUBLE_QUOTES,
                        LexerState.IN_SINGLE_QUOTES,
                    ):
                        character_buffer.add_character_to_buffer("\\")
                    character_buffer.add_character_to_buffer(character)
                lexer_state = lexer_state_before_escaped_state
            elif lexer_state == LexerState.DELIMITED:
                if character == " ":
                    pass
                elif character == '"':
                    lexer_state = LexerState.IN_DOUBLE_QUOTES
                    character_buffer.add_character_to_buffer("")
                elif character == "'":
                    lexer_state = LexerState.IN_SINGLE_QUOTES
                    character_buffer.add_character_to_buffer("")
                else:
                    character_buffer.add_character_to_buffer(character)
                    lexer_state = LexerState.NORMAL

        if lexer_state == LexerState.IN_DOUBLE_QUOTES:
            raise IncompleteDoubleQuoteError()
        elif lexer_state == LexerState.IN_SINGLE_QUOTES:
            raise IncompleteSingleQuoteError()
        elif lexer_state == LexerState.ESCAPED:
            raise IncompleteEscapeError()

        # If we have a buffer, and we are not in the NORMAL state, we need to store the
        # word. The only other option is being in the DELIMITED state at the very end.
        # This means that there are trailing whitespace delimiters that we ignore.
        if lexer_state == LexerState.NORMAL:
            tokens.append(character_buffer.flush_buffer())

        return TokenizedString(
            tokens=tokens,
            original_string=input_string,
        )

    def resolve_token_aliases(
        self,
        tokenized_string: TokenizedString,
    ) -> TokenizedString:
        alias_token = tokenized_string.tokens[0]
        # Perform recursive tokenization, taking into account command aliasing and
        # aliases that refer to other aliases as their command.
        while True:
            if alias_token in self.command_aliases:
                # Note that by nature of the lexer, an alias' command cannot be
                # incomplete. That is to say that it cannot have hanging backslashes or
                # unclosed quotes.
                expanded_alias_tokenized_string = self.tokenize_string(
                    self.command_aliases[alias_token],
                )
                tokenized_string.tokens = (
                    expanded_alias_tokenized_string.tokens + tokenized_string.tokens[1:]
                )
                alias_token = tokenized_string.tokens[0]
            else:
                break

        return tokenized_string

    @staticmethod
    def parse_tokenized_string_to_interpreter_command(
        tokenized_string: TokenizedString,
    ) -> InterpreterCommand:
        if not tokenized_string.tokens:
            return InterpreterCommand(
                command="",
                arguments=[],
                original_string=tokenized_string.original_string,
            )
        else:
            return InterpreterCommand(
                command=tokenized_string.tokens[0],
                arguments=tokenized_string.tokens[1:],
                original_string=tokenized_string.original_string,
            )

    async def execute_command(
        self,
        interpreter_command: InterpreterCommand,
    ) -> CommandReturnStatus:
        if not interpreter_command.command:
            return ContinueReturnStatus()
        elif interpreter_command.command in self.commands:
            command_return_status = await self.commands[
                interpreter_command.command
            ].run_command(
                interpreter_command=interpreter_command,
                client_session=self.client_session,
                interpreter=self,
            )

            if isinstance(command_return_status, ContinueReturnStatus):
                pass
            elif isinstance(
                command_return_status,
                ExitProgramReturnStatus,
            ) or isinstance(
                command_return_status,
                SwitchInterpreterReturnStatus,
            ):
                return command_return_status
            else:
                raise InvalidCommandReturnStatusError(
                    f"Invalid command return status: {command_return_status}",
                )
        else:
            raise InvalidCommandError(
                f"Command '{interpreter_command.command}' not found.",
            )

    async def run_interpreter(self) -> CommandReturnStatus:
        while True:
            # Check if there are any resource commands to execute. If there are no
            # resource commands, we will prompt the user for input.
            if self.resource_interpreter_commands.empty():
                # Read input from the user with the prompt that is specific to the
                # interpreter.
                input_string = await self.read_input_from_interpreter()

                # Attempt to tokenize the string, if the tokenization is invalid due to
                # some form of incomplete input, we will prompt the user for more input
                # and then attempt to parse the string again.
                while True:
                    try:
                        tokenized_string = self.tokenize_string(
                            input_string=input_string,
                        )
                        break
                    # Incomplete quote strings are concatenated with a newline
                    # character.
                    except (IncompleteDoubleQuoteError, IncompleteSingleQuoteError):
                        input_string += "\n" + await self.read_input("... ")
                        continue
                    # Incomplete escape characters are concatenated without a newline.
                    except IncompleteEscapeError:
                        input_string += await self.read_input("... ")
                        continue

                # Resolve any command aliases in the tokens. Only the first token is
                # resolved.
                tokenized_string = self.resolve_token_aliases(
                    tokenized_string=tokenized_string,
                )

                # Convert tokens to an interpreter command object.
                interpreter_command = (
                    self.parse_tokenized_string_to_interpreter_command(
                        tokenized_string=tokenized_string,
                    )
                )
            else:
                interpreter_command = self.resource_interpreter_commands.get()

            # Execute the command, accounting for any exceptions that arise, and
            # returning the command return status if required.
            try:
                command_return_status = await self.execute_command(
                    interpreter_command=interpreter_command,
                )
                if isinstance(
                    command_return_status,
                    ExitProgramReturnStatus,
                ) or isinstance(
                    command_return_status,
                    SwitchInterpreterReturnStatus,
                ):
                    return command_return_status
            # InvalidCommandReturnStatusError can also be raised, but should not be
            # caught here as it is a programming error for the developer to address.
            except InvalidCommandError:
                print_error(f'Command "{interpreter_command.command}" not found.')
                continue
            except KeyboardInterrupt:
                print_error('CTRL+C captured, use "exit" to exit the interpreter.')
                continue
            except Exception as exc:
                print_error(f"A fatal error occurred: {exc}")
                print_red(traceback.format_exc(), bold=True)
                continue
