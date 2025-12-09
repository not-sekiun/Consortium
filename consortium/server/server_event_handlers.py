from contextlib import asynccontextmanager

from fastapi import FastAPI

import consortium.server.server_singletons as server_singletons

# from consortium.framework.plugins._plugin_status import PluginState
from consortium.framework._components._component_status import State
from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType


@asynccontextmanager
async def lifespan(_: FastAPI) -> None:
    # Startup events occur before the yield.
    server_singletons.user_accounts_service.load_framework_user_accounts()
    await server_singletons.listener_profiles_service.load_framework_listener_profiles()
    await server_singletons.agent_profiles_service.load_framework_agent_profiles()
    await server_singletons.event_hooks_service.load_framework_event_hooks()
    # When the FastAPI server starts up we want to load all framework plugins from the
    # server framework's plugins folder that contains all the plugin project folders.
    # Order of startup events matters. We need to load all framework plugins before we
    # autostart any plugins. We can't do this in the __init__ function of the plugins
    # service because the FastAPI server instance is not available at that time and
    # __init__ cannot be asynchronous.
    await server_singletons.plugins_service.load_framework_plugins()
    await server_singletons.events_service.trigger_event(
        event=Event(event_type=EventType.START_SERVER),
    )
    yield
    # Shutdown events occur after the yield.
    await server_singletons.events_service.trigger_event(
        event=Event(event_type=EventType.STOP_SERVER),
    )
    for plugin in server_singletons.plugins_service.get_all_plugins():
        if plugin.status.state == State.RUNNING:
            await server_singletons.plugins_service.stop_plugin_by_plugin_id(
                plugin_id=str(plugin.plugin_id),
                blocking=True,
            )
