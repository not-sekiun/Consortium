from consortium.client.client_connection import ClientConnection
from consortium.client.framework.base_command import ReturnStatus
from consortium.client.interpreters.agents_interpreter import AgentsInterpreter
from consortium.client.interpreters.generators_interpreter import GeneratorsInterpreter
from consortium.client.interpreters.home_interpreter import HomeInterpreter
from consortium.client.interpreters.listeners_interpreter import ListenersInterpreter
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)


class ClientSession:
    def __init__(self, client_connection: ClientConnection):
        self.client_connection = client_connection

    async def run_client_session(self) -> ReturnStatus:
        interpreter = HomeInterpreter(client_connection=self.client_connection)
        while True:
            interpreter_return_status = await interpreter.run_interpreter()
            if interpreter_return_status.type in (
                ClientReturnStatusType.EXIT,
                ClientReturnStatusType.EXIT_CLIENT_CONNECTION,
                ClientReturnStatusType.SWITCH_CLIENT_CONNECTION,
            ):
                return interpreter_return_status
            elif (
                interpreter_return_status.type
                == ClientReturnStatusType.SWITCH_INTERPRETER
            ):
                interpreter_type = interpreter_return_status.data["interpreter_type"]
                if interpreter_type == InterpreterType.HOME:
                    interpreter = HomeInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.LISTENERS:
                    interpreter = ListenersInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.AGENTS:
                    interpreter = AgentsInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.GENERATORS:
                    interpreter = GeneratorsInterpreter(
                        client_connection=self.client_connection,
                    )
                else:
                    raise NotImplementedError(
                        f"Interpreter type {interpreter_type} not implemented.",
                    )
