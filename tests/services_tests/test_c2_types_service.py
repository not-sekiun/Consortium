from unittest.mock import MagicMock

import pytest

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.service_exceptions.c2_types_service_exceptions import (
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


# Deliberately left without a `compatible_listener_types` attribute. `BaseAgentType`
# does not declare one, and these stubs previously added it so that the service could
# read it off the agent type. That hid the defect these tests now cover: compatibility
# is declared by the agent template, and reaching for it on the agent type raises
# `AttributeError` against any real agent type.
class _AgentTypeX(BaseAgentType):
    name = "agent_x"
    agent_capabilities = set()


class _AgentTypeY(BaseAgentType):
    name = "agent_y"
    agent_capabilities = set()


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
    profiles = [_make_agent_profile(at, {"type_a", "type_b"})]
    agent_profiles_service.get_all_agent_profiles.return_value = profiles
    result = service.get_compatible_listener_types_from_agent_type_name("agent_x")
    assert set(result) == {"type_a", "type_b"}


def test_get_compatible_listener_types_reads_the_template_not_the_agent_type(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # A real agent type has no `compatible_listener_types`, so a lookup that goes
    # through the agent type raises `AttributeError` rather than returning names.
    at = _AgentTypeX()
    assert not hasattr(at, "compatible_listener_types")

    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {"type_a"})
    ]
    assert service.get_compatible_listener_types_from_agent_type_name("agent_x") == [
        "type_a"
    ]


def test_get_compatible_listener_types_unions_across_templates(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # One agent type can be declared by more than one template, each with its own
    # compatible listener types. The result is the union of all of them.
    at = _AgentTypeX()
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {"type_a"}),
        _make_agent_profile(at, {"type_b"}),
    ]
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
    # Two templates declaring the same agent type and overlapping listener types must
    # not report the overlap twice.
    at = _AgentTypeX()
    profiles = [
        _make_agent_profile(at, {"type_a", "type_b"}),
        _make_agent_profile(at, {"type_a"}),
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = profiles
    result = service.get_compatible_listener_types_from_agent_type_name("agent_x")
    assert len(result) == len(set(result))
    assert set(result) == {"type_a", "type_b"}


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
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(lt)
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {"type_a"})
    ]
    assert service.are_c2_types_compatible("agent_x", "type_a") is True


def test_are_c2_types_compatible_matches_on_name_not_identity(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    # The template declares compatibility as a name. The listener type the service
    # resolves is a separate object that shares only that name, and `BaseListenerType`
    # defines no `__eq__`, so anything comparing objects here reports incompatible.
    at = _AgentTypeX()
    declared = _ListenerTypeA()
    resolved = _ListenerTypeA()
    assert declared is not resolved
    assert declared != resolved

    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(resolved)
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {declared.name})
    ]
    assert service.are_c2_types_compatible("agent_x", "type_a") is True


def test_are_c2_types_compatible_true_for_one_of_several_declared(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    at = _AgentTypeX()
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(_ListenerTypeA()),
        _make_listener_profile(_ListenerTypeB()),
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {"type_a", "type_b"})
    ]
    assert service.are_c2_types_compatible("agent_x", "type_a") is True
    assert service.are_c2_types_compatible("agent_x", "type_b") is True


def test_are_c2_types_compatible_false_for_undeclared_listener_type(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    at = _AgentTypeX()
    listener_profiles_service.get_all_listener_profiles.return_value = [
        _make_listener_profile(_ListenerTypeA()),
        _make_listener_profile(_ListenerTypeB()),
    ]
    agent_profiles_service.get_all_agent_profiles.return_value = [
        _make_agent_profile(at, {"type_a"})
    ]
    assert service.are_c2_types_compatible("agent_x", "type_b") is False


def test_are_c2_types_compatible_returns_false(
    service: C2TypesService,
    listener_profiles_service: MagicMock,
    agent_profiles_service: MagicMock,
):
    lt = _ListenerTypeA()
    at = _AgentTypeX()
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


def test_resolve_agent_type_references_resolves_to_an_agent_type_instance(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # One profile declares a real agent type, another references it by name. After
    # resolution the reference must read back as an actual `BaseAgentType` instance,
    # which is what every consumer of `agent_type` expects to find there.
    at = _AgentTypeX()
    p_real = _make_agent_profile(at, set())
    p_ref = _make_agent_profile("agent_x", set())

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real, p_ref]
    service._resolve_agent_type_references()

    assert isinstance(p_ref.agent_type, BaseAgentType)
    assert p_ref.agent_type.name == "agent_x"


def test_resolve_agent_type_references_shares_the_referenced_instance(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # The reference resolves to the very same object the referenced profile carries,
    # not to a second instance of its class. Agent types define no `__eq__`, so a
    # separate instance would be a different agent type to every consumer that
    # compares or deduplicates them.
    at = _AgentTypeX()
    p_real = _make_agent_profile(at, set())
    p_ref = _make_agent_profile("agent_x", set())

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real, p_ref]
    service._resolve_agent_type_references()

    assert p_ref.agent_type is at


def test_resolve_agent_type_references_deduplicates_after_resolution(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # The payoff of sharing the instance: a referencing profile does not make the same
    # agent type name show up twice in the registered agent types.
    at = _AgentTypeX()
    p_real = _make_agent_profile(at, set())
    p_ref = _make_agent_profile("agent_x", set())

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real, p_ref]
    service._resolve_agent_type_references()

    assert service.get_all_agent_types() == [at]


def test_resolve_agent_type_references_resolves_template_and_generator(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # The loader points the profile, its template and its generator at one agent type
    # object, so resolution has to move all three off the string. The generator matters
    # in particular: it calls `agent_type.to_json()` when it serializes itself.
    at = _AgentTypeX()
    p_real = _make_agent_profile(at, set())
    p_ref = _make_agent_profile("agent_x", set())

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real, p_ref]
    service._resolve_agent_type_references()

    assert p_ref.agent_template.agent_type is at
    assert p_ref.agent_generator.agent_type is at


def test_resolve_agent_type_references_leaves_resolved_profiles_alone(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    at = _AgentTypeX()
    p_real = _make_agent_profile(at, set())

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real]
    service._resolve_agent_type_references()

    assert p_real.agent_type is at


def test_resolve_agent_type_references_is_idempotent(
    service: C2TypesService, agent_profiles_service: MagicMock
):
    # The resolver runs again on every profile load, reload and unload, so it has to
    # tolerate being handed profiles it has already resolved.
    at = _AgentTypeX()
    p_real = _make_agent_profile(at, set())
    p_ref = _make_agent_profile("agent_x", set())

    agent_profiles_service.get_all_agent_profiles.return_value = [p_real, p_ref]
    service._resolve_agent_type_references()
    service._resolve_agent_type_references()

    assert p_ref.agent_type is at


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
