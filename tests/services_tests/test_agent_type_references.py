import pytest
from pydantic import ValidationError

from consortium.framework.agents.base_agent_generator import BaseAgentGenerator
from consortium.framework.agents.base_agent_template import (
    _AgentTemplateMetadataModel,
)
from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.server.services.component_loader_services.agent_profile_loader_service import (
    AgentProfileLoaderService,
)

# An agent type is carried as a `BaseAgentType` instance everywhere downstream of
# loading. A template may name another profile's agent type as a string instead of
# declaring a class, and that string has to survive template validation and loading
# intact so that `C2TypesService._resolve_agent_type_references` can turn it into the
# instance it names once every profile is in. These tests pin both ends of that: the
# string is accepted and left alone on the way in, and nothing but an instance comes
# out. The service-level half lives in `test_c2_types_service.py`.


# ---------------------------------------------------------------------------
# Minimal stand-ins
# ---------------------------------------------------------------------------


class _AgentType(BaseAgentType):
    name = "agent_x"
    agent_capabilities = set()


class _AgentGeneratorStub:
    pass


class _AgentTemplateStub:
    # Stands in for a loaded agent template class. `_post_validate_component_object`
    # only ever reaches for these three attributes and assigns through them.
    def __init__(self, agent_type):
        self.agent_type = agent_type
        self.agent_generator = _AgentGeneratorStub()
        self.compatible_listener_types = {"type_a"}


def _metadata_fields(**overrides):
    fields = {
        "label": "consortium.agents.stub",
        # `type[...]` admits the base class itself, which keeps these tests off the
        # subclassing machinery: it is the annotation being checked here, not the
        # component definition pipeline.
        "agent_generator": BaseAgentGenerator,
        "agent_type": _AgentType,
        "compatible_listener_types": set(),
        "options": set(),
        "validating_function": None,
    }
    fields.update(overrides)
    return fields


# ---------------------------------------------------------------------------
# Agent template metadata validation
# ---------------------------------------------------------------------------


def test_agent_template_metadata_accepts_an_agent_type_class():
    model = _AgentTemplateMetadataModel(**_metadata_fields())
    assert model.agent_type is _AgentType


def test_agent_template_metadata_accepts_an_agent_type_string_reference():
    # Rejecting the string here would kill the reference at class definition time,
    # before there is any other profile to resolve it against.
    model = _AgentTemplateMetadataModel(**_metadata_fields(agent_type="agent_x"))
    assert model.agent_type == "agent_x"


def test_agent_template_metadata_rejects_a_non_class_non_string_agent_type():
    with pytest.raises(ValidationError):
        _AgentTemplateMetadataModel(**_metadata_fields(agent_type=object()))


# ---------------------------------------------------------------------------
# AgentProfileLoaderService._post_validate_component_object
# ---------------------------------------------------------------------------


def test_loader_instantiates_an_agent_type_class():
    # The framework user declares the class; everything downstream expects an instance.
    template = _AgentTemplateStub(agent_type=_AgentType)

    profile = AgentProfileLoaderService._post_validate_component_object(
        component_object=template,
    )

    assert isinstance(profile.agent_type, _AgentType)
    assert profile.agent_type is template.agent_type
    assert profile.agent_generator.agent_type is template.agent_type


def test_loader_leaves_an_agent_type_string_reference_unresolved():
    # The profile this names may not be loaded yet, so the loader cannot resolve it.
    # Calling it instead of leaving it raises `TypeError: 'str' object is not callable`.
    template = _AgentTemplateStub(agent_type="agent_x")

    profile = AgentProfileLoaderService._post_validate_component_object(
        component_object=template,
    )

    assert profile.agent_type == "agent_x"
    assert template.agent_type == "agent_x"


def test_loader_does_not_raise_on_an_agent_type_string_reference():
    template = _AgentTemplateStub(agent_type="agent_x")

    # Guards the regression directly: this used to raise before the profile was ever
    # handed to the reference resolver.
    AgentProfileLoaderService._post_validate_component_object(
        component_object=template,
    )


def test_loader_copies_compatible_listener_types_onto_the_generator():
    # Compatibility is declared by the template, never by the agent type. The generator
    # gets its own copy of the reference; the agent type is left without one.
    template = _AgentTemplateStub(agent_type=_AgentType)

    profile = AgentProfileLoaderService._post_validate_component_object(
        component_object=template,
    )

    assert profile.agent_generator.compatible_listener_types == {"type_a"}
    assert not hasattr(profile.agent_type, "compatible_listener_types")
