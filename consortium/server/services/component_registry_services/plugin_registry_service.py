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

        # `force_unload` means the plugin leaves the registry whatever happens, so the
        # forced cancellation must never be able to abort the unload it is meant to
        # guarantee. Two things can go wrong here and both used to escape:
        #
        # `cancel()` only accepts a RUNNING plugin, and by the time a stop has failed the
        # plugin usually is not one. A stop that timed out inside `on_stopped` leaves it
        # STOPPING and a stop that raised an unhandled exception leaves it FATAL; only a
        # signalled refusal rolls back to RUNNING. In the other two cases the plugin is
        # already off its runtime path, so there is nothing left to cancel and the guard
        # skips it rather than raising PluginNotRunningError.
        #
        # A cancellation that is attempted can still fail on its own terms, since a
        # plugin's `on_cancelled` hook can raise and take the plugin fatal. That is logged
        # and swallowed for the same reason: the unload still has to finish.
        async def _force_cancel_plugin() -> None:
            if component.status.state is not State.RUNNING:
                return
            try:
                await component.cancel()
            except Exception as exc:
                logger.opt(exception=exc).error(
                    f"Failed to cancel plugin {component} while forcing its unload. "
                    f"Unloading it regardless.",
                )

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
            await _force_cancel_plugin()
        except Exception as exc:
            if not force_unload:
                raise exc
            logger.error(
                f"An error occurred while stopping plugin {component}. "
                f"Forcing plugin cancellation. Error: {exc}",
            )
            await _force_cancel_plugin()

        return component
