import graphlib
import pathlib
from unittest.mock import MagicMock

import packaging.requirements as requirements
import packaging.version as pv
import pytest

from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentProjectEntryPointModuleNotFoundError,
    ComponentProjectInterfaceError,
    ComponentProjectManifestFileNotFoundError,
    ComponentProjectSymbolNotFoundError,
    IncompatibleComponentDependencyVersionError,
    IncompatibleComponentFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalComponentProjectError,
    InvalidComponentProjectManifestFileJSONError,
    InvalidComponentProjectManifestFileSchemaError,
    InvalidComponentProjectPyProjectFileDependencyError,
    InvalidComponentProjectPyProjectFileTOMLError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.services.component_loader_services.event_hook_loader_service import (
    EventHookLoaderService,
)
from consortium.server.services.component_loader_services.plugin_loader_service import (
    PluginLoaderService,
)

_HERE = pathlib.Path(__file__).parent
_MOCK_PLUGINS = _HERE / "mock" / "plugins"
_MOCK_EVENT_HOOKS = _HERE / "mock" / "event_hooks"
_CONSORTIUM_ROOT = _HERE.parent.parent


@pytest.fixture(scope="module")
def mock_release_service():
    svc = MagicMock()
    svc.release.version = "0.1.0"
    return svc


@pytest.fixture(scope="module")
def plugin_loader(mock_release_service):
    return PluginLoaderService(
        release_service=mock_release_service,
        consortium_root=_CONSORTIUM_ROOT,
    )


@pytest.fixture(scope="module")
def event_hook_loader(mock_release_service):
    return EventHookLoaderService(
        release_service=mock_release_service,
        consortium_root=_CONSORTIUM_ROOT,
    )


# --- Valid loading ---


def test_valid_plugin_loads(plugin_loader):
    plugin = plugin_loader.get_component_from_component_project_folder(
        _MOCK_PLUGINS / "mock_plugin_valid"
    )
    assert plugin is not None
    assert plugin.label == "consortium.tests.services.mock_plugin_valid"


def test_disabled_plugin_returns_none(plugin_loader):
    result = plugin_loader.get_component_from_component_project_folder(
        _MOCK_PLUGINS / "mock_plugin_disabled"
    )
    assert result is None


def test_disabled_plugin_with_ignore_flag_loads(plugin_loader):
    result = plugin_loader.get_component_from_component_project_folder(
        _MOCK_PLUGINS / "mock_plugin_disabled",
        ignore_enabled_component_flag=True,
    )
    assert result is not None


# --- Manifest errors ---


def test_missing_manifest_raises(plugin_loader, tmp_path):
    with pytest.raises(ComponentProjectManifestFileNotFoundError):
        plugin_loader.get_component_from_component_project_folder(tmp_path)


def test_bad_json_manifest_raises(plugin_loader):
    with pytest.raises(InvalidComponentProjectManifestFileJSONError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_json"
        )


def test_bad_schema_manifest_raises(plugin_loader):
    with pytest.raises(InvalidComponentProjectManifestFileSchemaError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_schema"
        )


def test_bad_entry_point_format_raises(plugin_loader):
    # Entry point without colon triggers schema error from the format check.
    with pytest.raises(InvalidComponentProjectManifestFileSchemaError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_entry_point"
        )


# --- pyproject.toml errors ---


def test_bad_toml_raises(plugin_loader):
    with pytest.raises(InvalidComponentProjectPyProjectFileTOMLError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_toml"
        )


def test_missing_dep_raises(plugin_loader):
    with pytest.raises(ThirdPartyDependencyNotFoundError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_missing_dep"
        )


def test_incompatible_dep_raises(plugin_loader):
    with pytest.raises(IncompatibleThirdPartyDependencyVersionError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_incompatible_dep"
        )


def test_bad_dep_format_raises(plugin_loader):
    with pytest.raises(InvalidComponentProjectPyProjectFileDependencyError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_dep_format"
        )


# --- Module / symbol / interface errors ---


def test_no_module_raises(plugin_loader):
    with pytest.raises(ComponentProjectEntryPointModuleNotFoundError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_no_module"
        )


def test_bad_symbol_raises(plugin_loader):
    with pytest.raises(ComponentProjectSymbolNotFoundError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_symbol"
        )


def test_bad_interface_raises(plugin_loader):
    with pytest.raises(ComponentProjectInterfaceError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_interface"
        )


def test_bad_framework_version_raises(plugin_loader):
    with pytest.raises(IncompatibleComponentFrameworkVersionError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_bad_version"
        )


def test_import_error_raises_internal_error(plugin_loader):
    with pytest.raises(InternalComponentProjectError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_import_error"
        )


def test_init_error_raises_internal_error(plugin_loader):
    with pytest.raises(InternalComponentProjectError):
        plugin_loader.get_component_from_component_project_folder(
            _MOCK_PLUGINS / "mock_plugin_init_error"
        )


# --- Directory scanning ---


def test_scan_directory_classifies_results(plugin_loader):
    retrieved, skipped, errored = (
        plugin_loader.get_components_from_component_project_folder_directories(
            _MOCK_PLUGINS
        )
    )
    # At minimum the valid plugin should be loaded successfully.
    labels = [p.label for p in retrieved]
    assert "consortium.tests.services.mock_plugin_valid" in labels
    # Disabled plugin should be skipped.
    assert len(skipped) > 0
    # Bad manifest/module entries should be errored.
    assert len(errored) > 0


