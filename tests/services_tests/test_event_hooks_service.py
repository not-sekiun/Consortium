import pathlib
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from consortium.server.services.event_hooks_service import EventHooksService
from consortium.server.services.events_service import EventsService
from consortium.server.services.release_service import ReleaseService
from tests.services_tests.mocks.paths_service import make_mock_paths_service

_HERE = pathlib.Path(__file__).parent
_MOCK_EVENT_HOOKS = _HERE / "mocks" / "event_hooks"
_CONSORTIUM_ROOT = _HERE.parent.parent
_RELEASE_JSON = _CONSORTIUM_ROOT / "data" / "release.json"


@pytest.fixture(scope="module")
def release_service():
    return ReleaseService(release_json_file=_RELEASE_JSON)


@pytest.fixture(scope="module")
def events_service():
    return EventsService()


@pytest.fixture(scope="module")
def event_hooks_service(release_service, events_service):
    return EventHooksService(
        events_service=events_service,
        release_service=release_service,
        paths_service=make_mock_paths_service(
            event_hooks_directory=_MOCK_EVENT_HOOKS,
            consortium_root=_CONSORTIUM_ROOT,
        ),
    )


@pytest.fixture
def svc_with_mock_registry(release_service, events_service):
    svc = EventHooksService(
        events_service=events_service,
        release_service=release_service,
        paths_service=make_mock_paths_service(
            event_hooks_directory=_MOCK_EVENT_HOOKS,
            consortium_root=_CONSORTIUM_ROOT,
        ),
    )
    mock_registry = MagicMock()
    mock_registry.get_all_components.return_value = []
    svc._event_hook_registry_service = mock_registry
    return svc, mock_registry


# --- __str__ / __repr__ ---


def test_str(event_hooks_service):
    assert str(event_hooks_service) == "Event Hooks Service"


def test_repr(event_hooks_service):
    assert repr(event_hooks_service) == "EventHooksService()"


# --- get_event_hook_from_directory ---


def test_get_event_hook_from_folder_enabled(event_hooks_service):
    hook = event_hooks_service.get_event_hook_from_directory(
        directory=_MOCK_EVENT_HOOKS / "mock_event_hook_valid"
    )
    assert hook is not None
    assert hook.label == "consortium.tests.services.mock_event_hook_valid"


def test_get_event_hook_from_folder_disabled_returns_none(event_hooks_service):
    result = event_hooks_service.get_event_hook_from_directory(
        directory=_MOCK_EVENT_HOOKS / "mock_event_hook_disabled"
    )
    assert result is None


def test_get_event_hook_from_folder_disabled_with_flag(event_hooks_service):
    result = event_hooks_service.get_event_hook_from_directory(
        directory=_MOCK_EVENT_HOOKS / "mock_event_hook_disabled",
        ignore_enabled_flag=True,
    )
    assert result is not None


# --- get_event_hooks_from_directories ---


def test_get_event_hooks_from_directories(event_hooks_service):
    retrieved, skipped, errored = (
        event_hooks_service.get_all_event_hooks_from_directory(
            directory=_MOCK_EVENT_HOOKS
        )
    )
    assert isinstance(retrieved, list)
    assert isinstance(skipped, list)
    assert isinstance(errored, list)


# --- register_event_hook ---


def test_register_event_hook_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_hook = MagicMock()
    svc.register_event_hook(event_hook=mock_hook)
    registry.register_component.assert_called_once_with(component=mock_hook)


# --- register_event_hook_from_folder ---


def test_register_event_hook_from_folder_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    folder = pathlib.Path("/tmp/some_hook")
    mock_hook = MagicMock()
    registry.register_component_from_directory.return_value = mock_hook
    result = svc.register_event_hook_from_directory(directory=folder)
    registry.register_component_from_directory.assert_called_once_with(
        directory=folder,
        ignore_enabled_component_flag=False,
    )
    assert result == mock_hook


