import pytest
from packaging import requirements, specifiers, version

from consortium.server.objects.mitre_attack_objects import MitreAttackTechnique

from .mocks import (
    MockAgentCapability,
    MockAgentTemplate,
    MockAgentType,
    MockEventHook,
    MockListenerTemplate,
    MockPlugin,
)
from .mocks.declarations import (
    DECLARED_AUTHORS,
    DECLARED_DEPENDENCY,
    DECLARED_DESCRIPTION,
    DECLARED_FRAMEWORK_VERSION,
    DECLARED_MITRE_TECHNIQUE,
    DECLARED_OPTION_DEFAULT,
    DECLARED_OPTION_NAME,
    DECLARED_VERSION,
)
from .mocks.mock_agent_template import DECLARED_AGENT_TYPE_NAME
from .mocks.mock_event_hook import DECLARED_EVENT_TYPE
from .mocks.mock_listener_template import DECLARED_LISTENER_TYPE_NAME
from .mocks.mock_plugin import DECLARED_AUTOSTART

# Regression coverage for the metadata declaration system, one mock component per domain.
# The point of this module is to make the blast radius of a change to that system visible:
# it asserts what a declaration means, so that a refactor either keeps these passing or
# tells you exactly which domain it changed.
#
# Assertions are written against the declared value in a form that does not depend on how
# the framework represents it internally (`str(version) == "0.1.0"` rather than
# `version == Version("0.1.0")`). The one exception is the "normalized shape" section at
# the bottom, which deliberately pins the current internal representation. See the note
# there.

# The four domains that inherit ComponentMetadata and so share the common metadata block.
# BaseAgentCapability is excluded: it carries a parallel implementation with a different
# field set (no label, no version) and is covered separately below.
_COMPONENT_METADATA_DOMAINS = [
    pytest.param(MockEventHook, id="event_hook"),
    pytest.param(MockPlugin, id="plugin"),
    pytest.param(MockListenerTemplate, id="listener_template"),
    pytest.param(MockAgentTemplate, id="agent_template"),
]


# ---------------------------------------------------------------------------
# Common metadata: every ComponentMetadata domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_declared_label_and_description_are_preserved(component):
    assert component.label
    assert component.description == DECLARED_DESCRIPTION


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_declared_name_is_preserved(component):
    # A declared name is kept as written. Metadata validation only substitutes the label
    # when no name was declared.
    assert component.name.startswith("Mock Metadata")


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_declared_version_is_readable_as_the_declared_value(component):
    assert str(component.version) == DECLARED_VERSION


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_declared_framework_version_is_readable_as_the_declared_value(component):
    assert str(component.compatible_framework_version) == DECLARED_FRAMEWORK_VERSION


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_declared_dependencies_are_readable_as_the_declared_values(component):
    assert {str(entry) for entry in component.component_dependencies} == {
        DECLARED_DEPENDENCY
    }


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_declared_authors_are_preserved(component):
    assert component.authors == set(DECLARED_AUTHORS)


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_third_party_dependencies_start_empty(component):
    # Populated by the loader from the component's pyproject.toml, so a class that was
    # never loaded declares none.
    assert component.third_party_dependencies == set()


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_root_directory_resolves_to_the_declaring_package(component):
    assert component.root_directory.name == "mocks"


# ---------------------------------------------------------------------------
# Domain specific metadata
# ---------------------------------------------------------------------------


def test_event_hook_declared_event_types_are_readable_as_the_declared_value():
    # `subscribed_event_types` is live registration state read from the events service,
    # not the declaration, so it is not exercised here. See
    # tests/framework_tests/event_hooks_framework_tests/test_event_types.py.
    assert MockEventHook.event_types == {DECLARED_EVENT_TYPE}


def test_plugin_declared_autostart_is_preserved():
    assert MockPlugin.autostart is DECLARED_AUTOSTART


def test_listener_template_declared_listener_and_type_are_preserved():
    assert MockListenerTemplate.listener_type.name == DECLARED_LISTENER_TYPE_NAME
    assert MockListenerTemplate.listener is not None


def test_agent_template_declared_agent_type_is_preserved():
    # Asserted by name rather than by identity: a declared agent type is resolved to a
    # shared instance once every agent profile is loaded, so identity against the declared
    # class only holds for a class that was never loaded.
    assert MockAgentTemplate.agent_type is MockAgentType
    assert MockAgentTemplate.agent_type.name == DECLARED_AGENT_TYPE_NAME


