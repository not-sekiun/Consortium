import pathlib
import uuid
from unittest.mock import MagicMock

import pytest

from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentAlreadyRegisteredError,
    ComponentNotFoundError,
    DuplicateComponentLabelError,
)
from consortium.server.services.component_registry_services.component_registry_service import (
    ComponentRegistryService,
)


class _ConcreteRegistry(ComponentRegistryService):
    def _get_component_id(self, component):
        return component._id

    def _get_component_project_folder(self, component):
        return component._folder


def _make_mock_loader():
    loader = MagicMock()
    loader.validate_component_component_dependencies.return_value = True
    return loader


def _make_component(label="comp.label", component_id=None):
    comp = MagicMock()
    comp._id = component_id or uuid.uuid4()
    comp._folder = pathlib.Path("/tmp/test_comp")
    comp.label = label
    comp.component_dependencies = set()
    comp.__str__ = lambda self: f"MockComponent({label})"
    return comp


@pytest.fixture
def loader():
    return _make_mock_loader()


@pytest.fixture
def registry(loader):
    return _ConcreteRegistry(
        component_loader_service=loader,
        component_framework_directory=pathlib.Path("/tmp"),
    )


# --- register_component ---


def test_register_component_succeeds(registry):
    comp = _make_component()
    registry.register_component(comp)
    assert comp in registry.get_all_components()


def test_register_component_duplicate_id_raises(registry):
    comp = _make_component()
    registry.register_component(comp)
    with pytest.raises(ComponentAlreadyRegisteredError):
        registry.register_component(comp)


def test_register_component_duplicate_label_raises(registry):
    comp1 = _make_component(label="shared.label")
    comp2 = _make_component(label="shared.label")
    registry.register_component(comp1)
    with pytest.raises(DuplicateComponentLabelError):
        registry.register_component(comp2)


def test_register_component_empty_label_allowed(registry):
    comp1 = _make_component(label="")
    comp2 = _make_component(label="")
    registry.register_component(comp1)
    # Empty labels must not be considered duplicates.
    registry.register_component(comp2)
    assert len(registry.get_all_components()) == 2


# --- register_component_from_component_project_folder ---


def test_register_from_folder_delegates_and_registers(registry, loader):
    folder = pathlib.Path("/tmp/plugin_folder")
    comp = _make_component()
    loader.get_component_from_component_project_folder.return_value = comp
    result = registry.register_component_from_component_project_folder(
        component_project_folder=folder
    )
    assert result == comp
    assert comp in registry.get_all_components()


def test_register_from_folder_disabled_returns_none(registry, loader):
    folder = pathlib.Path("/tmp/disabled_folder")
    loader.get_component_from_component_project_folder.return_value = None
    result = registry.register_component_from_component_project_folder(
        component_project_folder=folder
    )
    assert result is None


# --- load_component ---


@pytest.mark.anyio
async def test_load_component_runs_procedure_and_registers(registry):
    comp = _make_component()
    result = await registry.load_component(component=comp)
    assert result == comp
    assert comp in registry.get_all_components()


@pytest.mark.anyio
async def test_load_component_duplicate_raises(registry):
    comp = _make_component()
    await registry.load_component(component=comp)
    with pytest.raises(ComponentAlreadyRegisteredError):
        await registry.load_component(component=comp)


@pytest.mark.anyio
async def test_load_component_default_empty_context(registry):
    comp = _make_component()
    # Should not raise even without context argument.
    result = await registry.load_component(component=comp)
    assert result == comp


# --- load_component_from_component_project_folder ---


@pytest.mark.anyio
async def test_load_from_folder_loads_enabled(registry, loader):
    folder = pathlib.Path("/tmp/plugin_folder")
    comp = _make_component(label="loaded.comp")
    loader.get_component_from_component_project_folder.return_value = comp
    result = await registry.load_component_from_component_project_folder(
        component_project_folder=folder
    )
    assert result == comp


@pytest.mark.anyio
async def test_load_from_folder_disabled_returns_none(registry, loader):
    folder = pathlib.Path("/tmp/disabled_folder")
    loader.get_component_from_component_project_folder.return_value = None
    result = await registry.load_component_from_component_project_folder(
        component_project_folder=folder
    )
    assert result is None


# --- unload_component_by_component_id ---


@pytest.mark.anyio
async def test_unload_removes_component(registry):
    comp = _make_component()
    await registry.load_component(component=comp)
    assert comp in registry.get_all_components()
    await registry.unload_component_by_component_id(component_id=comp._id)
    assert comp not in registry.get_all_components()


@pytest.mark.anyio
async def test_unload_not_found_raises(registry):
    with pytest.raises(ComponentNotFoundError):
        await registry.unload_component_by_component_id(component_id=uuid.uuid4())


# --- reload_component_by_component_id ---


@pytest.mark.anyio
async def test_reload_unloads_then_loads_from_folder(registry, loader):
    folder = pathlib.Path("/tmp/comp_folder")
    comp = _make_component(label="reload.comp")
    comp._folder = folder

    await registry.load_component(component=comp)
    original_id = comp._id

    new_comp = _make_component(label="reload.comp")
    new_comp._folder = folder
    loader.get_component_from_component_project_folder.return_value = new_comp

    result = await registry.reload_component_by_component_id(component_id=original_id)
    # Original component was removed; new one was loaded.
    assert original_id not in [
        str(registry._get_component_id(c)) for c in registry.get_all_components()
    ]
    assert result == new_comp


# --- get_component_by_component_id ---


def test_get_by_id_returns_component(registry):
    comp = _make_component()
    registry.register_component(comp)
    result = registry.get_component_by_component_id(component_id=comp._id)
    assert result == comp


def test_get_by_id_string_uuid_works(registry):
    comp = _make_component()
    registry.register_component(comp)
    result = registry.get_component_by_component_id(component_id=str(comp._id))
    assert result == comp


def test_get_by_id_not_found_raises(registry):
    with pytest.raises(ComponentNotFoundError):
        registry.get_component_by_component_id(component_id=uuid.uuid4())


# --- get_components_by_label ---


def test_get_by_label_returns_matching(registry):
    comp1 = _make_component(label="my.label")
    comp2 = _make_component(label="other.label")
    registry.register_component(comp1)
    registry.register_component(comp2)
    result = registry.get_components_by_label("my.label")
    assert comp1 in result
    assert comp2 not in result


def test_get_by_label_empty_when_no_match(registry):
    result = registry.get_components_by_label("nonexistent.label")
    assert result == []


# --- get_all_components ---


def test_get_all_components_returns_all(registry):
    comp1 = _make_component(label="a")
    comp2 = _make_component(label="b")
    registry.register_component(comp1)
    registry.register_component(comp2)
    all_comps = registry.get_all_components()
    assert comp1 in all_comps
    assert comp2 in all_comps


def test_get_all_components_empty_initially():
    loader = _make_mock_loader()
    reg = _ConcreteRegistry(
        component_loader_service=loader,
        component_framework_directory=pathlib.Path("/tmp"),
    )
    assert reg.get_all_components() == []


# --- _component_load_procedure and _component_unload_procedure defaults ---


@pytest.mark.anyio
async def test_default_load_procedure_returns_component(registry):
    comp = _make_component()
    result = await registry._component_load_procedure(comp, {})
    assert result == comp


@pytest.mark.anyio
async def test_default_unload_procedure_returns_component(registry):
    comp = _make_component()
    result = await registry._component_unload_procedure(comp, {})
    assert result == comp
