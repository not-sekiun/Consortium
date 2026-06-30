import pathlib
import sys
import traceback
import types
import uuid

import loguru
from pydantic.config import JsonValue

import consortium.server.server_singletons as server_singletons
from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
    ComponentMetadata,
    ComponentMetadataModel,
)
from consortium.framework._utils import remap_exception
from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions import (
    EmptyPluginLabelError,
    InvalidFrameworkVersionSpecifierError,
    InvalidPluginConfigurationParameterTypeError,
    InvalidPluginDependencyVersionSpecifierError,
    InvalidPluginVersionError,
    MissingPluginConfigurationParameterError,
    PluginAlreadyRunningError,
    PluginNotRunningError,
    PluginRuntimeError,
    PluginStartError,
    PluginStopError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import construct_services_dataclass


class _PluginModel(ComponentMetadataModel):
    autostart: bool = True


class BasePlugin(ComponentMetadata, ComponentLifeCycle):
    """Base class for implementing custom server plugins in the Consortium framework.

    Plugins run as long-lived background components alongside the server, performing
    tasks such as integrating with external services, scheduling work, or augmenting
    server behavior. All custom plugins must inherit from this class and implement
    the required lifecycle hook methods.

    Attributes:
        plugin_id (uuid.UUID): Unique framework-wide identifier for this plugin
            instance, generated as a UUID4.
        name (str): Human-readable name for identifying this plugin.
        description (str): Brief description of the plugin's purpose and functionality.
        version (Version): Version of this plugin, specified as a PEP 440 version string.
        compatible_framework_version (SpecifierSet): Framework version specifier defining
            which versions of Consortium this plugin is compatible with.
        authors (set[str]): Set of authors associated with this plugin.
        component_dependencies (set[str]): Version-pinned dependencies on other framework
            components, defined using PEP 440 specifiers.
        third_party_dependencies (set[str]): Third-party library dependencies required
            for this plugin to function.
        autostart (bool): Whether the framework should start this plugin automatically
            on server startup. Defaults to True.
        environment (SimpleNamespace): Namespace for storing plugin-specific state shared
            across lifecycle hook calls without naming conflicts.
        logger (loguru.Logger): Plugin-specific logger instance, automatically tagged
            with the plugin's name and ID for easy identification in logs.
    """

    _METADATA_MODEL = _PluginModel

    _COMPONENT_METADATA_EXCEPTION_MAP = {
        comp_excs.MissingComponentConfigurationParameterError: MissingPluginConfigurationParameterError,
        comp_excs.EmptyComponentLabelError: EmptyPluginLabelError,
        comp_excs.InvalidComponentVersionError: InvalidPluginVersionError,
        comp_excs.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        comp_excs.InvalidComponentDependencyVersionSpecifierError: InvalidPluginDependencyVersionSpecifierError,
        comp_excs.InvalidComponentConfigurationParameterTypeError: InvalidPluginConfigurationParameterTypeError,
    }
    _COMPONENT_METADATA_EXCEPTION_KWARGS_MAP = {
        "component_str": "plugin_str",
        "component_filepath": "plugin_filepath",
    }

    autostart: bool = True

    def __init__(self) -> None:
        self.plugin_id = uuid.uuid4()
        self.environment = types.SimpleNamespace()
        self.logger = loguru.logger.bind(
            logger_name=f"Plugin - {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.plugin_project_folder = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc._kwargs,
                exception_map=cls._COMPONENT_METADATA_EXCEPTION_MAP,
                exception_kwargs_map=cls._COMPONENT_METADATA_EXCEPTION_KWARGS_MAP,
            ) from None

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' ({self.plugin_id})"

    def __repr__(self) -> str:
        return (
            f"Plugin("
            f"plugin_id={self.plugin_id!r}, "
            f"label={self.label!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"version={self.version!r}, "
            f"compatible_framework_version={self.compatible_framework_version!r}, "
            f"authors={self.authors!r}, "
            f"component_dependencies={self.component_dependencies!r}, "
            f"third_party_dependencies={self.third_party_dependencies}"
            f"autostart={self.autostart!r}, "
            f")"
        )

    async def on_started(self) -> None:
        """Called once immediately after the plugin enters the running state."""
        ...

    async def on_running(self) -> None:
        """Called on each iteration of the plugin's main loop while running."""
        ...

    async def on_stopped(self) -> None:
        """Called once after the plugin has been successfully stopped."""
        ...

    async def on_completed(self) -> None:
        """Called when the plugin's main loop exits normally without being stopped."""
        ...

    async def on_cancelled(self) -> None:
        """Called once after the plugin run has been cancelled."""
        ...

    async def on_errored(self, error: PluginRuntimeError) -> None:
        """Called when a runtime error occurs during the plugin's execution.

        Override to add custom error handling or alerting logic in addition to or
        instead of the default error logging.

        Args:
            error: The runtime error describing what went wrong during plugin
                execution, including the error message and any diagnostic detail.
        """
        self.logger.error(error)

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        """Called when an unhandled exception causes the plugin to terminate fatally.

        Override to add custom alerting or cleanup logic when a fatal failure occurs.
        The default implementation logs the full traceback at error level.

        Args:
            exc: The unhandled exception that triggered the fatal shutdown.
            fatal_context: The lifecycle phase during which the fatal exception
                occurred (starting, running, stopping, cancelling, or error handling).
        """
        ctx_to_str_map = {
            ComponentLifeCycleFatalContext.START: "starting",
            ComponentLifeCycleFatalContext.RUNNING: "running",
            ComponentLifeCycleFatalContext.STOP: "stopping",
            ComponentLifeCycleFatalContext.CANCEL: "being cancelled",
            ComponentLifeCycleFatalContext.ERROR: "handling a runtime error",
        }
        self.logger.opt(colors=True).error(
            "<bold><red>Fatal error occurred within plugin {} while it was {}:</></>\n{}",
            str(self),
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        """Start the plugin and begin executing its main loop.

        Raises:
            PluginAlreadyRunningError: If the plugin is already in a running state.
            PluginStartError: If the plugin fails to start due to a lifecycle error.
        """
        try:
            await super().start()
        except comp_excs.ComponentAlreadyRunningError:
            raise PluginAlreadyRunningError(
                plugin_str=str(self),
            ) from None
        except comp_excs.ComponentStartError as exc:
            raise PluginStartError(
                plugin_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def stop(self) -> None:
        """Stop the plugin and exit its main loop.

        Raises:
            PluginNotRunningError: If the plugin is not currently running.
            PluginStopError: If the plugin fails to stop cleanly.
        """
        try:
            await super().stop()
        except comp_excs.ComponentNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            ) from None
        except comp_excs.ComponentStopError as exc:
            raise PluginStopError(
                plugin_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def cancel(self) -> None:
        """Cancel the plugin run immediately.

        Raises:
            PluginNotRunningError: If the plugin is not currently running.
        """
        try:
            await super().cancel()
        except comp_excs.ComponentNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            ) from None

    def to_json(self) -> dict[str, JsonValue]:
        """Serialize the plugin's metadata and current state to a JSON-compatible dictionary.

        Returns:
            A dictionary containing the plugin ID, label, name, description, version,
            framework compatibility, authors, dependencies, autostart flag, and status.
        """
        return {
            "plugin_id": str(self.plugin_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": list(self.authors),
            "component_dependencies": list(map(str, self.component_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "autostart": self.autostart,
            "status": self.status.to_json(),
        }

    def to_json_reference(self) -> dict[str, str]:
        """Serialize a compact reference to this plugin.

        Returns:
            A dictionary containing only the plugin ID, label, and name, suitable
            for embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "plugin_id": str(self.plugin_id),
            "label": self.label,
            "name": self.name,
        }

    def _construct_component_runtime_error_from_framework_runtime_error(
        self,
        error: comp_excs.ComponentRuntimeError,
    ) -> PluginRuntimeError:
        return PluginRuntimeError(
            plugin_str=str(self),
            error_message=error.message,
            detail=error.detail,
        )

    def _construct_component_runtime_error_from_unhandled_exception(
        self,
        exc: Exception,
    ) -> PluginRuntimeError:
        return PluginRuntimeError(
            plugin_str=str(self),
            error_message=(
                f"An unhandled exception was raised while running. "
                f"{type(exc).__name__}: {exc}"
            ),
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
