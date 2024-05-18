import asyncio
import traceback
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.plugins_api_exceptions import (
    PluginAlreadyRunningError,
    PluginNotRunningError,
)
from consortium.server.framework.exceptions.plugins_framework_exceptions import (
    PluginCancellationError,
    PluginRuntimeError,
    PluginStartError,
    PluginStopError,
)
from consortium.server.objects.plugin_objects import PluginState, PluginStatus


# TODO: Prevent cancellation interruption
class BasePlugin(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        authors: list[str],
        autostart: bool,
    ):
        self.plugin_id = uuid.uuid4()
        self.name = name
        self.description = description
        self.authors = authors
        self.autostart = autostart

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
        for attr_name, attr_value in server_singletons.__dict__.items():
            # server_singletons also contains a reference to the server which we don't
            # want to set on the plugin.
            if attr_name != "server" and attr_name.endswith("_service"):
                setattr(self.server_services, attr_name, attr_value)
        self.plugin_project_folder = Path(__file__).parent
        self.plugin_logger = logger.bind(
            logger_name=f"Consortium Plugin {self}",
        )

        self._plugin_task = None

    @abstractmethod
    async def on_plugin_started(self) -> None:
        """
        This method is called when the plugin is started. To prevent the plugin
        from starting raise the framework error PluginStartError. Returning from this
        method will allow the plugin to continue starting.

        This method should be used to perform any setup or validation required before
        the plugin is started.
        """

    @abstractmethod
    async def on_plugin_running(self) -> None:
        """
        This method is called as the plugin's main runtime loop. To indicate that an
        error has occurred within this method raise the framework exception
        PluginRuntimeError. Returning from this method will allow the plugin to
        stop running. To detect when the plugin should stop running check the
        self.stop_plugin_event asynchronous event flag.

        This method should be used to perform the main runtime logic of the plugin.
        This includes listening for incoming connections, registering agents, sending
        tasks to and receiving results from agents.
        """

    @abstractmethod
    async def on_plugin_stopped(self) -> None:
        """
        This method is called when the plugin is stopped. To prevent the plugin
        from stopping raise the framework exception PluginStopError. Returning from
        this method will allow the plugin to set the self.stop_plugin_event
        asynchronous event flag which will signal to the plugin's main runtime loop
        to stop.

        This method should be used to perform any cleanup required before the plugin
        is stopped.
        """

    @abstractmethod
    async def on_plugin_cancelled(self) -> None:
        """
        This method is called when the plugin is cancelled. Cancellation occurs
        forcefully without setting the self.stop_plugin_event asynchronous event
        flag. To prevent the plugin from being cancelled raise the framework
        exception PluginCancellationError. Returning from this method will allow the
        plugin to be cancelled.

        This method should be used to perform any cleanup required before the plugin
        is forcefully cancelled.
        """

    @abstractmethod
    async def on_plugin_errored(self, exc: Exception) -> None:
        """
        This method is called when any unhandled exception or the framework exception
        PluginRuntimeError is raised within the plugin's main runtime loop. This
        excludes the exception asyncio.CancelledError which is raised when cancelling
        the plugin.
        """

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
                # The plugin is now cancelled
                self.status.transition_to_cancelled()
            except PluginRuntimeError as exc:
                # The plugin is now errored
                self.status.transition_to_errored(exc)
                try:
                    await self.on_plugin_errored(exc)
                except Exception as exc:
                    self.plugin_logger.opt(ansi=True).error(
                        "<bold><red>{}</></>",
                        traceback.format_exc(),
                    )
                    # The plugin is now fatally errored.
                    self.status.transition_to_fatal(exc)
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            self.status.transition_to_fatal(exc)
            # The plugin is now fatally errored.
            try:
                await self.on_plugin_errored(exc)
            except Exception as exc:
                self.plugin_logger.opt(ansi=True).error(
                    "<bold><red>{}</></>",
                    traceback.format_exc(),
                )
                self.status.transition_to_fatal(exc)

    async def start_plugin(self, autostart: bool = False) -> None:
        if self.status.state == PluginState.STARTED:
            raise PluginAlreadyRunningError(
                message="The plugin cannot be started because it is already running",
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
                raise exc
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored
            self.status.transition_to_fatal(exc)
            raise exc

        self._plugin_task = asyncio.create_task(self._run_plugin())

    async def stop_plugin(self) -> None:
        if self.status.state != PluginState.RUNNING:
            raise PluginNotRunningError(
                message="The plugin cannot be stopped because it is not running.",
            )

        try:
            await self.on_plugin_stopped()
        # PluginStopError is raised within on_plugin_stopped() to abort the
        # plugin stop process if preconditions are not met.
        except PluginStopError as exc:
            # The plugin has not changed from its running state.
            self.status.transition_to_running()
            raise exc
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored
            self.status.transition_to_fatal(exc)
            raise exc

        # Signal to the plugin to stop running.
        self.stop_plugin_event.set()

    async def cancel_plugin(self) -> None:
        if self.status.state != PluginState.RUNNING:
            raise PluginNotRunningError(
                message="The plugin cannot be cancelled because it is not running.",
            )

        try:
            await self.on_plugin_cancelled()
        # PluginCancellationError is raised within on_plugin_cancelled() to abort
        # the plugin cancellation process if preconditions are not met.
        except PluginCancellationError as exc:
            self.status.transition_to_running()
            raise exc
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored
            self.status.transition_to_fatal(exc)
            raise exc

        # Cancel the plugin.
        self._plugin_task.cancel()
        self._plugin_task = None

    def to_json(self) -> dict[str, str]:
        return {
            "plugin_id": str(self.plugin_id),
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "autostart": self.autostart,
            "status": self.status.to_json(),
        }

    def __str__(self) -> str:
        return f'"{self.name}" ({str(self.plugin_id)})'

    def __repr__(self) -> str:
        return (
            f"Plugin(name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}), "
            f"autostart={self.autostart!r})"
        )
