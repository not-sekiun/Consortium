import pathlib
import traceback
import types
import uuid

import loguru
from pydantic import JsonValue

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.components import (
    ComponentLifeCycle,
    ComponentLifeCycleExceptions,
    ComponentLifeCycleFatalContext,
    ComponentMetadata,
    ComponentMetadataExceptions,
    ComponentMetadataModel,
)
from consortium.framework._core.event_logging.event_log import EventLog
from consortium.framework._core.event_logging.event_logger import EventLogger
from consortium.framework._core.framework_exceptions.plugins_framework_exceptions import (
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
from consortium.framework._core.utils import resolve_component_filepath
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import construct_services_dataclass


class _PluginMetadataModel(ComponentMetadataModel):
    autostart: bool = True


class BasePlugin(ComponentMetadata, ComponentLifeCycle):
    """Base class for implementing custom server plugins in the Consortium framework.

    Plugins run as long-lived background components alongside the server, performing
    tasks such as integrating with external services, scheduling work, or augmenting
    server behavior. All custom plugins must inherit from this class and implement
    the required lifecycle hook methods.

    Attributes:
        plugin_id: Unique framework-wide identifier for this plugin instance,
            generated as a UUID4.
        name: Human-readable name for identifying this plugin.
        description: Brief description of the plugin's purpose and functionality.
        version: Version of this plugin, specified as a PEP 440 version string.
        compatible_framework_version: Framework version specifier defining which
            versions of Consortium this plugin is compatible with.
        authors: Set of authors associated with this plugin.
        component_dependencies: Version-pinned dependencies on other framework
            components, defined using PEP 440 specifiers.
        third_party_dependencies: Third-party library dependencies required for this
            plugin to function.
        autostart: Whether the framework should start this plugin automatically on
            server startup. Defaults to True.
        environment: Namespace for storing plugin-specific state shared across
            lifecycle hook calls without naming conflicts.
        logger: Plugin-specific logger instance, automatically tagged with the
            plugin's name and ID for easy identification in logs.
        event_logger: Plugin-specific event logger used to record structured,
            client-facing lifecycle events (successes, failures, informational
            messages, progress updates). Entries are optionally mirrored to the
            plugin's system logger.
    """

    _component_metadata_model = _PluginMetadataModel
    # Raise plugin framework exceptions directly from the shared metadata validation instead
    # of raising generic component exceptions and remapping them in __init_subclass__.
    _component_metadata_exceptions = ComponentMetadataExceptions(
        missing_configuration_parameter=MissingPluginConfigurationParameterError,
        invalid_configuration_parameter_type=InvalidPluginConfigurationParameterTypeError,
        empty_label=EmptyPluginLabelError,
        invalid_version=InvalidPluginVersionError,
        invalid_framework_version_specifier=InvalidFrameworkVersionSpecifierError,
        invalid_dependency_version_specifier=InvalidPluginDependencyVersionSpecifierError,
    )
    # Raise plugin errors directly from the shared lifecycle instead of raising generic
    # component errors and remapping them here, which would format the message twice.
    _component_life_cycle_exceptions = ComponentLifeCycleExceptions(
        start=PluginStartError,
        stop=PluginStopError,
        runtime=PluginRuntimeError,
        not_running=PluginNotRunningError,
        already_running=PluginAlreadyRunningError,
    )

    autostart: bool = True

    def __init__(self) -> None:
        self.plugin_id: uuid.UUID = uuid.uuid4()
        self.environment: types.SimpleNamespace = types.SimpleNamespace()
        self.logger: loguru.Logger = loguru.logger.bind(
            logger_name=f"Plugin - {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        self.event_logger: EventLogger = EventLogger(
            event_log=EventLog(subject_id=self.plugin_id),
            system_logger=self.logger,
        )
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.root_directory = pathlib.Path(
            resolve_component_filepath(cls),
        ).parents[0]
        cls.services = construct_services_dataclass(server_singletons=server_singletons)

        cls._validate_metadata()

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
        instead of the default behaviour of recording the error as a failure event.

        Args:
            error: The runtime error describing what went wrong during plugin
                execution, including the error message and any diagnostic detail.
        """
        # Recording through the event logger both surfaces the failure in the
        # client-facing event log and mirrors it to the plugin's system logger.
        self.event_logger.failure(str(error))

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

    # start(), stop() and cancel() below add no behaviour and exist purely to carry their
    # documentation. The documentation generator infers docstrings statically and does not
    # follow the MRO, so the plugin specific `Raises:` entries have to be physically
    # present on this class to be published.
    #
    # Do NOT reintroduce a try/except here to convert component errors into plugin errors.
    # The lifecycle already raises the plugin errors directly via
    # `_component_life_cycle_exceptions`; catching and re-raising would pass an already
    # formatted message back through a second template and nest the prefix.

    async def start(self) -> None:
        """Start the plugin and begin executing its main loop.

        Raises:
            PluginAlreadyRunningError: If the plugin is already in a running state.
            PluginStartError: If the plugin fails to start due to a lifecycle error.
        """
        await super().start()

    async def stop(self) -> None:
        """Stop the plugin and exit its main loop.

        Raises:
            PluginNotRunningError: If the plugin is not currently running.
            PluginStopError: If the plugin fails to stop cleanly.
        """
        await super().stop()

    async def cancel(self) -> None:
        """Cancel the plugin run immediately.

        Raises:
            PluginNotRunningError: If the plugin is not currently running.
        """
        await super().cancel()

    def to_json(
        self, limit: int = 10, offset: int | None = None
    ) -> dict[str, JsonValue]:
        """Serialize the plugin's metadata and current state to a JSON-compatible dictionary.

        Args:
            limit: Maximum number of event log entries to include.
            offset: Sequence offset to start the event log window from. If None, the
                tail (most recent entries up to limit) is returned.

        Returns:
            A dictionary containing the plugin ID, label, name, description, version,
            framework compatibility, authors, dependencies, autostart flag, status, and
            event log.
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
            "event_log": self.event_logger.to_json(limit=limit, offset=offset),
        }

    def to_json_reference(self) -> dict[str, JsonValue]:
        """Serialize a compact reference to this plugin.

        Returns:
            A dictionary containing only the plugin ID, label, and name, suitable
            for embedding as a lightweight foreign key reference in other JSON objects.
        """
        return {
            "plugin_id": str(self.plugin_id),
            "label": self.label,
            # `name` is declared optional so component authors can omit it, and metadata
            # validation falls it back to the label when it was not declared.
            "name": self.name or self.label,
        }
