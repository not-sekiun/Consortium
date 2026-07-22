import pathlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consortium.framework._core.components.component_status import State
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    PluginStopTimeoutError,
)
from consortium.server.services.component_registry_services.plugin_registry_service import (
    PluginRegistryService,
)


def _closing_side_effect(exc: Exception):
    # asyncio.wait_for is mocked wholesale in the tests below, so the coroutine passed
    # to it (e.g. _stop_plugin()) is never awaited by the real implementation. Closing
    # it here avoids a "coroutine was never awaited" RuntimeWarning surfacing later,
    # attached to an unrelated test, when it gets garbage collected.
    def _side_effect(coro, *args, **kwargs):
        coro.close()
        raise exc

    return _side_effect


def _make_mock_loader():
    loader = MagicMock()
    loader.validate_component_component_dependencies.return_value = True
    loader.get_component_from_directory.return_value = None
    loader.get_all_components_from_directory.return_value = (
        [],
        [],
        [],
    )
    return loader


def _make_plugin(autostart=False, state=State.STOPPED):
    plugin = MagicMock()
    plugin.plugin_id = uuid.uuid4()
    plugin.root_directory = pathlib.Path("/tmp/mock_plugin")
    plugin.label = "test.plugin"
    plugin.autostart = autostart
    plugin.status = MagicMock()
    plugin.status.state = state
    plugin.start = AsyncMock()
    plugin.stop = AsyncMock()
    plugin.cancel = AsyncMock()
    plugin.stop_event = MagicMock()
    plugin.stop_event.wait = AsyncMock()
    plugin.component_dependencies = set()
    plugin.__str__ = MagicMock(return_value="MockPlugin")
    return plugin


@pytest.fixture
def registry():
    return PluginRegistryService(
        component_loader_service=_make_mock_loader(),
        component_framework_directory=pathlib.Path("/tmp"),
    )


# --- Accessors ---


def test_get_component_id(registry):
    plugin = _make_plugin()
    assert registry._get_component_id(plugin) == plugin.plugin_id


# --- _component_load_procedure ---


@pytest.mark.anyio
async def test_load_procedure_no_autostart_skips_start(registry):
    plugin = _make_plugin(autostart=False)
    result = await registry._component_load_procedure(plugin, {"timeout": 5})
    plugin.start.assert_not_called()
    assert result is plugin


@pytest.mark.anyio
async def test_load_procedure_autostart_calls_start(registry):
    plugin = _make_plugin(autostart=True)
    result = await registry._component_load_procedure(plugin, {"timeout": 5})
    plugin.start.assert_called_once()
    assert result is plugin


# --- _component_unload_procedure ---


@pytest.mark.anyio
async def test_unload_procedure_not_running_returns_early(registry):
    plugin = _make_plugin(state=State.STOPPED)
    result = await registry._component_unload_procedure(
        plugin, {"timeout": 5, "force_unload": False, "logger": MagicMock()}
    )
    plugin.stop.assert_not_called()
    assert result is plugin


@pytest.mark.anyio
async def test_unload_procedure_running_plugin_stopped(registry):
    plugin = _make_plugin(state=State.RUNNING)

    async def _stop_effect():
        plugin.status.state = State.STOPPED

    plugin.stop.side_effect = _stop_effect

    result = await registry._component_unload_procedure(
        plugin, {"timeout": 5, "force_unload": False, "logger": MagicMock()}
    )
    plugin.stop.assert_called_once()
    assert result is plugin


@pytest.mark.anyio
async def test_unload_procedure_timeout_no_force_raises(registry):
    plugin = _make_plugin(state=State.RUNNING)
    with patch(
        "consortium.server.services.component_registry_services.plugin_registry_service.asyncio.wait_for",
        side_effect=_closing_side_effect(TimeoutError()),
    ):
        with pytest.raises(PluginStopTimeoutError):
            await registry._component_unload_procedure(
                plugin, {"timeout": 5, "force_unload": False, "logger": MagicMock()}
            )


@pytest.mark.anyio
async def test_unload_procedure_timeout_force_cancels(registry):
    plugin = _make_plugin(state=State.RUNNING)
    mock_logger = MagicMock()
    with patch(
        "consortium.server.services.component_registry_services.plugin_registry_service.asyncio.wait_for",
        side_effect=_closing_side_effect(TimeoutError()),
    ):
        result = await registry._component_unload_procedure(
            plugin, {"timeout": 5, "force_unload": True, "logger": mock_logger}
        )
    plugin.cancel.assert_called_once()
    mock_logger.warning.assert_called_once()
    assert result is plugin


@pytest.mark.anyio
async def test_unload_procedure_exception_no_force_reraises(registry):
    plugin = _make_plugin(state=State.RUNNING)
    with patch(
        "consortium.server.services.component_registry_services.plugin_registry_service.asyncio.wait_for",
        side_effect=_closing_side_effect(RuntimeError("unexpected")),
    ):
        with pytest.raises(RuntimeError, match="unexpected"):
            await registry._component_unload_procedure(
                plugin, {"timeout": 5, "force_unload": False, "logger": MagicMock()}
            )


@pytest.mark.anyio
async def test_unload_procedure_exception_force_cancels(registry):
    plugin = _make_plugin(state=State.RUNNING)
    mock_logger = MagicMock()
    with patch(
        "consortium.server.services.component_registry_services.plugin_registry_service.asyncio.wait_for",
        side_effect=_closing_side_effect(RuntimeError("unexpected")),
    ):
        result = await registry._component_unload_procedure(
            plugin, {"timeout": 5, "force_unload": True, "logger": mock_logger}
        )
    plugin.cancel.assert_called_once()
    mock_logger.error.assert_called_once()
    assert result is plugin
