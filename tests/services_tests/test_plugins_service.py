import pathlib
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from consortium.server.services.plugins_service import PluginsService
from consortium.server.services.release_service import ReleaseService

_HERE = pathlib.Path(__file__).parent
_MOCK_PLUGINS = _HERE / "mock" / "plugins"
_CONSORTIUM_ROOT = _HERE.parent.parent
_RELEASE_JSON = _CONSORTIUM_ROOT / "data" / "release.json"


@pytest.fixture(scope="module")
def release_service():
    return ReleaseService(release_json_file=_RELEASE_JSON)


@pytest.fixture(scope="module")
def plugins_service(release_service):
    return PluginsService(
        release_service=release_service,
        plugins_directory=_MOCK_PLUGINS,
        consortium_root=_CONSORTIUM_ROOT,
    )


@pytest.fixture
def plugins_service_with_mock_registry(release_service):
    svc = PluginsService(
        release_service=release_service,
        plugins_directory=_MOCK_PLUGINS,
        consortium_root=_CONSORTIUM_ROOT,
    )
    mock_registry = MagicMock()
    mock_registry.get_all_components.return_value = []
    svc._plugin_registry_service = mock_registry
    return svc, mock_registry


# --- __str__ / __repr__ ---


def test_str(plugins_service):
    assert str(plugins_service) == "Plugins Service"


def test_repr(plugins_service):
    assert repr(plugins_service) == "PluginsService()"


# --- get_plugin_from_plugin_project_folder ---


def test_get_plugin_from_folder_enabled(plugins_service):
    plugin = plugins_service.get_plugin_from_plugin_project_folder(
        plugin_project_folder=_MOCK_PLUGINS / "mock_plugin_valid"
    )
    assert plugin is not None
    assert plugin.label == "consortium.tests.services.mock_plugin_valid"


def test_get_plugin_from_folder_disabled_returns_none(plugins_service):
    result = plugins_service.get_plugin_from_plugin_project_folder(
        plugin_project_folder=_MOCK_PLUGINS / "mock_plugin_disabled"
    )
    assert result is None


def test_get_plugin_from_folder_disabled_with_flag_loads(plugins_service):
    result = plugins_service.get_plugin_from_plugin_project_folder(
        plugin_project_folder=_MOCK_PLUGINS / "mock_plugin_disabled",
        ignore_enabled_plugin_flag=True,
    )
    assert result is not None


# --- get_plugins_from_plugin_project_folder_directories ---


def test_get_plugins_from_directories(plugins_service):
    retrieved, skipped, errored = (
        plugins_service.get_plugins_from_plugin_project_folder_directories(
            directory=_MOCK_PLUGINS
        )
    )
    assert isinstance(retrieved, list)
    assert isinstance(skipped, list)
    assert isinstance(errored, list)
    labels = [p.label for p in retrieved]
    assert "consortium.tests.services.mock_plugin_valid" in labels


# --- register_plugin ---


def test_register_plugin_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugin = MagicMock()
    svc.register_plugin(plugin=mock_plugin)
    registry.register_component.assert_called_once_with(component=mock_plugin)


# --- register_plugin_from_plugin_project_folder ---


def test_register_plugin_from_folder_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    folder = pathlib.Path("/tmp/some_plugin")
    mock_plugin = MagicMock()
    registry.register_component_from_component_project_folder.return_value = mock_plugin
    result = svc.register_plugin_from_plugin_project_folder(
        plugin_project_folder=folder
    )
    registry.register_component_from_component_project_folder.assert_called_once_with(
        component_project_folder=folder,
        ignore_enabled_component_flag=False,
    )
    assert result == mock_plugin


# --- load_plugin_from_plugin_project_folder ---


@pytest.mark.anyio
async def test_load_plugin_from_folder_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    folder = pathlib.Path("/tmp/some_plugin")
    mock_plugin = MagicMock()
    registry.load_component_from_component_project_folder = AsyncMock(
        return_value=mock_plugin
    )
    result = await svc.load_plugin_from_plugin_project_folder(
        plugin_project_folder=folder
    )
    registry.load_component_from_component_project_folder.assert_called_once_with(
        component_project_folder=folder,
        ignore_enabled_component_flag=False,
        context={"timeout": 5},
    )
    assert result == mock_plugin


