from consortium.framework.event_hooks import BaseEventHook

from .declarations import (
    DECLARED_AUTHORS,
    DECLARED_DEPENDENCY,
    DECLARED_DESCRIPTION,
    DECLARED_FRAMEWORK_VERSION,
    DECLARED_VERSION,
)

DECLARED_EVENT_TYPE = "START_SERVER"


class MockEventHook(BaseEventHook):
    label = "consortium.event_hooks.mock_metadata"
    name = "Mock Metadata Event Hook"
    description = DECLARED_DESCRIPTION
    version = DECLARED_VERSION
    compatible_framework_version = DECLARED_FRAMEWORK_VERSION
    authors = set(DECLARED_AUTHORS)
    component_dependencies = {DECLARED_DEPENDENCY}
    event_types = {DECLARED_EVENT_TYPE}