def test_agent_template_declared_compatible_listener_types_are_preserved():
    assert MockAgentTemplate.compatible_listener_types == {DECLARED_LISTENER_TYPE_NAME}


@pytest.mark.parametrize(
    "component",
    [
        pytest.param(MockListenerTemplate, id="listener_template"),
        pytest.param(MockAgentTemplate, id="agent_template"),
        pytest.param(MockAgentCapability, id="agent_capability"),
    ],
)
def test_declared_options_are_reachable_by_name(component):
    # Options are declared as a set and consumed by name. This asserts the lookup works,
    # not that it is backed by a dict.
    assert component.options[DECLARED_OPTION_NAME].default_value == (
        DECLARED_OPTION_DEFAULT
    )


@pytest.mark.parametrize(
    "component",
    [
        pytest.param(MockListenerTemplate, id="listener_template"),
        pytest.param(MockAgentCapability, id="agent_capability"),
    ],
)
def test_declared_validating_function_stays_callable_with_one_parameter(component):
    # Wrapped in a staticmethod during validation so it is not bound as a method. What
    # matters to callers is that it is still callable with the single parameter it was
    # declared with.
    assert component.validating_function({}) is None


# ---------------------------------------------------------------------------
# Agent capability: the parallel declaration system
# ---------------------------------------------------------------------------


def test_agent_capability_declared_name_and_description_are_preserved():
    assert MockAgentCapability.name
    assert MockAgentCapability.description == DECLARED_DESCRIPTION


def test_agent_capability_declared_authors_are_preserved():
    assert MockAgentCapability.authors == set(DECLARED_AUTHORS)


def test_agent_capability_declared_supported_oses_are_preserved():
    assert len(MockAgentCapability.supported_oses) == 1


def test_agent_capability_declared_mitre_techniques_resolve():
    (technique,) = MockAgentCapability.mitre_attack_techniques
    assert isinstance(technique, MitreAttackTechnique)
    assert technique.mitre_attack_technique_id == DECLARED_MITRE_TECHNIQUE


def test_agent_capability_undeclared_metadata_takes_its_default():
    assert MockAgentCapability.requires_admin is False


# ---------------------------------------------------------------------------
# Normalized shape
# ---------------------------------------------------------------------------

# CONTRACT (see issue #42): these pin the *current* internal representation, which is not
# the type the attribute was declared as. They are the checklist for the metadata
# declaration rework: an option that stops normalizing in place is expected to change
# every assertion below, and only these. Nothing above this line should need to change.


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_version_currently_normalizes_to_a_packaging_version(component):
    assert isinstance(component.version, version.Version)


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_framework_version_currently_normalizes_to_a_specifier_set(component):
    assert isinstance(component.compatible_framework_version, specifiers.SpecifierSet)


@pytest.mark.parametrize("component", _COMPONENT_METADATA_DOMAINS)
def test_dependencies_currently_normalize_to_requirements(component):
    assert all(
        isinstance(entry, requirements.Requirement)
        for entry in component.component_dependencies
    )


@pytest.mark.parametrize(
    "component",
    [
        pytest.param(MockListenerTemplate, id="listener_template"),
        pytest.param(MockAgentTemplate, id="agent_template"),
        pytest.param(MockAgentCapability, id="agent_capability"),
    ],
)
def test_options_currently_normalize_from_a_set_to_a_dict(component):
    assert isinstance(component.options, dict)


@pytest.mark.parametrize(
    "component",
    [
        pytest.param(MockListenerTemplate, id="listener_template"),
        pytest.param(MockAgentCapability, id="agent_capability"),
    ],
)
def test_validating_function_currently_normalizes_to_a_staticmethod(component):
    assert isinstance(component.__dict__["validating_function"], staticmethod)


def test_event_types_currently_normalize_to_a_frozenset_of_strings():
    assert isinstance(MockEventHook.event_types, frozenset)
    assert all(isinstance(entry, str) for entry in MockEventHook.event_types)


def test_mitre_techniques_currently_normalize_from_a_set_to_a_list():
    assert isinstance(MockAgentCapability.mitre_attack_techniques, list)
