from consortium.client.client_connection import ClientConnection
from consortium.client.framework.base_command import ReturnStatus
from consortium.client.interpreters.agents_interpreter import AgentsInterpreter
from consortium.client.interpreters.generators_interpreter import GeneratorsInterpreter
from consortium.client.interpreters.home_interpreter import HomeInterpreter
from consortium.client.interpreters.interact_agent_interpreter import (
    InteractAgentInterpreter,
)
from consortium.client.interpreters.listeners_interpreter import ListenersInterpreter
from consortium.client.interpreters.use_agent_template_interpreter import (
    UseAgentTemplateInterpreter,
)
from consortium.client.interpreters.use_listener_template_interpreter import (
    UseListenerTemplateInterpreter,
)
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
                if interpreter_type == InterpreterType.HOME_INTERPRETER:
                    interpreter = HomeInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.LISTENERS_INTERPRETER:
                    interpreter = ListenersInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.AGENTS_INTERPRETER:
                    interpreter = AgentsInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.GENERATORS_INTERPRETER:
                    interpreter = GeneratorsInterpreter(
                        client_connection=self.client_connection,
                    )
                elif interpreter_type == InterpreterType.USE_AGENT_TEMPLATE_INTERPRETER:
                    interpreter = UseAgentTemplateInterpreter(
                        client_connection=self.client_connection,
                        agent_template=interpreter_return_status.data["agent_template"],
                    )
                elif (
                    interpreter_type
                    == InterpreterType.USE_LISTENER_TEMPLATE_INTERPRETER
                ):
                    interpreter = UseListenerTemplateInterpreter(
                        client_connection=self.client_connection,
                        listener_template=interpreter_return_status.data[
                            "listener_template"
                        ],
                    )
                elif interpreter_type == InterpreterType.INTERACT_AGENT_INTERPRETER:
                    interpreter = InteractAgentInterpreter(
                        client_connection=self.client_connection,
                        agent=interpreter_return_status.data["agent"],
                    )
                else:
                    raise NotImplementedError(
                        f"Interpreter type {interpreter_type} not implemented.",
                    )
