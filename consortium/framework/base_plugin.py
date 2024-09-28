import asyncio
import sys
import traceback
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework.exceptions.plugins_framework_exceptions import (
    PluginRuntimeError,
    PluginStartError,
    PluginStopError,
)
from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
    EmptyPluginNameError,
    PluginAlreadyRunningError,
    PluginConfigurationParameterTypeError,
    PluginNotRunningError,
    PluginRuntimeError as PluginRuntimeFrameworkError,
    PluginStartError as PluginStartFrameworkError,
    PluginStopError as PluginStopFrameworkError,
    RequiredPluginConfigurationParameterNotDeclaredError,
)
from consortium.server.objects.plugin_objects import PluginState, PluginStatus
from consortium.server.server_logging import LoggerType


class BasePlugin(ABC):
    name: str
    description: str = ""
    authors: set[str] | None = None
    autostart: bool = True

    def __init__(self):
        self.plugin_id = uuid.uuid4()

        # Original status.state is set to INITIALIZED.
        self.status = PluginStatus()
        # self.environment is used to store any information that the plugin may need
        # to store and share amongst its user defined methods.
        self.environment = SimpleNamespace()
        # self.stop_plugin_event used to signal to the plugin runtime loop to exit.
        # The implementation of the plugin runtime loop should check this event
        # periodically and exit if it is set.
        self.stop_plugin_event = asyncio.Event()
        # Server services are all accessed through the self.server_services attribute.
        self.server_services = SimpleNamespace()
        self.server_services.agent_profiles_service = (
            server_singletons.agent_profiles_service
        )
        self.server_services.agent_templates_service = (
            server_singletons.agent_templates_service
        )
        self.server_services.agent_generators_service = (
            server_singletons.agent_generators_service
        )
        self.server_services.agents_service = server_singletons.agents_service
        self.server_services.application_service = server_singletons.application_service
        self.server_services.c2_types_service = server_singletons.c2_types_service
        self.server_services.event_hooks_service = server_singletons.event_hooks_service
        self.server_services.listener_profiles_service = (
            server_singletons.listener_profiles_service
        )
        self.server_services.listener_templates_service = (
            server_singletons.listener_templates_service
        )
        self.server_services.listeners_service = server_singletons.listeners_service
        self.server_services.plugins_service = server_singletons.plugins_service
        self.server_services.user_accounts_service = (
            server_singletons.user_accounts_service
        )
        self.server_services.users_service = server_singletons.users_service
        self.plugin_logger = logger.bind(
            logger_name=f"Plugin {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        self.plugin_project_folder_path = Path(
            sys.modules[self.__module__].__file__,
        ).parents[0]

        self._plugin_task = None

    def __init_subclass__(cls, **kwargs):
        if cls.authors is None:
            cls.authors = set()

        # Check the existence of a provided plugin name first so that we can
        # reference the plugin name for every other error message.
        if not hasattr(cls, "name"):
            # The plugin is identified by its name, but at this point we are still
            # validating the name parameter, so we refer to it by its filepath for now.
            raise RequiredPluginConfigurationParameterNotDeclaredError(
                plugin_str=sys.modules[cls.__module__].__file__,
                parameter_name="name",
            )
        if not isinstance(cls.name, str):
            raise PluginConfigurationParameterTypeError(
                plugin_str=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyPluginNameError(
                plugin_filepath=sys.modules[cls.__module__].__file__,
            )
        # From here onwards we can refer to the plugin by its name.
        if not isinstance(cls.description, str):
            raise PluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(cls.authors, set):
            raise PluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="authors",
                parameter_type="set",
            )
        for author in cls.authors:
            if not isinstance(author, str):
                raise PluginConfigurationParameterTypeError(
                    plugin_str=cls.name,
                    error_message=(
                        "The elements in the authors set must be strings for plugin "
                        f"'{cls.name}'."
                    ),
                )
        if not isinstance(cls.autostart, bool):
            raise PluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="autostart",
                parameter_type="bool",
            )

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.plugin_id)})"

    def __repr__(self) -> str:
        return (
            f"Plugin(name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}), "
            f"autostart={self.autostart!r})"
        )

    @abstractmethod
    async def on_plugin_started(self) -> None: ...

    @abstractmethod
    async def on_plugin_running(self) -> None: ...

    @abstractmethod
    async def on_plugin_stopped(self) -> None: ...

    @abstractmethod
    async def on_plugin_cancelled(self) -> None: ...

    @abstractmethod
    async def on_plugin_errored(self, exc: Exception) -> None: ...

    async def start_plugin(self, autostart: bool = False) -> None:
        if self.status.state == PluginState.STARTED:
            raise PluginAlreadyRunningError(
                plugin=str(self),
                error_message=(
                    "The plugin cannot be started because it is already running"
                ),
            )

        # Clear the signal to the plugin to stop running if it is set, so it won't
        # instantly stop.
        self.stop_plugin_event.clear()

        # The plugin is now started.
        self.status.transition_to_started()
        try:
            await self.on_plugin_started()
        # PluginStartError is raised within on_plugin_started() to abort the
        # plugin start process if preconditions are not met.
        except PluginStartError as exc:
            # The plugin is now initialized.
            self.status.transition_to_initialized()
            if not autostart:
                # If the plugin was not automatically started, it was started through
                # the REST API. An automatically started plugin has no client to return
                # any error response to.
                raise PluginStartFrameworkError(
                    plugin=str(self),
                    start_error_message=exc.message,
                    detail=exc.detail,
                )
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored.
            self.status.transition_to_fatal(
                plugin=str(self),
                exception=exc,
            )
            raise exc

        self._plugin_task = asyncio.create_task(self._run_plugin())

    async def stop_plugin(self) -> None:
        if self.status.state != PluginState.RUNNING:
            raise PluginNotRunningError(
                plugin=str(self),
                error_message="The plugin cannot be stopped because it is not running.",
            )

        try:
            await self.on_plugin_stopped()
        # PluginStopError is raised within on_plugin_stopped() to abort the
        # plugin stop process if preconditions are not met.
        except PluginStopError as exc:
            # The plugin has not changed from its running state.
            self.status.transition_to_running()
            raise PluginStopFrameworkError(
                plugin=str(self),
                stop_error_message=exc.message,
                detail=exc.detail,
            )
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored.
            self.status.transition_to_fatal(
                plugin=str(self),
                exception=exc,
            )
            raise exc

        # Signal to the plugin to stop running.
        self.stop_plugin_event.set()

    async def cancel_plugin(self) -> None:
        if self.status.state != PluginState.RUNNING:
            raise PluginNotRunningError(
                plugin=str(self),
                error_message=(
                    "The plugin cannot be cancelled because it is not running."
                ),
            )

        # Cancel the plugin.
        self._plugin_task.cancel()

        # Wait for the task to finish. Then remove the task reference.
        while not self._plugin_task.done():
            await asyncio.sleep(0.1)
        self._plugin_task = None

        try:
            await self.on_plugin_cancelled()
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored.
            self.status.transition_to_fatal(
                plugin=str(self),
                exception=exc,
            )
            raise exc

    def to_json(self) -> dict[str, str]:
        return {
            "plugin_id": str(self.plugin_id),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "autostart": self.autostart,
            "status": self.status.to_json(),
        }

    async def _run_plugin(self):
        try:
            try:
                # The plugin is now running.
                self.status.transition_to_running()
                await self.on_plugin_running()

                # The plugin is now stopped.
                self.status.transition_to_stopped()
                self._plugin_task = None
            except asyncio.CancelledError:
                # The plugin is now cancelled.
                self.status.transition_to_cancelled()
            except PluginRuntimeError as exc:
                exc = PluginRuntimeFrameworkError(
                    plugin=str(self),
                    runtime_error_message=exc.message,
                    detail=exc.detail,
                )
                # The plugin is now errored.
                self.status.transition_to_errored(exc)
                try:
                    await self.on_plugin_errored(exc)
                except Exception as exc:
                    self.plugin_logger.opt(ansi=True).error(
                        "<bold><red>{}</></>",
                        traceback.format_exc(),
                    )
                    # The plugin is now fatally errored.
                    self.status.transition_to_fatal(
                        plugin=str(self),
                        exception=exc,
                    )
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            self.status.transition_to_fatal(
                plugin=str(self),
                exception=exc,
            )
            # The plugin is now fatally errored.
            try:
                await self.on_plugin_errored(exc)
            except Exception as exc:
                self.plugin_logger.opt(ansi=True).error(
                    "<bold><red>{}</></>",
                    traceback.format_exc(),
                )
                self.status.transition_to_fatal(
                    plugin=str(self),
                    exception=exc,
                )
