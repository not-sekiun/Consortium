from fastapi import FastAPI

import consortium.server.server_singletons as server_singletons
from consortium.server.objects.event_objects import Event, EventType

plugins_service = server_singletons.plugins_service
listener_profiles_service = server_singletons.listener_profiles_service
agent_profiles_service = server_singletons.agent_profiles_service
user_accounts_service = server_singletons.user_accounts_service
event_hooks_service = server_singletons.event_hooks_service


def register_server_event_handlers(app: FastAPI) -> None:
    @app.on_event("startup")
    def load_framework_user_accounts():
        user_accounts_service.load_framework_user_accounts()

    @app.on_event("startup")
    def load_framework_listener_profiles():
        listener_profiles_service.load_framework_listener_profiles()

    @app.on_event("startup")
    def load_framework_agent_profiles():
        agent_profiles_service.load_framework_agent_profiles()

    # When the FastAPI server starts up we want to load all framework plugins from the
    # server framework's plugins folder that contains all the plugin project folders.
    # Order of startup events matters. We need to load all framework plugins before we
    # autostart any plugins. We can't do this in the __init__ function of the plugins
    # service because the FastAPI server instance is not available at that time and
    # __init__ cannot be asynchronous.
    @app.on_event("startup")
    async def load_framework_plugins():
        await plugins_service.load_framework_plugins()

    @app.on_event("startup")
    def load_framework_event_hooks():
        event_hooks_service.load_framework_event_hooks()

    # Order matters here. Only after the event hooks have loaded can we trigger the
    # server startup event.
    @app.on_event("startup")
    def trigger_server_startup_event():
        event_hooks_service.trigger_event(
            Event(
                event_type=EventType.START_SERVER,
            ),
        )

    @app.on_event("shutdown")
    def trigger_server_shutdown_event():
        event_hooks_service.trigger_event(
            Event(
                event_type=EventType.STOP_SERVER,
            ),
        )
