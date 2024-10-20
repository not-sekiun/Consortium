import uuid
from datetime import datetime

from consortium.client.client_rest_api_connection import ClientRESTAPIConnection
from consortium.client.client_websockets_api_connection import (
    ClientWebsocketsAPIConnection,
)
from consortium.client.exceptions.client_session_exceptions import (
    ClientSessionAlreadyConnectedException,
    ClientSessionNotConnectedException,
)
from consortium.client.interpreters import (
    AgentsInterpreter,
    GeneratorsInterpreter,
    HomeInterpreter,
    InteractAgentInterpreter,
    ListenersInterpreter,
    UseAgentTemplateInterpreter,
    UseListenerTemplateInterpreter,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)
from consortium.client.repl_framework.base_command import ReturnStatus


class ClientSession:
    def __init__(
        self,
        username: str,
        password: str,
        remote_host: str,
        remote_port: int,
    ):
        self.client_session_id = uuid.uuid4()
        self.name = ""
        self.description = ""
        self.username = username
        self.password = password
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.connected = False
        self.datetime_connected = None

        self.client_rest_api_connection = None
        self.client_websockets_api_connection = None

    def __str__(self) -> str:
        return f"'{self.name}' ({self.client_session_id})"

    def __repr__(self) -> str:
        return (
            f"ClientSession(username='{self.username}', password='{self.password}' "
            f"remote_host='{self.remote_host}', remote_port={self.remote_port})"
        )

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        if self.connected:
            raise ClientSessionAlreadyConnectedException

        client_rest_api_connection = ClientRESTAPIConnection(
            username=self.username,
            password=self.password,
            remote_host=self.remote_host,
            remote_port=self.remote_port,
        )
        await client_rest_api_connection.connect()
        client_websockets_api_connection = ClientWebsocketsAPIConnection(
            remote_host=self.remote_host,
            remote_port=self.remote_port,
            json_web_token=client_rest_api_connection.json_web_token,
        )
        await client_websockets_api_connection.connect()

        self.client_rest_api_connection = client_rest_api_connection
        self.client_websockets_api_connection = client_websockets_api_connection
        self.datetime_connected = datetime.now()
        self.connected = True

    async def disconnect(self) -> None:
        if not self.connected:
            raise ClientSessionNotConnectedException

        await self.client_websockets_api_connection.disconnect()
        await self.client_rest_api_connection.disconnect()

        self.client_rest_api_connection = None
        self.client_websockets_api_connection = None
        self.connected = False

    async def run(self) -> ReturnStatus:
        interpreter = HomeInterpreter(client_session=self)

        while True:
            interpreter_return_status = await interpreter.run_interpreter()
            if interpreter_return_status.type in (
                ClientReturnStatusType.EXIT,
                ClientReturnStatusType.EXIT_CLIENT_SESSION,
                ClientReturnStatusType.SWITCH_CLIENT_SESSION,
            ):
                return interpreter_return_status
            elif (
                interpreter_return_status.type
                == ClientReturnStatusType.SWITCH_INTERPRETER
            ):
                interpreter_type = interpreter_return_status.data["interpreter_type"]
                if interpreter_type == InterpreterType.HOME_INTERPRETER:
                    interpreter = HomeInterpreter(
                        client_session=self,
                    )
                elif interpreter_type == InterpreterType.LISTENERS_INTERPRETER:
                    interpreter = ListenersInterpreter(
                        client_session=self,
                    )
                elif interpreter_type == InterpreterType.AGENTS_INTERPRETER:
                    interpreter = AgentsInterpreter(
                        client_session=self,
                    )
                elif interpreter_type == InterpreterType.GENERATORS_INTERPRETER:
                    interpreter = GeneratorsInterpreter(
                        client_session=self,
                    )
                elif interpreter_type == InterpreterType.USE_AGENT_TEMPLATE_INTERPRETER:
                    interpreter = UseAgentTemplateInterpreter(
                        client_session=self,
                        agent_template=interpreter_return_status.data["agent_template"],
                    )
                elif (
                    interpreter_type
                    == InterpreterType.USE_LISTENER_TEMPLATE_INTERPRETER
                ):
                    interpreter = UseListenerTemplateInterpreter(
                        client_session=self,
                        listener_template=interpreter_return_status.data[
                            "listener_template"
                        ],
                    )
                elif interpreter_type == InterpreterType.INTERACT_AGENT_INTERPRETER:
                    interpreter = InteractAgentInterpreter(
                        client_session=self,
                        agent=interpreter_return_status.data["agent"],
                    )
                else:
                    assert False, (
                        "Failed to switch to interpreter with interpreter type "
                        f"'{interpreter_type}'. Invalid interpreter type was returned "
                        "as part of the return status."
                    )
