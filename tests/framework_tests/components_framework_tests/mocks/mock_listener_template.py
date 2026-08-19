from consortium.framework.listeners import (
    BaseListener,
    BaseListenerTemplate,
    BaseListenerType,
)

from .declarations import (
    DECLARED_AUTHORS,
    DECLARED_DEPENDENCY,
    DECLARED_DESCRIPTION,
    DECLARED_FRAMEWORK_VERSION,
    DECLARED_VERSION,
    declared_options,
    declared_validating_function,
)

DECLARED_LISTENER_TYPE_NAME = "mock_metadata_listener_type"


class MockListener(BaseListener):
    async def on_started(self) -> None: ...

    async def on_running(self) -> None:
        await self.stop_event.wait()

    async def on_stopped(self) -> None: ...

    async def on_cancelled(self) -> None: ...


class MockListenerType(BaseListenerType):
    name = DECLARED_LISTENER_TYPE_NAME


class MockListenerTemplate(BaseListenerTemplate):
    label = "consortium.listeners.mock_metadata"
    name = "Mock Metadata Listener Template"
    description = DECLARED_DESCRIPTION
    version = DECLARED_VERSION
    compatible_framework_version = DECLARED_FRAMEWORK_VERSION
    authors = set(DECLARED_AUTHORS)
    component_dependencies = {DECLARED_DEPENDENCY}
    listener = MockListener
    listener_type = MockListenerType
    options = declared_options()
    validating_function = declared_validating_function

    def resolve_listener_endpoint(self, parameters):
        return "mock://localhost"
