import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

import consortium.server.server_singletons as server_singletons
from consortium.framework._components._component_status import State
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
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
from consortium.server.models.config_models import ServerConfigModel
from consortium.server.objects.server_objects import ServerStatus
from consortium.server.server_exception_handlers import (
    register_server_exception_handlers,
)
from consortium.server.server_logging import LoggerType
from consortium.server.server_middleware import (
    check_if_remote_host_is_allowed,
    check_if_request_is_authenticated,
    check_if_server_is_shutting_down,
    log_rest_api_requests_and_responses,
)


class Server:
    def __init__(self, server_config: ServerConfigModel):
        self.server_config = server_config

        self.status = ServerStatus.STOPPED

        self._logger = logger.bind(
            logger_name="Server", logger_type=LoggerType.SERVER_LOGGER
        )
        self._app = FastAPI(
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
            lifespan=self._lifespan,
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

    @asynccontextmanager
    async def _lifespan(self, _app: FastAPI) -> AsyncGenerator[None, Any]:
        await self._server_startup_procedure()
        yield
        await self._server_shutdown_procedure()

    async def _server_shutdown_procedure(self) -> None:
        self._logger.info("Shutting down server...")
        self.status = ServerStatus.SHUTTING_DOWN

        # Signal to event hooks that the server is stopping first.
        await server_singletons.events_service.trigger_event(
            event=Event(event_type=EventType.STOP_SERVER),
        )

        # TODO: Add `timeout` to prevent hanging during shutdown. Do not replace
        #  `blocking` because we want non block (false, Any), block with finite timeout
        #  (true, float), block forever (true, None).
        self._logger.info("- Stopping all running listeners...")
        # Gracefully stop all running listeners.
        for listener in server_singletons.listeners_service.get_all_listeners():
            if listener.status.state == State.RUNNING:
                try:
                    await server_singletons.listeners_service.stop_listener_by_listener_id(
                        listener_id=listener.listener_id,
                        blocking=True,
                    )
                    self._logger.success(
                        "  - Stopped listener: {}.",
                        listener,
                    )
                except Exception as exc:
                    self._logger.error(
                        "  - Failed to stop listener {} due to error: {}",
                        listener,
                        exc,
                    )
            else:
                self._logger.info(
                    "  - Listener {} is not running, skipped stop procedure.",
                    listener,
                )

        # Gracefully stop all running agent generators.
        self._logger.info("- Stopping all running agent generators...")
        for (
            agent_generator
        ) in server_singletons.agent_generators_service.get_all_agent_generators():
            if agent_generator.status.state == State.RUNNING:
                try:
                    await server_singletons.agent_generators_service.stop_agent_generator_by_id(
                        agent_generator_id=agent_generator.agent_generator_id,
                        blocking=True,
                    )
                    self._logger.success(
                        "  - Stopped agent generator: {}.",
                        agent_generator,
                    )
                except Exception as exc:
                    self._logger.error(
                        "  - Failed to stop agent generator {} due to error: {}",
                        agent_generator,
                        exc,
                    )
            else:
                self._logger.info(
                    "  - Agent generator {} is not running, skipped stop procedure.",
                    agent_generator,
                )

        # Gracefully stop all running plugins.
        self._logger.info("- Stopping all running plugins...")
        for plugin in server_singletons.plugins_service.get_all_plugins():
            if plugin.status.state == State.RUNNING:
                try:
                    await server_singletons.plugins_service.stop_plugin_by_plugin_id(
                        plugin_id=plugin.plugin_id,
                        blocking=True,
                    )
                    self._logger.success(
                        "  - Stopped plugin: {}.",
                        plugin,
                    )
                except Exception as exc:
                    self._logger.error(
                        "  - Failed to stop plugin {} due to error: {}",
                        plugin,
                        exc,
                    )
            else:
                self._logger.info(
                    "  - Plugin {} is not running, skipped stop procedure.",
                    plugin,
                )

        self._logger.info("Server shutdown complete.")
        # Flush and complete the logger.
        await self._logger.complete()
        self.status = ServerStatus.STOPPED

    async def _server_startup_procedure(self) -> None:
        server_release = server_singletons.release_service.release
        self._logger.info(
            f'Starting server (v{server_release.version} "{server_release.codename}") '
            f"at {self.server_config.local_host}:{self.server_config.local_port}...",
        )
        self.status = ServerStatus.RUNNING

        # Setup all services and emit startup event.
        server_singletons.user_accounts_service.load_framework_user_accounts()
        # Load listener and agent profiles before running the C2 type resolution so
        # that any profiles that register custom listener/agent types are accounted for.
        await server_singletons.listener_profiles_service.load_framework_listener_profiles()
        await server_singletons.agent_profiles_service.load_framework_agent_profiles()
        server_singletons.c2_types_service.resolve_registered_compatible_agent_types_for_listener_types()
        # Load repository metadata before loading payloads metadata because the payloads
        # metadata depends on repository information.
        server_singletons.payloads_service._repository_service.load_repository_metadata()
        server_singletons.payloads_service.load_payloads_metadata()
        # assets and artifacts repository services can load repository metadata in any
        # order as they do not depend on any other service.
        server_singletons.assets_service.load_repository_metadata()
        server_singletons.artifacts_service.load_repository_metadata()
        await server_singletons.event_hooks_service.load_framework_event_hooks()
        # Load plugins last so that they can make use of other services during their
        # startup procedures.
        await server_singletons.plugins_service.load_framework_plugins()
        # Trigger the server start event after all services have been started.
        await server_singletons.events_service.trigger_event(
            event=Event(event_type=EventType.START_SERVER),
        )

    async def start_server(self) -> None:
        # Uvicorn will ordinarily warn of an already bound socket through its logger,
        # but we disabled it, so we need to do our own socket check to see if the
        # address is bindable.
        try:
            test_sock = socket.socket()
            test_sock.bind(
                (self.server_config.local_host, self.server_config.local_port),
            )
            test_sock.close()
        except OSError as exc:
            self._logger.error(
                "Failed to start server. Network error occurred while attempting to "
                "bind server to target socket address: {}. Check that no other "
                "process is already using the socket address {}:{}",
                exc,
                self.server_config.local_host,
                self.server_config.local_port,
            )
            return

        # Manually start the server with the uvicorn backend and disable the uvicorn
        # logger
        try:
            config = uvicorn.Config(
                self._app,
                host=self.server_config.local_host,
                port=self.server_config.local_port,
                # Suppress most of uvicorn's logging. Weird behaviour occurs when
                # attempting to catch/log errors for asynchronous tasks. When
                # exceptions happen in those tasks they bypass their supposed exception
                # handler and are raised at the uvicorn level of logging.
                log_level="error",
                # Disables Uvicorn's default server header to prevent C2 server
                # fingerprinting, replacing it with a custom specified header.
                server_header=False,
                headers=[("Server", self.server_config.server_header)]
                if self.server_config.server_header is not None
                else None,
            )
            server = uvicorn.Server(config)
            await server.serve()
        # This except block triggered before the server runs. Any other exceptions that
        # skip past the middleware are handled internally by uvicorn and will NOT
        # trigger this except block. The traceback can be disabled by setting the
        # log_level parameter to "critical" in the uvicorn.run() call above.
        except Exception as exc:
            self._logger.opt(colors=True, exception=exc).critical(
                "<white><RED><bold>Unrecoverable unhandled exception occurred in "
                "server</></></>",
            )
