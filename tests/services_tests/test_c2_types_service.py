from unittest.mock import MagicMock

import pytest

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions import (
    AgentTypeNotFoundError,
    DuplicateAgentTypeNameError,
    ListenerTypeNotFoundError,
    UnresolvableAgentTypeReferenceError,
)
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.services.c2_types_service import C2TypesService
from consortium.server.services.listener_profiles_service import ListenerProfilesService

# ---------------------------------------------------------------------------
# Minimal concrete types for testing
# ---------------------------------------------------------------------------


class _ListenerTypeA(BaseListenerType):
    name = "type_a"


class _ListenerTypeB(BaseListenerType):
    name = "type_b"


class _AgentTypeX(BaseAgentType):
    name = "agent_x"
    agent_capabilities = set()
    # compatible_listener_types is not defined on BaseAgentType but is accessed by
    # get_compatible_listener_types_from_agent_type_name; set it here for tests.
    compatible_listener_types: list = []


class _AgentTypeY(BaseAgentType):
    name = "agent_y"
    agent_capabilities = set()
    compatible_listener_types: list = []


# ---------------------------------------------------------------------------
# Helpers to build mock profiles
# ---------------------------------------------------------------------------


def _make_listener_profile(listener_type: BaseListenerType) -> MagicMock:
    profile = MagicMock()
    profile.listener_type = listener_type
    return profile


def _make_agent_profile(
    agent_type, compatible_listener_type_names: set[str]
) -> MagicMock:
    profile = MagicMock()
    profile.agent_type = agent_type
    profile.agent_template = MagicMock()
    profile.agent_template.compatible_listener_types = compatible_listener_type_names
    return profile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def listener_profiles_service() -> MagicMock:
    return MagicMock(spec=ListenerProfilesService)


@pytest.fixture
def agent_profiles_service() -> MagicMock:
    return MagicMock(spec=AgentProfilesService)


@pytest.fixture
def service(
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
) -> C2TypesService:
    return C2TypesService(
        listener_profiles_service=listener_profiles_service,
        agent_profiles_service=agent_profiles_service,
    )


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(service: C2TypesService):
    assert "C2TypesService" in repr(service)


# ---------------------------------------------------------------------------
# get_all_listener_types
# ---------------------------------------------------------------------------


