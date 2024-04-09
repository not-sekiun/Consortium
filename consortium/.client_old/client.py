import consortium.client.client_singletons as client_singletons
from consortium.client.client_exceptions import InvalidReturnStatus
from consortium.client.client_session import ClientSession
from consortium.client.commands.global_commands.banner import BannerCommand
from consortium.client.interpreters.agents_interpreter import AgentsInterpreter
from consortium.client.interpreters.create_listener_interpreter import (
    CreateListenerInterpreter,
)
from consortium.client.interpreters.disconnected_interpreter import (
    DisconnectedInterpreter,
)
from consortium.client.interpreters.generators_interpreter import GeneratorsInterpreter
from consortium.client.interpreters.home_interpreter import HomeInterpreter
from consortium.client.interpreters.listeners_interpreter import ListenersInterpreter
from consortium.client.objects.client_objects import ClientConfig
from consortium.client.objects.command_objects import (
    ExitClientSessionReturnStatus,
    ExitProgramReturnStatus,
    InterpreterCommand,
    SwitchClientSessionReturnStatus,
    SwitchInterpreterReturnStatus,
    SwitchToCreateListenerInterpreterReturnStatus,
)
from consortium.client.objects.interpreter_objects import InterpreterType
from consortium.client.utils.standard_io_utils import print_error, print_success

client_sessions_service = client_singletons.client_sessions_service


class Client:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    async def run_client(self):
        # Attempt to log in to server and initialize the current interpreter.
        try:
            client_session = ClientSession(
                client_config=self.client_config,
            )
            await client_session.login()
            print_success(
                f"Successfully logged in to server: {self.client_config.remote_host}:{self.client_config.remote_port}",
            )
            current_interpreter = HomeInterpreter()
            client_singletons.client_sessions_service.add_client_session(client_session)
        except Exception as exc:
            print_error(f"Failed to login to server: {str(exc)}")
            client_session = None
            current_interpreter = DisconnectedInterpreter()

        # Display startup banner.
        mock_interpreter_command = InterpreterCommand(
            command="banner",
            arguments=[],
            original_string="banner",
        )
        await BannerCommand().run_command(
            interpreter_command=mock_interpreter_command,
            client_session=client_session,
        )

        interpreter_type_enum_to_interpreter_class_map = {
            InterpreterType.HOME: HomeInterpreter,
            InterpreterType.LISTENERS: ListenersInterpreter,
            InterpreterType.AGENTS: AgentsInterpreter,
            InterpreterType.GENERATORS: GeneratorsInterpreter,
            InterpreterType.CREATE_LISTENER: CreateListenerInterpreter,
        }

        # Manage the switching of sessions or interpreters.
        while True:
            interpreter_return_status = await current_interpreter.run_interpreter()

            if isinstance(
                interpreter_return_status,
                SwitchToCreateListenerInterpreterReturnStatus,
            ):
                current_interpreter = CreateListenerInterpreter(
                    listener_template_id=interpreter_return_status.listener_template_id,
                )
            elif isinstance(interpreter_return_status, SwitchInterpreterReturnStatus):
                interpreter_type = interpreter_return_status.interpreter_type
                interpreter_class = interpreter_type_enum_to_interpreter_class_map[
                    interpreter_type
                ]
                current_interpreter = interpreter_class().run_interpreter(
                    client_session=client_session,
                )
            elif isinstance(interpreter_return_status, SwitchClientSessionReturnStatus):
                client_session = (
                    client_sessions_service.get_client_session_by_client_session_id(
                        client_session_id=interpreter_return_status.client_session_id,
                    )
                )
                current_interpreter = HomeInterpreter()
            elif isinstance(interpreter_return_status, ExitClientSessionReturnStatus):
                client_session = None
                current_interpreter = DisconnectedInterpreter()
            elif isinstance(interpreter_return_status, ExitProgramReturnStatus):
                return
            else:
                # This should never be reached unless a programmer error is made.
                raise InvalidReturnStatus(
                    f"Invalid return status received from interpreter: {interpreter_return_status}",
                )