def test_register_event_hook_from_folder_disabled_returns_none(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    folder = pathlib.Path("/tmp/disabled_hook")
    registry.register_component_from_directory.return_value = None
    result = svc.register_event_hook_from_directory(directory=folder)
    assert result is None


# --- load_event_hook ---


@pytest.mark.anyio
async def test_load_event_hook_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_hook = MagicMock()
    registry.load_component = AsyncMock(return_value=mock_hook)
    result = await svc.load_event_hook(event_hook=mock_hook)
    registry.load_component.assert_called_once_with(component=mock_hook)
    assert result == mock_hook


# --- load_event_hook_from_folder ---


@pytest.mark.anyio
async def test_load_event_hook_from_folder_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    folder = pathlib.Path("/tmp/some_hook")
    mock_hook = MagicMock()
    registry.load_component_from_directory = AsyncMock(return_value=mock_hook)
    result = await svc.load_event_hook_from_directory(directory=folder)
    registry.load_component_from_directory.assert_called_once_with(
        directory=folder,
        ignore_enabled_component_flag=False,
    )
    assert result == mock_hook


@pytest.mark.anyio
async def test_load_event_hook_from_folder_disabled_returns_none(
    svc_with_mock_registry,
):
    svc, registry = svc_with_mock_registry
    registry.load_component_from_directory = AsyncMock(return_value=None)
    result = await svc.load_event_hook_from_directory(
        directory=pathlib.Path("/tmp/disabled")
    )
    assert result is None


# --- unload_event_hook_by_event_hook_id ---


@pytest.mark.anyio
async def test_unload_event_hook_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    hook_id = uuid.uuid4()
    registry.unload_component_by_component_id = AsyncMock(return_value=None)
    await svc.unload_event_hook_by_event_hook_id(event_hook_id=hook_id)
    registry.unload_component_by_component_id.assert_called_once_with(
        component_id=hook_id,
    )


# --- reload_event_hook_by_event_hook_id ---


@pytest.mark.anyio
async def test_reload_event_hook_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    hook_id = uuid.uuid4()
    mock_hook = MagicMock()
    registry.reload_component_by_component_id = AsyncMock(return_value=mock_hook)
    result = await svc.reload_event_hook_by_event_hook_id(event_hook_id=hook_id)
    registry.reload_component_by_component_id.assert_called_once_with(
        component_id=hook_id,
        ignore_enabled_component_flag=False,
    )
    assert result == mock_hook


@pytest.mark.anyio
async def test_reload_event_hook_disabled_returns_none(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    hook_id = uuid.uuid4()
    registry.reload_component_by_component_id = AsyncMock(return_value=None)
    result = await svc.reload_event_hook_by_event_hook_id(event_hook_id=hook_id)
    assert result is None


# --- get_event_hook_by_event_hook_id ---


def test_get_event_hook_by_id_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_hook = MagicMock()
    hook_id = uuid.uuid4()
    registry.get_component_by_component_id.return_value = mock_hook
    result = svc.get_event_hook_by_event_hook_id(event_hook_id=hook_id)
    registry.get_component_by_component_id.assert_called_once_with(component_id=hook_id)
    assert result == mock_hook


# --- get_all_event_hooks ---


def test_get_all_event_hooks_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_hooks = [MagicMock(), MagicMock()]
    registry.get_all_components.return_value = mock_hooks
    result = svc.get_all_event_hooks()
    assert result == mock_hooks


# --- load_framework_event_hooks ---


@pytest.mark.anyio
async def test_load_framework_event_hooks_registers_and_loads(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_hook = MagicMock()
    svc.get_all_event_hooks_from_directory = MagicMock(
        return_value=([mock_hook], [], [])
    )
    svc.load_event_hook = AsyncMock(return_value=mock_hook)
    await svc.load_framework_event_hooks()
    svc.load_event_hook.assert_called_once_with(event_hook=mock_hook)