# --- unload_plugin_by_plugin_id ---


@pytest.mark.anyio
async def test_unload_plugin_by_id_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    plugin_id = uuid.uuid4()
    registry.unload_component_by_component_id = AsyncMock(return_value=None)
    await svc.unload_plugin_by_plugin_id(
        plugin_id=plugin_id, timeout=10, force_unload=True
    )
    registry.unload_component_by_component_id.assert_called_once_with(
        component_id=plugin_id,
        context={"timeout": 10, "force_unload": True, "logger": svc._logger},
    )


# --- reload_plugin_by_plugin_id ---


@pytest.mark.anyio
async def test_reload_plugin_by_id_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    plugin_id = uuid.uuid4()
    mock_plugin = MagicMock()
    registry.reload_component_by_component_id = AsyncMock(return_value=mock_plugin)
    result = await svc.reload_plugin_by_plugin_id(plugin_id=plugin_id)
    registry.reload_component_by_component_id.assert_called_once()
    assert result == mock_plugin


# --- start_plugin_by_plugin_id ---


@pytest.mark.anyio
async def test_start_plugin_by_id(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugin = MagicMock()
    mock_plugin.start = AsyncMock()
    plugin_id = uuid.uuid4()
    registry.get_component_by_component_id.return_value = mock_plugin
    await svc.start_plugin_by_plugin_id(plugin_id=plugin_id)
    mock_plugin.start.assert_called_once()


# --- stop_plugin_by_plugin_id ---


@pytest.mark.anyio
async def test_stop_plugin_by_id(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugin = MagicMock()
    mock_plugin.stop = AsyncMock()
    plugin_id = uuid.uuid4()
    registry.get_component_by_component_id.return_value = mock_plugin
    await svc.stop_plugin_by_plugin_id(plugin_id=plugin_id)
    mock_plugin.stop.assert_called_once()


# --- cancel_plugin_by_plugin_id ---


@pytest.mark.anyio
async def test_cancel_plugin_by_id(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugin = MagicMock()
    mock_plugin.cancel = AsyncMock()
    plugin_id = uuid.uuid4()
    registry.get_component_by_component_id.return_value = mock_plugin
    await svc.cancel_plugin_by_plugin_id(plugin_id=plugin_id)
    mock_plugin.cancel.assert_called_once()


# --- get_plugin_by_plugin_id ---


def test_get_plugin_by_id_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugin = MagicMock()
    plugin_id = uuid.uuid4()
    registry.get_component_by_component_id.return_value = mock_plugin
    result = svc.get_plugin_by_plugin_id(plugin_id=plugin_id)
    registry.get_component_by_component_id.assert_called_once_with(
        component_id=plugin_id
    )
    assert result == mock_plugin


# --- get_plugins_by_label ---


def test_get_plugins_by_label_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugins = [MagicMock()]
    registry.get_components_by_label.return_value = mock_plugins
    result = svc.get_plugins_by_label(label="some.label")
    registry.get_components_by_label.assert_called_once_with(label="some.label")
    assert result == mock_plugins


# --- get_all_plugins ---


def test_get_all_plugins_delegates(plugins_service_with_mock_registry):
    svc, registry = plugins_service_with_mock_registry
    mock_plugins = [MagicMock(), MagicMock()]
    registry.get_all_components.return_value = mock_plugins
    result = svc.get_all_plugins()
    assert result == mock_plugins


# --- load_framework_plugins ---


@pytest.mark.anyio
async def test_load_framework_plugins_loads_from_directory(
    plugins_service_with_mock_registry,
):
    svc, registry = plugins_service_with_mock_registry
    # Provide mock resolved order so registration is attempted.
    mock_plugin = MagicMock()
    mock_plugin.autostart = False
    svc._plugin_loader_service = MagicMock()
    svc._plugin_loader_service.resolve_component_load_order.return_value = (
        [mock_plugin],
        [],
    )
    svc.get_plugins_from_plugin_project_folder_directories = MagicMock(
        return_value=([], [], [])
    )
    svc.get_all_plugins = MagicMock(return_value=[])
    svc.register_plugin = MagicMock()
    await svc.load_framework_plugins()
    svc.register_plugin.assert_called_once_with(mock_plugin)
