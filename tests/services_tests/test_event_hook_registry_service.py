import pathlib
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    EventHookSetupError,
    EventHookTeardownError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoadingExceptions,
)
from consortium.server.services.component_registry_services.event_hook_registry_service import (
    EventHookRegistryService,
)


def _make_mock_loader():
    loader = MagicMock()
    loader.validate_component_component_dependencies.return_value = True
    loader.get_component_from_directory.return_value = None
    loader.get_all_components_from_directory.return_value = (
        [],
        [],
        [],
    )
    loader._component_exceptions = ComponentLoadingExceptions()
    return loader


def _make_event_hook(setup_raises=False, teardown_raises=False):
    hook = MagicMock()
    hook.event_hook_id = uuid.uuid4()
    hook.root_directory = pathlib.Path("/tmp/mock_event_hook")
    hook.label = "test.event_hook"
    hook.subscribed_event_types = frozenset({EventType.AGENT_REGISTERED})
    hook.component_dependencies = set()
    hook.__str__ = MagicMock(return_value="MockEventHook")

    if setup_raises:
        hook.on_setup = AsyncMock(side_effect=RuntimeError("setup failed"))
    else:
        hook.on_setup = AsyncMock()

    if teardown_raises:
        hook.on_teardown = AsyncMock(side_effect=RuntimeError("teardown failed"))
    else:
        hook.on_teardown = AsyncMock()

    hook.on_triggered = MagicMock()
    return hook


@pytest.fixture
def mock_events_service():
    svc = MagicMock()
    svc.register_event_handler_to_event_type = MagicMock()
    svc.deregister_event_handler_from_event_type = MagicMock()
    # Unloading deregisters what is actually registered rather than what the hook
    # declares, so this lookup has to return a real iterable.
    svc.get_event_types_from_registered_event_handler = MagicMock(
        return_value=[EventType.AGENT_REGISTERED],
    )
    return svc


@pytest.fixture
def registry(mock_events_service):
    return EventHookRegistryService(
        component_loader_service=_make_mock_loader(),
        component_framework_directory=pathlib.Path("/tmp"),
        events_service=mock_events_service,
    )


# --- Accessors ---


def test_get_component_id(registry):
    hook = _make_event_hook()
    assert registry._get_component_id(hook) == hook.event_hook_id


# --- _component_load_procedure ---


@pytest.mark.anyio
async def test_load_procedure_calls_setup_and_registers_handlers(
    registry, mock_events_service
):
    hook = _make_event_hook()
    result = await registry._component_load_procedure(hook, {})

    mock_events_service.register_event_handler_to_event_type.assert_called_once_with(
        event_type=EventType.AGENT_REGISTERED,
        event_handler=hook.on_triggered,
    )
    hook.on_setup.assert_called_once()
    assert result is hook


@pytest.mark.anyio
async def test_load_procedure_registers_event_types_subscribed_during_setup(
    registry, mock_events_service
):
    # A hook that resolves its subscriptions from configuration calls
    # subscribe_to_event_type during on_setup, which updates subscribed_event_types
    # before the registry reads it. Those additions must still be registered.
    hook = _make_event_hook()

    async def _on_setup():
        hook.subscribed_event_types = frozenset(
            {EventType.AGENT_REGISTERED, EventType.PAYLOAD_CREATED},
        )

    hook.on_setup = _on_setup
    await registry._component_load_procedure(hook, {})

    registered_event_types = {
        call.kwargs["event_type"]
        for call in mock_events_service.register_event_handler_to_event_type.call_args_list
    }
    assert registered_event_types == {
        EventType.AGENT_REGISTERED,
        EventType.PAYLOAD_CREATED,
    }


@pytest.mark.anyio
async def test_load_procedure_setup_error_raises_event_hook_setup_error(
    registry, mock_events_service
):
    hook = _make_event_hook(setup_raises=True)
    with pytest.raises(EventHookSetupError):
        await registry._component_load_procedure(hook, {})
    # Handlers are registered only after on_setup succeeds, so a failed setup must not
    # leave any behind.
    mock_events_service.register_event_handler_to_event_type.assert_not_called()


# --- _component_unload_procedure ---


@pytest.mark.anyio
async def test_unload_procedure_calls_teardown_and_deregisters(
    registry, mock_events_service
):
    hook = _make_event_hook()
    result = await registry._component_unload_procedure(hook, {})

    hook.on_teardown.assert_called_once()
    mock_events_service.deregister_event_handler_from_event_type.assert_called_once_with(
        event_type=EventType.AGENT_REGISTERED,
        event_handler=hook.on_triggered,
    )
    assert result is hook


@pytest.mark.anyio
async def test_unload_procedure_teardown_error_raises_event_hook_teardown_error(
    registry, mock_events_service
):
    hook = _make_event_hook(teardown_raises=True)
    with pytest.raises(EventHookTeardownError):
        await registry._component_unload_procedure(hook, {})
    # Handlers must NOT be deregistered when teardown fails.
    mock_events_service.deregister_event_handler_from_event_type.assert_not_called()
