from consortium.framework.plugins import BasePlugin

from .declarations import (
    DECLARED_AUTHORS,
    DECLARED_DEPENDENCY,
    DECLARED_DESCRIPTION,
    DECLARED_FRAMEWORK_VERSION,
    DECLARED_VERSION,
)

# Declared False rather than left to default, so the tests can tell a declared value apart
# from the class default.
DECLARED_AUTOSTART = False


class MockPlugin(BasePlugin):
    label = "consortium.plugins.mock_metadata"
    name = "Mock Metadata Plugin"
    description = DECLARED_DESCRIPTION
    version = DECLARED_VERSION
    compatible_framework_version = DECLARED_FRAMEWORK_VERSION
    authors = set(DECLARED_AUTHORS)
    component_dependencies = {DECLARED_DEPENDENCY}
    autostart = DECLARED_AUTOSTART

    async def on_started(self) -> None: ...

    async def on_running(self) -> None: ...

    async def on_stopped(self) -> None: ...

    async def on_cancelled(self) -> None: ...
