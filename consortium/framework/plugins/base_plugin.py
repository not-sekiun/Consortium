import asyncio
import sys
import traceback
import uuid
import types
import pathlib

import loguru
from packaging import version, specifiers

import consortium.server.server_singletons as server_singletons
from consortium.framework.exceptions.plugins_framework_exceptions import (
    PluginRuntimeError,
    PluginStartError,
    PluginStopError,
)
from consortium.framework.plugins.exceptions import (
    EmptyPluginNameError,
    InvalidPluginConfigurationParameterTypeError,
    InvalidPluginVersionError,
    PluginAlreadyRunningError,
    PluginNotRunningError,
    PluginRuntimeError as PluginRuntimeFrameworkError,
    PluginStartError as PluginStartFrameworkError,
    PluginStopError as PluginStopFrameworkError,
    RequiredPluginConfigurationParameterNotDeclaredError, InvalidFrameworkVersionSpecifierError,
)
from consortium.framework.plugins import plugin_status
from consortium.server.server_logging import LoggerType


class BasePlugin:
    """
    Base class for all plugins in the Consortium framework.

    Attributes:
        plugin_id:
            The primary identifier for the plugin. This identifier is a version 4 UUID
            string represented as a `uuid.UUID` object. Plugin IDs are used as primary
            identifiers when attempting to access their corresponding plugin through
            the framework.
        name:
            A human-readable name for the plugin. This name **must be unique** across
            all plugins that are loaded into the framework and cannot be an empty
            string. Plugin names are used as primary identifiers in specifying
            dependencies can also be used to access the plugin.
        description:
            A description of the plugin.
        plugin_version:
            The version of the plugin. This version is a `packaging.version.Version`
            object that represents a version string. The version string must be a valid
            version string according to the `PEP 440` specification.
        compatible_framework_version:
            A specifier string that specifies the compatible framework version for the
            plugin. The specifier string must be a valid specifier string according to
            the `PEP 440` specification.
        authors:
            The author(s) that wrote the plugin.
        autostart:
            Whether to automatically run the plugin after the plugin service has loaded
            it successfully.
        plugin_dependencies:
            The set of plugins that this plugin depends on. The plugin dependencies are
            a set of plugin `names` that this plugin depends on. These plugins will all
            be loaded ahead of the plugin that depends on them.
        third_party_dependencies:
            The set of third-party library dependencies that this plugin depends on.
            This plugin will not load if the plugin service cannot import these
            third-party libraries.
        status:
            The status of the plugin. This contains the plugin's current state as a
            [`PluginState`][plugin_status.PluginState] string enum as well as the
            relevant exception if it happens to be in an `ERRORED` or `FATAL` state.
    """

    name: str
    description: str = ""
    plugin_version: str = ""
    compatible_framework_version: str = ""
    authors: set[str] | None = None
    autostart: bool = True
    plugin_dependencies: set[str] | None = None
    third_party_dependencies: set[str] | None = None

    def __init__(self):
        self.plugin_id = uuid.uuid4()

        # The plugin status `state` attribute is set to
        # `plugin_status.PluginState.INITIALIZED` at instantiation.
        self.status = plugin_status.PluginStatus()
        # self.environment is used to store any information that the plugin may need
        # to store and share amongst its user defined methods.
        self.environment = types.SimpleNamespace()
        # self.stop_plugin_event used to signal to the plugin runtime loop to exit.
        # The implementation of the plugin runtime loop should check this event
        # periodically and exit if it is set.
        self.stop_plugin_event = asyncio.Event()
        # Dynamically construct the `server_services` simple namespace object by
        # iterating over the attributes of the `server_singletons` module and adding
        # any object with an attribute that ends with `_service`.
        services_dict = {}
        for attr in dir(server_singletons):
            if attr.endswith("_service"):
                services_dict[attr] = getattr(server_singletons, attr)
        self.server_services = types.SimpleNamespace(**services_dict)
        self.plugin_logger = loguru.logger.bind(
            logger_name=f"Plugin {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        self.plugin_project_folder_path = pathlib.Path(
            sys.modules[self.__module__].__file__,
        ).parents[0]

        self._plugin_task = None

    def __init_subclass__(cls, **kwargs):
        if cls.authors is None:
            cls.authors = set()
        if cls.plugin_dependencies is None:
            cls.plugin_dependencies = set()
        if cls.third_party_dependencies is None:
            cls.third_party_dependencies = set()

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
            raise InvalidPluginConfigurationParameterTypeError(
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
            raise InvalidPluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(cls.plugin_version, str):
            raise InvalidPluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="plugin_version",
                parameter_type="str",
            )
        try:
            cls.plugin_version: version.Version = version.Version(cls.plugin_version)
        except version.InvalidVersion:
            raise InvalidPluginVersionError(
                plugin_version_str=cls.plugin_version, plugin_str=cls.name
            )
        if not isinstance(cls.compatible_framework_version, str):
            raise InvalidPluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="framework_version",
                parameter_type="str",
            )
        try:
            cls.compatible_framework_version: specifiers.SpecifierSet = specifiers.SpecifierSet(
                cls.compatible_framework_version
            )
        except specifiers.InvalidSpecifier:
            raise InvalidFrameworkVersionSpecifierError(
                framework_version_specifier_str=cls.compatible_framework_version, plugin_str=cls.name
            )
        if not isinstance(cls.authors, set):
            raise InvalidPluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="authors",
                parameter_type="set",
            )
        for author in cls.authors:
            if not isinstance(author, str):
                raise InvalidPluginConfigurationParameterTypeError(
                    plugin_str=cls.name,
                    error_message=(
                        "The elements in the authors set must be strings for plugin "
                        f"'{cls.name}'."
                    ),
                )
        if not isinstance(cls.autostart, bool):
            raise InvalidPluginConfigurationParameterTypeError(
                plugin_str=cls.name,
                parameter_name="autostart",
                parameter_type="bool",
            )

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({str(self.plugin_id)})"

    def __repr__(self) -> str:
        return "Plugin()"

    async def on_plugin_started(self) -> None: ...

    async def on_plugin_running(self) -> None: ...

    async def on_plugin_stopped(self) -> None: ...

    async def on_plugin_cancelled(self) -> None: ...

    async def on_plugin_errored(self, exc: Exception) -> None: ...

    async def start_plugin(self, autostart: bool = False) -> None:
        if self.status.state == plugin_status.PluginState.STARTED:
            raise PluginAlreadyRunningError(
                plugin_str=str(self),
                error_message=(
                    "The plugin cannot be started because it is already running"
                ),
            )

        # Clear the signal to the plugin to stop running if it is set, so it won't
        # instantly stop.
        self.stop_plugin_event.clear()

        # The plugin is now started.
        self.status._transition_to_started()
        try:
            await self.on_plugin_started()
        # PluginStartError is raised within on_plugin_started() to abort the
        # plugin start process if preconditions are not met.
        except PluginStartError as exc:
            # The plugin is now initialized.
            self.status._transition_to_initialized()
            if not autostart:
                # If the plugin was not automatically started, it was started through
                # the REST API. An automatically started plugin has no client to return
                # any error response to.
                raise PluginStartFrameworkError(
                    plugin_str=str(self),
                    start_error_message=exc.message,
                    detail=exc.detail,
                )
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored.
            self.status._transition_to_fatal(
                plugin_str=str(self),
                exception=exc,
            )
            raise exc

        self._plugin_task = asyncio.create_task(self._run_plugin())

    async def stop_plugin(self) -> None:
        if self.status.state != plugin_status.PluginState.RUNNING:
            raise PluginNotRunningError(
                plugin_str=str(self),
                error_message="The plugin cannot be stopped because it is not running.",
            )

        try:
            await self.on_plugin_stopped()
        # PluginStopError is raised within on_plugin_stopped() to abort the
        # plugin stop process if preconditions are not met.
        except PluginStopError as exc:
            # The plugin has not changed from its running state.
            self.status._transition_to_running()
            raise PluginStopFrameworkError(
                plugin_str=str(self),
                stop_error_message=exc.message,
                detail=exc.detail,
            )
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            # The plugin is now fatally errored.
            self.status._transition_to_fatal(
                plugin_str=str(self),
                exception=exc,
            )
            raise exc

        # Signal to the plugin to stop running.
        self.stop_plugin_event.set()

    async def cancel_plugin(self) -> None:
        if self.status.state != plugin_status.PluginState.RUNNING:
            raise PluginNotRunningError(
                plugin_str=str(self),
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
            self.status._transition_to_fatal(
                plugin_str=str(self),
                exception=exc,
            )
            raise exc

    def to_json(self) -> dict[str, str]:
        return {
            "plugin_id": str(self.plugin_id),
            "name": self.name,
            "description": self.description,
            "plugin_version": str(self.plugin_version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": self.authors,
            "autostart": self.autostart,
            "plugin_dependencies": list(map(str, self.plugin_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "status": self.status.to_json(),
        }

    async def _run_plugin(self):
        try:
            try:
                # The plugin is now running.
                self.status._transition_to_running()
                await self.on_plugin_running()

                # The plugin is now stopped.
                self.status._transition_to_stopped()
                self._plugin_task = None
            except asyncio.CancelledError:
                # The plugin is now cancelled.
                self.status._transition_to_cancelled()
            except PluginRuntimeError as exc:
                exc = PluginRuntimeFrameworkError(
                    plugin_str=str(self),
                    runtime_error_message=exc.message,
                    detail=exc.detail,
                )
                # The plugin is now errored.
                self.status._transition_to_errored(exc)
                try:
                    await self.on_plugin_errored(exc)
                except Exception as exc:
                    self.plugin_logger.opt(ansi=True).error(
                        "<bold><red>{}</></>",
                        traceback.format_exc(),
                    )
                    # The plugin is now fatally errored.
                    self.status._transition_to_fatal(
                        plugin_str=str(self),
                        exception=exc,
                    )
        except Exception as exc:
            self.plugin_logger.opt(ansi=True).error(
                "<bold><red>{}</></>",
                traceback.format_exc(),
            )
            self.status._transition_to_fatal(
                plugin_str=str(self),
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
                self.status._transition_to_fatal(
                    plugin_str=str(self),
                    exception=exc,
                )
