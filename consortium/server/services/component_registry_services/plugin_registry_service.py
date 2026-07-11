import asyncio
import pathlib
import uuid

from consortium.framework._core.components.component_status import State
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.service_exceptions import (
    components_service_exceptions as comp_excs,
)
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
    InvalidPluginProjectPyProjectFileTOMLError,
    PluginAlreadyRegisteredError,
    PluginDependsOnInvalidComponentDependencyError,
    PluginLoadingError,
    PluginNotFoundError,
    PluginProjectEntryPointModuleNotFoundError,
    PluginProjectInterfaceError,
    PluginProjectManifestFileNotFoundError,
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
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP = {
        comp_excs.ComponentProjectManifestFileNotFoundError: PluginProjectManifestFileNotFoundError,
        comp_excs.InvalidComponentProjectManifestFileJSONError: InvalidPluginProjectManifestFileJSONError,
        comp_excs.InvalidComponentProjectManifestFileSchemaError: InvalidPluginProjectManifestFileSchemaError,
        comp_excs.InvalidComponentProjectPyProjectFileError: InvalidPluginProjectPyProjectFileError,
        comp_excs.InvalidComponentProjectPyProjectFileTOMLError: InvalidPluginProjectPyProjectFileTOMLError,
        comp_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidPluginProjectPyProjectFileDependencyError,
        comp_excs.ComponentProjectEntryPointModuleNotFoundError: PluginProjectEntryPointModuleNotFoundError,
        comp_excs.ComponentProjectSymbolNotFoundError: PluginProjectSymbolNotFoundError,
        comp_excs.ComponentProjectInterfaceError: PluginProjectInterfaceError,
        comp_excs.IncompatibleComponentFrameworkVersionError: IncompatiblePluginFrameworkVersionError,
        comp_excs.InternalComponentProjectError: InternalPluginProjectError,
        comp_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_excs.ComponentDependsOnInvalidComponentDependencyError: PluginDependsOnInvalidComponentDependencyError,
        comp_excs.ComponentNotFoundError: PluginNotFoundError,
        comp_excs.ComponentAlreadyRegisteredError: PluginAlreadyRegisteredError,
        comp_excs.DuplicateComponentLabelError: DuplicatePluginLabelError,
    }
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "plugin_project_folder",
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
                f"second(s)",
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
