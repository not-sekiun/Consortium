import pathlib
import sys
import traceback
import types
import uuid
from typing import Any

import loguru

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
import consortium.server.server_singletons as server_singletons
from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
    ComponentMetadata,
    ComponentMetadataModel,
)
from consortium.framework.utils.exception_utils import remap_exception
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyRunningError,
    ComponentNotRunningError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
    EmptyPluginLabelError,
    InvalidFrameworkVersionSpecifierError,
    InvalidPluginConfigurationParameterTypeError,
    InvalidPluginDependencyVersionSpecifierError,
    InvalidPluginVersionError,
    MissingPluginConfigurationParameterError,
    PluginAlreadyRunningError,
    PluginNotRunningError,
    PluginStartError,
    PluginStopError,
)
from consortium.server.server_logging import LoggerType


class _PluginModel(ComponentMetadataModel):
    autostart: bool = True


class BasePlugin(ComponentMetadata, ComponentLifeCycle):
    _METADATA_MODEL = _PluginModel
    _EXCEPTION_MAP = {
        comp_excs.MissingComponentConfigurationParameterError: MissingPluginConfigurationParameterError,
        comp_excs.EmptyComponentLabelError: EmptyPluginLabelError,
        comp_excs.InvalidComponentVersionError: InvalidPluginVersionError,
        comp_excs.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        comp_excs.InvalidComponentDependencyVersionSpecifierError: InvalidPluginDependencyVersionSpecifierError,
        comp_excs.InvalidComponentConfigurationParameterTypeError: InvalidPluginConfigurationParameterTypeError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_str": "plugin_str",
        "component_filepath": "plugin_filepath",
    }

    autostart: bool = True

    def __init__(self):
        self.plugin_id = uuid.uuid4()
        self.environment = types.SimpleNamespace()
        self.server_services = types.SimpleNamespace(
            **{
                attr: getattr(server_singletons, attr)
                for attr in dir(server_singletons)
                if attr.endswith("_service")
            },
        )
        self.logger = loguru.logger.bind(
            logger_name=f"Plugin - {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.plugin_project_folder = pathlib.Path(
            sys.modules[cls.__module__].__file__,
        ).parents[0]
        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=cls._EXCEPTION_MAP,
                exception_kwargs_map=cls._EXCEPTION_KWARGS_MAP,
            ) from None
        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.plugin_id})"

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

    async def on_errored(self, error: BaseFrameworkException) -> None:
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
        self.logger.opt(ansi=True).error(
            "<bold><red>Fatal error occurred within plugin while it was {}:</></>\n{}",
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        try:
            await super().start()
        except ComponentAlreadyRunningError:
            raise PluginAlreadyRunningError(
                plugin_str=str(self),
            ) from None
        except ComponentStartError as exc:
            raise PluginStartError(
                plugin_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def stop(self) -> None:
        try:
            await super().stop()
        except ComponentNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            ) from None
        except ComponentStopError as exc:
            raise PluginStopError(
                plugin_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None

    async def cancel(self) -> None:
        try:
            await super().cancel()
        except ComponentNotRunningError:
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
