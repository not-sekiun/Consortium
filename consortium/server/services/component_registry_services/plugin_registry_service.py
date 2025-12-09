import asyncio
import pathlib
import uuid

import consortium.server.exceptions.service_exceptions.component_service_exceptions as comp_ldr_svc_excs
from consortium.framework._components._component_status import State
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    DuplicatePluginLabelError,
    IncompatibleComponentDependencyVersionError,
    IncompatiblePluginFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalPluginProjectError,
    InvalidPluginProjectManifestFileJSONError,
    InvalidPluginProjectManifestFileSchemaError,
    InvalidPluginProjectPyProjectFileDependencyError,
    InvalidPluginProjectPyProjectFileError,
    PluginAlreadyRegisteredError,
    PluginDependsOnInvalidComponentDependencyError,
    PluginLoadingError,
    PluginNotFoundError,
    PluginProjectInterfaceError,
    PluginProjectManifestFileNotFoundError,
    PluginProjectPluginFileNotFoundError,
    PluginProjectSymbolNotFoundError,
    PluginStopTimeoutError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.services.component_registry_services.exception_remapping_component_registry_service import (
    ExceptionRemappingComponentRegistryService,
)


class PluginRegistryService(
    ExceptionRemappingComponentRegistryService[BasePlugin, PluginLoadingError],
):
    _EXCEPTION_MAP = {
        comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError: PluginProjectManifestFileNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError: InvalidPluginProjectManifestFileJSONError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError: InvalidPluginProjectManifestFileSchemaError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError: InvalidPluginProjectPyProjectFileError,
        comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidPluginProjectPyProjectFileDependencyError,
        comp_ldr_svc_excs.ComponentProjectComponentFileNotFoundError: PluginProjectPluginFileNotFoundError,
        comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError: PluginProjectSymbolNotFoundError,
        comp_ldr_svc_excs.ComponentProjectInterfaceError: PluginProjectInterfaceError,
        comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError: IncompatiblePluginFrameworkVersionError,
        comp_ldr_svc_excs.InternalComponentProjectError: InternalPluginProjectError,
        comp_ldr_svc_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_ldr_svc_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError: PluginDependsOnInvalidComponentDependencyError,
        comp_ldr_svc_excs.ComponentNotFoundError: PluginNotFoundError,
        comp_ldr_svc_excs.ComponentAlreadyRegisteredError: PluginAlreadyRegisteredError,
        comp_ldr_svc_excs.DuplicateComponentLabelError: DuplicatePluginLabelError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "plugin_project_folder",
        "component_file": "plugin_file",
        "component_symbol": "plugin_symbol",
        "component_str": "plugin_str",
        "component_id": "plugin_id",
    }

    def _get_component_id(self, component: BasePlugin) -> uuid.UUID:
        return component.plugin_id

    def _get_component_project_folder(self, component: BasePlugin) -> pathlib.Path:
        return component.plugin_project_folder

    async def _component_load_procedure(
        self,
        component: BasePlugin,
        context: dict,
    ) -> BasePlugin:
        timeout = context["timeout"]
        if component.autostart:
            await asyncio.wait_for(component.start(), timeout=timeout)
        return component

    async def _component_unload_procedure(
        self,
        component: BasePlugin,
        context: dict,
    ) -> BasePlugin:
        if component.status.state != State.RUNNING:
            return component

        timeout = context["timeout"]
        force_unload = context["force_unload"]
        logger = context["logger"]

        async def _wait_for_plugin_running_state_change() -> None:
            while component.status.state == State.RUNNING:
                await asyncio.sleep(1)

        async def _stop_plugin() -> None:
            try:
                await component.stop()
                # Ensure that the stop plugin event has been set before proceeding to
                # wait on the timeout.
                await component.stop_event.wait()
                await _wait_for_plugin_running_state_change()
            except asyncio.CancelledError:
                pass

        try:
            await asyncio.wait_for(_stop_plugin(), timeout=timeout)
        except TimeoutError:
            if not force_unload:
                raise PluginStopTimeoutError(plugin_str=str(component)) from None
            logger.warning(
                f"Forcing plugin cancellation for plugin {component} because "
                f"its timeout exceeded the specified duration: {timeout} "
                f"second(s).",
            )
            await component.cancel()
        except Exception as exc:
            if not force_unload:
                raise exc
            logger.error(
                f"An error occurred while stopping plugin {component}. "
                f"Forcing plugin cancellation. Error: {exc}",
            )
            await component.cancel()

        return component
