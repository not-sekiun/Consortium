from prompt_toolkit import PromptSession

from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_framework.base_lexer import BaseLexer, SimpleLexer
from consortium.client.repl_framework.base_parser import (
    BaseParser,
    ParsedCommand,
    SimpleParser,
)


class BaseInterpreter:
    def __init__(
        self,
        prompt_session: PromptSession | None = None,
        commands: list[BaseCommand] = None,
        environment: dict = None,
        ignore_keyboard_interrupt: bool = False,
        lexer: BaseLexer | None = None,
        parser: BaseParser | None = None,
    ):
        if prompt_session is None:
            prompt_session = PromptSession()
        if lexer is None:
            lexer = SimpleLexer()
        if parser is None:
            parser = SimpleParser()
        if commands is None:
            commands = []
        if environment is None:
            environment = {}

        self.prompt_session = prompt_session
        self.commands = {command.name: command for command in commands}
        self.environment = environment
        self.ignore_keyboard_interrupt = ignore_keyboard_interrupt
        self.lexer = lexer
        self.parser = parser

    async def read_input(
        self,
    ) -> str:
        return await self.prompt_session.prompt_async()

    async def on_command(self, parsed_command: ParsedCommand) -> ReturnStatus:
        command_context = CommandContext(
            command=parsed_command.command,
            arguments=parsed_command.arguments,
            original_string=parsed_command.original_string,
            environment=self.environment,
        )
        return await self.commands[parsed_command.command].run_command(command_context)

    async def on_command_not_found(self, parsed_command: ParsedCommand) -> None:
        pass

    async def on_interrupt(self) -> None:
        pass

    async def on_enter(self) -> None:
        pass

    async def on_exit(self) -> None:
        pass

    async def on_loop(self) -> None:
        pass

    async def on_error(self, exc: Exception) -> None:
        raise exc

    async def run(self) -> ReturnStatus:
        await self.on_enter()

        while True:
            try:
                await self.on_loop()

                input_string = await self.read_input()
                if not input_string:
                    continue

                tokens = self.lexer.tokenize(input_string)
                parsed_command = self.parser.parse(tokens)

                if parsed_command.command in self.commands:
                    command_return_status = await self.on_command(parsed_command)
                    if command_return_status.type == ReturnStatusType.CONTINUE:
                        continue
                    else:
                        return command_return_status
                else:
                    await self.on_command_not_found(parsed_command)
            except KeyboardInterrupt:
                await self.on_interrupt()
                if not self.ignore_keyboard_interrupt:
                    await self.on_exit()
                    return ReturnStatus(type=ReturnStatusType.EXIT)
            except Exception as exc:
                await self.on_error(exc)
