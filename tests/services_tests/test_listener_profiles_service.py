import pathlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import consortium.server.server_singletons as _ss
from consortium.server.services.listener_profiles_service import ListenerProfilesService
from consortium.server.services.release_service import ReleaseService
from tests.services_tests.mocks.paths_service import make_mock_paths_service

_HERE = pathlib.Path(__file__).parent
_CONSORTIUM_ROOT = _HERE.parent.parent
_RELEASE_JSON = _CONSORTIUM_ROOT / "data" / "release.json"


@pytest.fixture(scope="module")
def release_service():
    return ReleaseService(release_json_file=_RELEASE_JSON)


@pytest.fixture
def svc_with_mock_registry(release_service, tmp_path):
    svc = ListenerProfilesService(
        release_service=release_service,
        paths_service=make_mock_paths_service(
            listeners_directory=tmp_path,
            consortium_root=_CONSORTIUM_ROOT,
        ),
    )
    mock_registry = MagicMock()
    mock_registry.get_all_components.return_value = []
    svc._listener_profile_registry_service = mock_registry
    return svc, mock_registry


# --- __str__ / __repr__ ---


def test_str(svc_with_mock_registry):
    svc, _ = svc_with_mock_registry
    assert str(svc) == "Listener Profiles Service"


def test_repr(svc_with_mock_registry):
    svc, _ = svc_with_mock_registry
    assert repr(svc) == "ListenerProfilesService()"


# --- get_listener_profile_from_directory ---


def test_get_from_folder_enabled(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    folder = pathlib.Path("/tmp/listener_folder")
    mock_profile = MagicMock()
    registry.get_component_from_directory.return_value = mock_profile
    result = svc.get_listener_profile_from_directory(directory=folder)
    assert result == mock_profile


def test_get_from_folder_disabled_returns_none(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    registry.get_component_from_directory.return_value = None
    result = svc.get_listener_profile_from_directory(
        directory=pathlib.Path("/tmp/disabled")
    )
    assert result is None


# --- get_listener_profiles_from_directories ---


def test_get_profiles_from_directories(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_profile = MagicMock()
    registry.get_all_components_from_directory.return_value = (
        [mock_profile],
        [],
        [],
    )
    retrieved, skipped, errored = svc.get_all_listener_profiles_from_directory(
        directory=pathlib.Path("/tmp/listeners")
    )
    assert len(retrieved) == 1
    assert skipped == []


# --- load_listener_profile ---


@pytest.mark.anyio
async def test_load_listener_profile_resolves_compatible_types(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_profile = MagicMock()
    registry.load_component = AsyncMock(return_value=mock_profile)

    with patch.object(_ss, "c2_types_service") as mock_c2:
        await svc.load_listener_profile(listener_profile=mock_profile)

    mock_c2._resolve_registered_compatible_agent_types_for_listener_profiles.assert_called_once_with(
        mock_profile
    )


# --- load_listener_profile_from_directory ---


@pytest.mark.anyio
async def test_load_from_folder_resolves_types(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_profile = MagicMock()
    registry.load_component_from_directory = AsyncMock(return_value=mock_profile)
    folder = pathlib.Path("/tmp/listener_profile")

    with patch.object(_ss, "c2_types_service") as mock_c2:
        result = await svc.load_listener_profile_from_directory(directory=folder)

    assert result == mock_profile
    mock_c2._resolve_registered_compatible_agent_types_for_listener_profiles.assert_called_once_with(
        mock_profile
    )


@pytest.mark.anyio
async def test_load_from_folder_disabled_skips_resolution(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    registry.load_component_from_directory = AsyncMock(return_value=None)
    folder = pathlib.Path("/tmp/disabled_listener")

    with patch.object(_ss, "c2_types_service") as mock_c2:
        result = await svc.load_listener_profile_from_directory(directory=folder)

    assert result is None
    mock_c2._resolve_registered_compatible_agent_types_for_listener_profiles.assert_not_called()


# --- unload_listener_profile_by_listener_profile_id ---


@pytest.mark.anyio
async def test_unload_profile_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    profile_id = uuid.uuid4()
    registry.unload_component_by_component_id = AsyncMock(return_value=None)
    await svc.unload_listener_profile_by_listener_profile_id(
        listener_profile_id=profile_id
    )
    registry.unload_component_by_component_id.assert_called_once_with(
        component_id=profile_id,
    )


# --- reload_listener_profile_by_listener_profile_id ---


@pytest.mark.anyio
async def test_reload_profile_resolves_types(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    profile_id = uuid.uuid4()
    mock_profile = MagicMock()
    registry.reload_component_by_component_id = AsyncMock(return_value=mock_profile)

    with patch.object(_ss, "c2_types_service") as mock_c2:
        result = await svc.reload_listener_profile_by_listener_profile_id(
            listener_profile_id=profile_id
        )

    assert result == mock_profile
    mock_c2._resolve_registered_compatible_agent_types_for_listener_profiles.assert_called_once_with(
        mock_profile
    )


@pytest.mark.anyio
async def test_reload_profile_disabled_skips_resolution(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    profile_id = uuid.uuid4()
    registry.reload_component_by_component_id = AsyncMock(return_value=None)

    with patch.object(_ss, "c2_types_service") as mock_c2:
        result = await svc.reload_listener_profile_by_listener_profile_id(
            listener_profile_id=profile_id
        )

    assert result is None
    mock_c2._resolve_registered_compatible_agent_types_for_listener_profiles.assert_not_called()


# --- get_all_listener_profiles ---


def test_get_all_listener_profiles_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    mock_profiles = [MagicMock(), MagicMock()]
    registry.get_all_components.return_value = mock_profiles
    result = svc.get_all_listener_profiles()
    assert result == mock_profiles


# --- get_listener_profile_by_listener_profile_id ---


def test_get_profile_by_id_delegates(svc_with_mock_registry):
    svc, registry = svc_with_mock_registry
    profile_id = uuid.uuid4()
    mock_profile = MagicMock()
    registry.get_component_by_component_id.return_value = mock_profile
    result = svc.get_listener_profile_by_listener_profile_id(
        listener_profile_id=profile_id
    )
    registry.get_component_by_component_id.assert_called_once()
    assert result == mock_profile