def test_get_all_listener_types_empty(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    listener_profiles_service.get_all_listener_profiles.return_value = []
    result = service.get_all_listener_types()
    assert result == []


def test_get_all_listener_types_deduplicates(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    t = _ListenerTypeA()
    profiles = [_make_listener_profile(t), _make_listener_profile(t)]
    listener_profiles_service.get_all_listener_profiles.return_value = profiles
    result = service.get_all_listener_types()
    assert len(result) == 1
    assert result[0] is t


def test_get_all_listener_types_multiple(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    ta, tb = _ListenerTypeA(), _ListenerTypeB()
    profiles = [_make_listener_profile(ta), _make_listener_profile(tb)]
    listener_profiles_service.get_all_listener_profiles.return_value = profiles
    result = service.get_all_listener_types()
    assert len(result) == 2


# ---------------------------------------------------------------------------
# get_listener_type_by_name
# ---------------------------------------------------------------------------


def test_get_listener_type_by_name_success(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    t = _ListenerTypeA()
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(t)
    ]
    found = service.get_listener_type_by_name("type_a")
    assert found is t


def test_get_listener_type_by_name_not_found_raises(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    listener_profiles_service.get_all_listener_profiles.return_value = []
    with pytest.raises(ListenerTypeNotFoundError):
        service.get_listener_type_by_name("nonexistent")


# ---------------------------------------------------------------------------
# get_all_agent_types
# ---------------------------------------------------------------------------


def test_get_all_agent_types_empty(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    agent_profiles_service.get_all_agent_profiles.return_value = []
    result = service.get_all_agent_types()
    assert result == []


def test_get_all_agent_types_deduplicates(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    profiles = [
        _make_agent_profile(at, set()),
        _make_agent_profile(at, set()),
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = profiles
    result = service.get_all_agent_types()
    assert len(result) == 1


# ---------------------------------------------------------------------------
# get_agent_type_by_name
# ---------------------------------------------------------------------------


def test_get_agent_type_by_name_success(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, set())
    ]
    found = service.get_agent_type_by_name("agent_x")
    assert found is at


def test_get_agent_type_by_name_not_found_raises(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    agent_profiles_service.get_all_agent_profiles.return_value = []
    with pytest.raises(AgentTypeNotFoundError):
        service.get_agent_type_by_name("nonexistent")


# ---------------------------------------------------------------------------
# get_compatible_listener_types_from_agent_type_name
# ---------------------------------------------------------------------------


def test_get_compatible_listener_types_from_agent_type_name_returns_names(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    # compatible_listener_types is read from agent_type (not agent_template) by this method
    at.compatible_listener_types = ["type_a", "type_b"]
    profiles = [_make_agent_profile(at, {"type_a", "type_b"})]
    agent_profiles_service.get_all_agent_profiles.return_value = profiles
    result = service.get_compatible_listener_types_from_agent_type_name("agent_x")
    assert set(result) == {"type_a", "type_b"}


def test_get_compatible_listener_types_from_agent_type_name_no_match(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    profiles = [_make_agent_profile(at, {"type_a"})]
    agent_profiles_service.get_all_agent_profiles.return_value = profiles
    result = service.get_compatible_listener_types_from_agent_type_name("agent_y")
    assert result == []


def test_get_compatible_listener_types_from_agent_type_name_deduplicates(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    at.compatible_listener_types = ["type_a", "type_a", "type_b"]
    profiles = [_make_agent_profile(at, set())]
    agent_profiles_service.get_all_agent_profiles.return_value = profiles
    result = service.get_compatible_listener_types_from_agent_type_name("agent_x")
    assert len(result) == len(set(result))


# ---------------------------------------------------------------------------
# get_registered_compatible_agent_types_from_listener_type_name
# ---------------------------------------------------------------------------


def test_get_registered_compatible_agent_types_from_listener_type_name(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    t = _ListenerTypeA()
    t.registered_compatible_agent_types = {"agent_x", "agent_y"}
    profiles = [_make_listener_profile(t)]
    listener_profiles_service.get_all_listener_profiles.return_value = profiles
    result = service.get_registered_compatible_agent_types_from_listener_type_name(
        "type_a"
    )
    assert set(result) == {"agent_x", "agent_y"}


def test_get_registered_compatible_agent_types_from_listener_type_name_no_match(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    listener_profiles_service.get_all_listener_profiles.return_value = []
    result = service.get_registered_compatible_agent_types_from_listener_type_name(
        "type_a"
    )
    assert result == []


# ---------------------------------------------------------------------------
# is_agent_type_registered
# ---------------------------------------------------------------------------


def test_is_agent_type_registered_true(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, set())
    ]
    assert service.is_agent_type_registered("agent_x") is True


def test_is_agent_type_registered_false(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    agent_profiles_service.get_all_agent_profiles.return_value = []
    assert service.is_agent_type_registered("agent_x") is False


# ---------------------------------------------------------------------------
# is_listener_type_registered
# ---------------------------------------------------------------------------


def test_is_listener_type_registered_true(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    t = _ListenerTypeA()
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(t)
    ]
    assert service.is_listener_type_registered("type_a") is True


def test_is_listener_type_registered_false(
    service: C2TypesService, listener_profiles_service: MagicMock
):
    listener_profiles_service.get_all_listener_profiles.return_value = []
    assert service.is_listener_type_registered("type_a") is False


# ---------------------------------------------------------------------------
# are_c2_types_compatible
# ---------------------------------------------------------------------------


def test_are_c2_types_compatible_returns_true(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    lt = _ListenerTypeA()
    at = _AgentTypeX()
    at.compatible_listener_types = [lt]
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(lt)
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {"type_a"})
    ]
    assert service.are_c2_types_compatible("agent_x", "type_a") is True


def test_are_c2_types_compatible_returns_false(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    lt = _ListenerTypeA()
    at = _AgentTypeX()
    at.compatible_listener_types = []
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(lt)
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, set())
    ]
    assert service.are_c2_types_compatible("agent_x", "type_a") is False


def test_are_c2_types_compatible_missing_agent_type_raises(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    lt = _ListenerTypeA()
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(lt)
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = []
    with pytest.raises(AgentTypeNotFoundError):
        service.are_c2_types_compatible("missing_agent", "type_a")


def test_are_c2_types_compatible_missing_listener_type_raises(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    at = _AgentTypeX()
    at.compatible_listener_types = []
    listener_profiles_service.get_all_listener_profiles.return_value = []
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, set())
    ]
    with pytest.raises(ListenerTypeNotFoundError):
        service.are_c2_types_compatible("agent_x", "missing_listener")


# ---------------------------------------------------------------------------
# _resolve_registered_compatible_agent_types_for_listener_profiles
# ---------------------------------------------------------------------------


def test_resolve_registered_compatible_agent_types_no_listener_profiles(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    # When no explicit profiles are passed and get_all_listener_profiles returns empty
    # the function takes the early return path (no listener profiles to resolve)
    listener_profiles_service.get_all_listener_profiles.return_value = []
    agent_profiles_service.get_all_agent_profiles.return_value = []
    # Should not raise
    service._resolve_registered_compatible_agent_types_for_listener_profiles()


def test_resolve_registered_compatible_agent_types_populates_reverse_index(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    lt = _ListenerTypeA()
    lt.registered_compatible_agent_types = set()

    at = _AgentTypeX()
    listener_profile = _make_listener_profile(lt)
    agent_profile = _make_agent_profile(at, {"type_a"})

    listener_profiles_service.get_all_listener_profiles.return_value = [
        listener_profile
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [agent_profile]

    service._resolve_registered_compatible_agent_types_for_listener_profiles(
        listener_profile
    )
    # The reverse index should now contain agent_x for type_a
    assert "agent_x" in lt.registered_compatible_agent_types


# ---------------------------------------------------------------------------
# _resolve_agent_type_references
# ---------------------------------------------------------------------------


def test_resolve_agent_type_references_no_profiles(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    agent_profiles_service.get_all_agent_profiles.return_value = []
    # Should not raise
    service._resolve_agent_type_references()


def test_resolve_agent_type_references_duplicate_agent_type_name_raises(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # Two different classes with the same name triggers DuplicateAgentTypeNameError
    class _AgentTypeXDuplicate(BaseAgentType):
        name = "agent_x"
        agent_capabilities = set()

    at1 = _AgentTypeX()
    at2 = _AgentTypeXDuplicate()

    p1 = _make_agent_profile(at1, set())
    p1.agent_template.__str__ = lambda self: "template_1"
    p2 = _make_agent_profile(at2, set())
    p2.agent_template.__str__ = lambda self: "template_2"

    agent_profiles_service.get_all_agent_profiles.return_value = [p1, p2]
    with pytest.raises(DuplicateAgentTypeNameError):
        service._resolve_agent_type_references()


def test_resolve_agent_type_references_resolves_string_reference(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # One profile has a real BaseAgentType; another references it by name (string).
    # The resolution code does: p_ref.agent_type = map[string]() where map[string] is
    # p_real (the profile). Since p_real is a MagicMock, calling it returns a child
    # MagicMock, so p_ref.agent_type is no longer the original string after resolution.
    at = _AgentTypeX()

    p_real = _make_agent_profile(at, set())
    p_ref = MagicMock()
    p_ref.agent_type = "agent_x"
    p_ref.agent_template = MagicMock()
    p_ref.agent_template.compatible_listener_types = set()

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real, p_ref]
    service._resolve_agent_type_references()
    # The string reference was replaced (agent_type is no longer the string "agent_x")
    assert p_ref.agent_type != "agent_x"


def test_resolve_agent_type_references_unresolvable_string_raises(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    p_ref = MagicMock()
    p_ref.agent_type = "nonexistent_agent_type"
    p_ref.agent_template = MagicMock()
    p_ref.agent_template.compatible_listener_types = set()

    agent_profiles_service.get_all_agent_profiles.return_value = [p_ref]
    with pytest.raises(UnresolvableAgentTypeReferenceError):
        service._resolve_agent_type_references()
