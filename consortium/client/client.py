from aiohttp.client import ClientConnectionError
from websockets.exceptions import WebSocketException

import consortium.client.client_singletons as client_singletons
from consortium.client.client_session import ClientSession
from consortium.client.commands.core_commands.banner import BannerCommand
from consortium.client.exceptions.client_sessions_service_exceptions import (
    ClientSessionConnectionError,
)
from consortium.client.exceptions.rest_api_exceptions import (
    RestAPIError,
    RestAPIOperationError,
)
from consortium.client.exceptions.websockets_api_exceptions import (
    WebsocketsAPIError,
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
from consortium.client.interpreters.disconnected_interpreter import (
    DisconnectedInterpreter,
)
from consortium.client.models.client_models import ClientConfig
from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ExitClientSessionSignal,
    ExitClientSignal,
    InterpreterSignal,
    SwitchAgentsInterpreterSignal,
    SwitchClientSessionSignal,
    SwitchGeneratorsInterpreterSignal,
    SwitchHomeInterpreterSignal,
    SwitchInteractAgentInterpreterSignal,
    SwitchListenersInterpreterSignal,
    SwitchUseAgentTemplateInterpreterSignal,
    SwitchUseListenerTemplateInterpreterSignal,
)
from consortium.client.utils.printer_utils import print_error, print_info, print_success


