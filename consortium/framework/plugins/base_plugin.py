import pathlib
import sys
import traceback
import types
import uuid
from typing import Any

import loguru

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
from consortium.server.utils import construct_services_namespace_object


class _PluginModel(ComponentMetadataModel):
    autostart: bool = True


class BasePlugin(ComponentMetadata, ComponentLifeCycle):
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
        cls.services = construct_services_namespace_object(
            server_singletons=server_singletons
        )

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

    async def on_started(self) -> None: ...

    async def on_running(self) -> None: ...

    async def on_stopped(self) -> None: ...

    async def on_completed(self) -> None: ...

    async def on_cancelled(self) -> None: ...

    async def on_errored(self, error: PluginRuntimeError) -> None:
        self.logger.error(error)

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
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
        try:
            await super().cancel()
        except comp_excs.ComponentNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            ) from None

    def to_json(self) -> dict[str, Any]:
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