def test_scan_directory_ignore_enabled(plugin_loader):
    retrieved, skipped, _ = (
        plugin_loader.get_components_from_component_project_folder_directories(
            _MOCK_PLUGINS,
            ignore_enabled_component_flag=True,
        )
    )
    labels = [p.label for p in retrieved]
    assert "consortium.tests.services.mock_plugin_disabled" in labels
    assert len(skipped) == 0


# --- Event hook loader ---


def test_valid_event_hook_loads(event_hook_loader):
    event_hook = event_hook_loader.get_component_from_component_project_folder(
        _MOCK_EVENT_HOOKS / "mock_event_hook_valid"
    )
    assert event_hook is not None
    assert event_hook.label == "consortium.tests.services.mock_event_hook_valid"


def test_disabled_event_hook_returns_none(event_hook_loader):
    result = event_hook_loader.get_component_from_component_project_folder(
        _MOCK_EVENT_HOOKS / "mock_event_hook_disabled"
    )
    assert result is None


# --- resolve_component_load_order ---


def test_resolve_order_no_deps(plugin_loader):
    comp = MagicMock()
    comp.label = "comp_a"
    comp.component_dependencies = set()

    ordered, skipped = plugin_loader.resolve_component_load_order(
        components=[comp], already_loaded_components=[]
    )
    assert len(ordered) == 1
    assert ordered[0].label == "comp_a"
    assert skipped == []


def test_resolve_order_deps_ordered_before_dependents(plugin_loader):
    comp_a = MagicMock()
    comp_a.label = "comp_a"
    comp_a.component_dependencies = set()
    comp_a.version = pv.Version("1.0.0")

    comp_b = MagicMock()
    comp_b.label = "comp_b"
    comp_b.component_dependencies = {requirements.Requirement("comp_a")}

    ordered, skipped = plugin_loader.resolve_component_load_order(
        components=[comp_b, comp_a], already_loaded_components=[]
    )
    assert len(ordered) == 2
    assert ordered[0].label == "comp_a"
    assert ordered[1].label == "comp_b"
    assert skipped == []


def test_resolve_order_missing_dep_skipped(plugin_loader):
    comp = MagicMock()
    comp.label = "comp_a"
    comp.component_dependencies = {requirements.Requirement("ghost_dep")}

    ordered, skipped = plugin_loader.resolve_component_load_order(
        components=[comp], already_loaded_components=[]
    )
    assert ordered == []
    assert len(skipped) == 1
    _, err = skipped[0]
    assert isinstance(err, ComponentDependencyNotFoundError)


def test_resolve_order_incompatible_dep_version_skipped(plugin_loader):
    comp_a = MagicMock()
    comp_a.label = "comp_a"
    comp_a.component_dependencies = set()
    comp_a.version = pv.Version("1.0.0")

    comp_b = MagicMock()
    comp_b.label = "comp_b"
    comp_b.component_dependencies = {requirements.Requirement("comp_a>=999.0.0")}

    ordered, skipped = plugin_loader.resolve_component_load_order(
        components=[comp_a, comp_b], already_loaded_components=[]
    )
    ordered_labels = {c.label for c in ordered}
    skipped_labels = {c.label for c, _ in skipped}
    assert "comp_a" in ordered_labels
    assert "comp_b" in skipped_labels
    _, err = next((c, e) for c, e in skipped if c.label == "comp_b")
    assert isinstance(err, IncompatibleComponentDependencyVersionError)


def test_resolve_order_dependent_on_skipped_is_also_skipped(plugin_loader):
    # comp_a has missing dep -> skipped
    # comp_b depends on comp_a -> also skipped
    comp_a = MagicMock()
    comp_a.label = "comp_a"
    comp_a.component_dependencies = {requirements.Requirement("no_such_dep")}

    comp_b = MagicMock()
    comp_b.label = "comp_b"
    comp_b.component_dependencies = {requirements.Requirement("comp_a")}

    ordered, skipped = plugin_loader.resolve_component_load_order(
        components=[comp_a, comp_b], already_loaded_components=[]
    )
    skipped_labels = {c.label for c, _ in skipped}
    assert "comp_a" in skipped_labels
    assert "comp_b" in skipped_labels


def test_resolve_order_already_loaded_satisfies_dep(plugin_loader):
    already = MagicMock()
    already.label = "comp_a"
    already.version = pv.Version("1.0.0")

    comp_b = MagicMock()
    comp_b.label = "comp_b"
    comp_b.component_dependencies = {requirements.Requirement("comp_a>=1.0.0")}

    ordered, skipped = plugin_loader.resolve_component_load_order(
        components=[comp_b], already_loaded_components=[already]
    )
    assert len(ordered) == 1
    assert ordered[0].label == "comp_b"
    assert skipped == []


def test_resolve_order_cycle_raises(plugin_loader):
    comp_a = MagicMock()
    comp_a.label = "comp_a"
    comp_a.component_dependencies = {requirements.Requirement("comp_b")}

    comp_b = MagicMock()
    comp_b.label = "comp_b"
    comp_b.component_dependencies = {requirements.Requirement("comp_a")}

    with pytest.raises(graphlib.CycleError):
        plugin_loader.resolve_component_load_order(
            components=[comp_a, comp_b], already_loaded_components=[]
        )
