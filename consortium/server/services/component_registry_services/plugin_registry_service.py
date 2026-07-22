import asyncio
import uuid

from consortium.framework._core.components.component_status import State
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    PluginLoadingError,
    PluginStopTimeoutError,
)
from consortium.server.services.component_registry_services.component_registry_service import (
    ComponentRegistryService,
)


# The plugin loader carries a plugin exception set, so loading and registry errors are
# raised as plugin types directly. This registry therefore extends the plain
# ComponentRegistryService rather than the exception remapping variant that the other
# domains still use.
class PluginRegistryService(
    ComponentRegistryService[BasePlugin, PluginLoadingError],
):
    def _get_component_id(self, component: BasePlugin) -> uuid.UUID:
        return component.plugin_id

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
