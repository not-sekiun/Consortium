import socket
import traceback

import uvicorn
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

import consortium.server.server_singletons as server_singletons
from consortium.server.api.agent_generators_api import (
    router as agent_generators_api_router,
)
from consortium.server.api.agent_templates_api import (
    router as agent_templates_api_router,
)
from consortium.server.api.agents_api import router as agents_api_router
from consortium.server.api.artifacts_api import router as artifacts_api_router
from consortium.server.api.assets_api import router as assets_api_router
from consortium.server.api.events_api import router as events_api_router
from consortium.server.api.listener_templates_api import (
    router as listener_templates_api_router,
)
from consortium.server.api.listeners_api import router as listeners_api_router
from consortium.server.api.login_api import router as login_api_router
from consortium.server.api.logout_api import router as logout_api_router
from consortium.server.api.payloads_api import router as payloads_api_router
from consortium.server.api.server_api import router as server_api_router
from consortium.server.api.user_accounts_api import router as user_accounts_api_router
from consortium.server.api.users_api import router as users_api_router
from consortium.server.models.server_models import ServerConfigModel
from consortium.server.objects.server_objects import ServerStatus
from consortium.server.server_config import SERVER_RELEASE
from consortium.server.server_event_handlers import lifespan
from consortium.server.server_exception_handlers import (
    register_server_exception_handlers,
)
from consortium.server.server_middleware import (
    check_if_remote_host_is_allowed,
    check_if_request_is_authenticated,
    check_if_server_is_shutting_down,
    log_rest_api_requests_and_responses,
    spoof_response_server_header,
)

# These services need to have their managed objects stopped when the server is shutting
# down.
listeners_service = server_singletons.listeners_service
plugins_service = server_singletons.plugins_service


class Server:
    def __init__(
        self,
        server_config: ServerConfigModel,
    ):
        self.server_config = server_config

        self.status = ServerStatus.STOPPED

        self._server_logger = logger.bind(logger_name="Server")
        self._app = FastAPI(
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
            lifespan=lifespan,
        )

        # Configure custom api endpoints.
        self._app.include_router(login_api_router)
        self._app.include_router(logout_api_router)
        self._app.include_router(server_api_router)
        self._app.include_router(users_api_router)
        self._app.include_router(user_accounts_api_router)
        self._app.include_router(listener_templates_api_router)
        self._app.include_router(listeners_api_router)
        self._app.include_router(agent_templates_api_router)
        self._app.include_router(agent_generators_api_router)
        self._app.include_router(agents_api_router)
        self._app.include_router(events_api_router)
        self._app.include_router(assets_api_router)
        self._app.include_router(artifacts_api_router)
        self._app.include_router(payloads_api_router)

        # Configure middleware. Order matters, the last middleware added will be the
        # first to be executed on the request and the last to be executed on the
        # response.
        self._app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=check_if_server_is_shutting_down,
        )
        self._app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=check_if_request_is_authenticated,
        )
        self._app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=check_if_remote_host_is_allowed,
        )
        self._app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=spoof_response_server_header,
        )
        self._app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=log_rest_api_requests_and_responses,
        )

        # Register custom exception handlers, these are used to standardize the error
        # responses returned by the server and to account for custom exceptions that
        # may be raised by the server.
        register_server_exception_handlers(self._app)

        # TODO: Make this hack more elegant.
        # Manually modify the openapi schema to remove the default 422 response from
        # the /api/login endpoint (https://github.com/tiangolo/fastapi/issues/660).
        del self._app.openapi()["paths"]["/api/login"]["post"]["responses"]["422"]
        # Workaround to modify the openapi schema to add in null detail responses that
        # were removed. Go bug tiangolo about this issue because it still has yet to be
        # fixed (https://github.com/tiangolo/fastapi/issues/1082).
        for schema_name, schema in self._app.openapi()["components"]["schemas"].items():
            if "ErrorModel" in schema_name and "examples" in schema:
                if "detail" not in schema["examples"][0]["error"]:
                    schema["examples"][0]["error"]["detail"] = None
                else:
                    # Dictionaries are in insertion order in python 3.7+ so this
                    # moves the detail key to the end of the dictionary to make the
                    # example look cleaner.
                    reordered_dict = {
                        key: schema["examples"][0]["error"][key]
                        for key in ["code", "message", "detail"]
                    }
                    schema["examples"][0]["error"] = reordered_dict

    def _shutdown_server(self) -> None:
        # TODO: run all the necessary shutdown procedures, this is where we gracefully
        #  shutdown listeners, notify clients and agents of the shutdown, etc.
        self._server_logger.info("Shutting down server...")
        self.status = ServerStatus.SHUTTING_DOWN

    def start_server(self) -> None:
        # Manually start the server with the uvicorn backend and disable the uvicorn
        # logger
        self._server_logger.info(
            f'Starting server (v{SERVER_RELEASE.version} "{SERVER_RELEASE.codename}") '
            f"at {self.server_config.local_host}:{self.server_config.local_port}...",
        )
        self.status = ServerStatus.RUNNING

        # Uvicorn will ordinarily warn of an already bound socket through its logger,
        # but we disabled it, so we need to do our own socket check to see if the
        # address is bindable.
        try:
            test_sock = socket.socket()
            test_sock.bind(
                (self.server_config.local_host, self.server_config.local_port),
            )
            test_sock.close()
        except socket.error as exc:
            self._server_logger.error(
                f"Network error occurred while attempting to bind server to target "
                f"socket address: {exc}",
            )
            return

        try:
            uvicorn.run(
                self._app,
                host=self.server_config.local_host,
                port=self.server_config.local_port,
                # Suppress most of uvicorn's logging. Weird behaviour occurs when
                # attempting to catch/log errors for asynchronous tasks. When
                # exceptions happen in those tasks they bypass their supposed exception
                # handler and are raised at the uvicorn level of logging.
                log_level="error",
                # Disables Uvicorn's server header to prevent C2 server fingerprinting.
                server_header=False,
            )
        # This except block triggered before the server runs. Any other exceptions that
        # skip past the middleware are handled internally by uvicorn and will NOT
        # trigger this except block. The traceback can be disabled by setting the
        # log_level parameter to "critical" in the uvicorn.run() call above.
        except Exception:
            logger.opt(ansi=True).critical(
                "<red><bold>Unrecoverable unhandled exception occurred while server "
                "was starting:\n{}</></>",
                traceback.format_exc(),
            )
            return

        # Uvicorn blocks the main thread until a keyboard interrupt is sent to it
        # signifying a shutdown. Execution is continued here where we can perform any
        # graceful shutdowns such as notifying clients and agents of the shutdown as
        # well as killing any running listeners.
        self._shutdown_server()
        self._server_logger.info("Server shutdown complete. See you again ^_^")
        self.status = ServerStatus.STOPPED