class Client:
    def __init__(self, client_config: ClientConfig):
        self._client_sessions_service = client_singletons.client_sessions_service
        self._client_config = client_config

    @staticmethod
    async def _handle_client_session_interpreters(
        client_session: ClientSession,
    ) -> InterpreterSignal:
        interpreter = HomeInterpreter(client_session=client_session)

        while True:
            interpreter_signal = await interpreter.run()

            match interpreter_signal:
                case (
                    ExitClientSignal()
                    | ExitClientSessionSignal()
                    | SwitchClientSessionSignal()
                ):
                    return interpreter_signal
                case SwitchHomeInterpreterSignal():
                    interpreter = HomeInterpreter(client_session=client_session)
                case SwitchListenersInterpreterSignal():
                    interpreter = ListenersInterpreter(client_session=client_session)
                case SwitchAgentsInterpreterSignal():
                    interpreter = AgentsInterpreter(client_session=client_session)
                case SwitchGeneratorsInterpreterSignal():
                    interpreter = GeneratorsInterpreter(client_session=client_session)
                case SwitchUseAgentTemplateInterpreterSignal():
                    interpreter = UseAgentTemplateInterpreter(
                        client_session=client_session,
                        agent_template=interpreter_signal.agent_template,
                    )
                case SwitchUseListenerTemplateInterpreterSignal():
                    interpreter = UseListenerTemplateInterpreter(
                        client_session=client_session,
                        listener_template=interpreter_signal.listener_template,
                    )
                case SwitchInteractAgentInterpreterSignal():
                    interpreter = InteractAgentInterpreter(
                        client_session=client_session,
                        agent=interpreter_signal.agent,
                    )
                case _:
                    raise AssertionError(
                        "Failed to handle return signal from interpreter. The return "
                        f"signal '{interpreter_signal}' is not supported."
                    )

            # if interpreter_signal.type in (
            #     ReturnStatusType.EXIT_CLIENT,
            #     ReturnStatusType.EXIT_CLIENT_SESSION,
            #     ReturnStatusType.SWITCH_CLIENT_SESSION,
            # ):
            #     return interpreter_signal
            # elif interpreter_signal.type == ReturnStatusType.SWITCH_INTERPRETER:
            #     interpreter_type = interpreter_signal.data["interpreter_type"]
            #     if interpreter_type == InterpreterType.HOME_INTERPRETER:
            #         interpreter = HomeInterpreter(client_session=client_session)
            #     elif interpreter_type == InterpreterType.LISTENERS_INTERPRETER:
            #         interpreter = ListenersInterpreter(client_session=client_session)
            #     elif interpreter_type == InterpreterType.AGENTS_INTERPRETER:
            #         interpreter = AgentsInterpreter(client_session=client_session)
            #     elif interpreter_type == InterpreterType.GENERATORS_INTERPRETER:
            #         interpreter = GeneratorsInterpreter(client_session=client_session)
            #     elif interpreter_type == InterpreterType.USE_AGENT_TEMPLATE_INTERPRETER:
            #         interpreter = UseAgentTemplateInterpreter(
            #             client_session=client_session,
            #             agent_template=interpreter_signal.data["agent_template"],
            #         )
            #     elif (
            #         interpreter_type
            #         == InterpreterType.USE_LISTENER_TEMPLATE_INTERPRETER
            #     ):
            #         interpreter = UseListenerTemplateInterpreter(
            #             client_session=client_session,
            #             listener_template=interpreter_signal.data["listener_template"],
            #         )
            #     elif interpreter_type == InterpreterType.INTERACT_AGENT_INTERPRETER:
            #         interpreter = InteractAgentInterpreter(
            #             client_session=client_session,
            #             agent=interpreter_signal.data["agent"],
            #         )
            #     else:
            #         raise AssertionError(
            #             "Failed to switch to interpreter with interpreter type "
            #             f"'{interpreter_type}'. Invalid interpreter type was returned "
            #             "as part of the return status."
            #         )
            # else:
            #     raise AssertionError(
            #         "Failed to handle return status from interpreter. The return "
            #         f"status type '{interpreter_signal.type}' is not supported."
            #     )

    async def run(self) -> None:
        try:
            client_session = await self._client_sessions_service.create_client_session(
                username=self._client_config.username,
                password=self._client_config.password,
                remote_host=self._client_config.remote_host,
                remote_port=self._client_config.remote_port,
            )
            print_success(
                f"Connected to server "
                f"{self._client_config.remote_host}:{self._client_config.remote_port} "
                f"as '{self._client_config.username}'.",
            )
        except (
            # Exceptions raised when failing to log in to the REST API.
            RestAPIError,
            # Exceptions raised when failing to connect to the Websockets API.
            WebsocketsAPIError,
            # Generic network exceptions.
            ClientSessionConnectionError,
            WebSocketException,
            ClientConnectionError,
            TimeoutError,
            OSError,
        ) as exc:
            client_session = None
            print_error(
                f"Failed to connect to server "
                f"{self._client_config.remote_host}:{self._client_config.remote_port}. "
                f"An error occurred while attempting to login. "
                f"{exc.__class__.__name__}: {exc}",
            )

        # Display banner once at client startup.
        await BannerCommand().run(
            context=Context(
                command="banner",
                arguments=[],
                raw_input="banner",
                client_session=client_session,
                interpreter_context={},
            ),
        )

        # Run the initial interpreter. Either we run a special disconnected interpreter
        # that can run independently of any client session in the case where a
        # connection failed, or we run the client session's own interpreter loop for a
        # successful initial connection.
        if client_session is None:
            interpreter_signal = await DisconnectedInterpreter().run()
        else:
            interpreter_signal = await self._handle_client_session_interpreters(
                client_session=client_session,
            )

        # Based on successive client session return statuses decide whether to continue
        # running client sessions or not.
        while True:
            match interpreter_signal:
                case ExitClientSignal():
                    return
                case ExitClientSessionSignal():
                    interpreter_signal = await DisconnectedInterpreter().run()
                case SwitchClientSessionSignal():
                    try:
                        # The client connection switched to has no guarantee of being valid
                        interpreter_signal = (
                            await self._handle_client_session_interpreters(
                                client_session=interpreter_signal.client_session
                            )
                        )
                    except RestAPIOperationError as exc:
                        print_error(
                            f"Failed to switch to client session "
                            f"{interpreter_signal.client_session}. {exc}",
                        )
                        print_info(
                            "Switching to disconnected interpreter due to error raised "
                            + "while switching client sessions..."
                        )
                        interpreter_signal = await DisconnectedInterpreter().run()
                    # # Catch any fatal errors raised by the client session. If a fatal error
                    # # occurs in any of the interpreters it is already printed. We catch it
                    # # here and kill the session.
                    # except Exception as exc:
                    #     print_error(
                    #         f"Unhandled exception occurred while switching to client "
                    #         f"session {return_status.data['client_session']}. "
                    #         f"{exc.__class__.__name__}: {exc}"
                    #     )
                    #     console.print_exception(show_locals=True)
                    #     print_info("Removing the faulty client session...")
                    #     self._client_sessions_service.remove_client_session_by_client_session_id(
                    #         client_session_id=return_status.data[
                    #             "client_session"
                    #         ].client_session_id,
                    #     )
                    #     return_status = await DisconnectedInterpreter().run()
                case _:
                    raise AssertionError(
                        "Failed to handle return signal from interpreter. The return "
                        f"signal '{interpreter_signal}' is not supported."
                    )

            # # `SwitchInterpreterSignal` will never be returned since the
            # # client session itself will handle that return signal.
            # if interpreter_signal.type == ReturnStatusType.EXIT_CLIENT:
            #     return
            # elif interpreter_signal.type == ReturnStatusType.EXIT_CLIENT_SESSION:
            #     interpreter_signal = await DisconnectedInterpreter().run()
            # elif interpreter_signal.type == ReturnStatusType.SWITCH_CLIENT_SESSION:
            #     try:
            #         # The client connection switched to has no guarantee of being valid
            #         interpreter_signal = await self._handle_client_session_interpreters(
            #             client_session=interpreter_signal.data["client_session"]
            #         )
            #     except RestAPIOperationError as exc:
            #         print_error(
            #             f"Failed to switch to client session "
            #             f"{interpreter_signal.data['client_session']}. {exc}",
            #         )
            #         print_info(
            #             "Switching to disconnected interpreter due to error raised "
            #             + "while switching client sessions..."
            #         )
            #         interpreter_signal = await DisconnectedInterpreter().run()
            #     # # Catch any fatal errors raised by the client session. If a fatal error
            #     # # occurs in any of the interpreters it is already printed. We catch it
            #     # # here and kill the session.
            #     # except Exception as exc:
            #     #     print_error(
            #     #         f"Unhandled exception occurred while switching to client "
            #     #         f"session {return_status.data['client_session']}. "
            #     #         f"{exc.__class__.__name__}: {exc}"
            #     #     )
            #     #     console.print_exception(show_locals=True)
            #     #     print_info("Removing the faulty client session...")
            #     #     self._client_sessions_service.remove_client_session_by_client_session_id(
            #     #         client_session_id=return_status.data[
            #     #             "client_session"
            #     #         ].client_session_id,
            #     #     )
            #     #     return_status = await DisconnectedInterpreter().run()
            # else:
            #     raise AssertionError(
            #         "Failed to handle return status from interpreter. The return "
            #         f"status type '{interpreter_signal.type}' is not supported."
            #     )
