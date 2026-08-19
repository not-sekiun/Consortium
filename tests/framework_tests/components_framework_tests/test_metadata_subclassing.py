import pytest

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    InvalidAgentCapabilityConfigurationParameterTypeError,
)
from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    InvalidComponentConfigurationParameterTypeError,
)

from .mocks import (
    MockAgentCapability,
    MockAgentTemplate,
    MockEventHook,
    MockListenerTemplate,
    MockPlugin,
)
from .mocks.declarations import (
    DECLARED_DEPENDENCY,
    DECLARED_OPTION_DEFAULT,
    DECLARED_OPTION_NAME,
    DECLARED_VERSION,
)
from .mocks.mock_event_hook import DECLARED_EVENT_TYPE
from .mocks.mock_plugin import DECLARED_AUTOSTART

# Subclassing integrity for every user of the metadata declaration system.
#
# Subclassing a component class is a second pass through class definition time validation,
# against values the parent already normalized. That makes it the sharpest probe of
# whether the declaration system is self consistent, and it is a shape component authors
# reach for (a shared base class with common metadata, specialized per component).
#
# Three of the five domains fail this today and are marked xfail(strict=True), so the suite
# stays green while the failures stay visible. strict means these turn into failures the
# moment they start passing: fixing the declaration system is expected to require deleting
# the marks, not discovering later that they were quietly succeeding. See issue #42.

_BROKEN_BY_OPTIONS_REMAP = pytest.mark.xfail(
    strict=True,
    reason=(
        "#42: options is declared as a set and normalized to a dict in place, so a "
        "subclass is validated against its parent's normalized value and rejected"
    ),
)

# Each domain paired with the attribute that carries its identity, so a subclass can be
# given its own. The capability domain identifies components by `name`; the four
# ComponentMetadata domains use `label`.
_DOMAINS = [
    pytest.param(MockEventHook, "label", id="event_hook"),
    pytest.param(MockPlugin, "label", id="plugin"),
    pytest.param(
        MockListenerTemplate,
        "label",
        id="listener_template",
        marks=_BROKEN_BY_OPTIONS_REMAP,
    ),
    pytest.param(
        MockAgentTemplate,
        "label",
        id="agent_template",
        marks=_BROKEN_BY_OPTIONS_REMAP,
    ),
    pytest.param(
        MockAgentCapability,
        "name",
        id="agent_capability",
        marks=_BROKEN_BY_OPTIONS_REMAP,
    ),
]

_DOMAINS_WITH_OPTIONS = [
    domain for domain in _DOMAINS if domain.id != "event_hook" and domain.id != "plugin"
]


# Builds a subclass the way a component author would: inherit everything, redeclare only
# what makes this component its own.
def _subclass(parent, identity_attribute, suffix, **overrides):
    identity = f"{getattr(parent, identity_attribute)}.{suffix}"
    return type(
        f"{parent.__name__}_{suffix}",
        (parent,),
        {identity_attribute: identity, **overrides},
    )


# ---------------------------------------------------------------------------
# Integrity of the subclass
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS)
def test_a_subclass_of_a_declared_component_can_be_created(parent, identity_attribute):
    child = _subclass(parent, identity_attribute, "created")

    assert issubclass(child, parent)


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS)
def test_a_subclass_takes_its_own_identity(parent, identity_attribute):
    child = _subclass(parent, identity_attribute, "identity")

    assert getattr(child, identity_attribute) != getattr(parent, identity_attribute)


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS)
def test_a_subclass_inherits_undeclared_metadata_from_its_parent(
    parent,
    identity_attribute,
):
    child = _subclass(parent, identity_attribute, "inherits")

    assert child.description == parent.description
    assert child.authors == parent.authors


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS[:4])
def test_a_subclass_inherits_the_declared_version(parent, identity_attribute):
    # The capability domain declares no version, so this covers the four
    # ComponentMetadata domains only.
    child = _subclass(parent, identity_attribute, "version")

    assert str(child.version) == DECLARED_VERSION


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS[:4])
def test_a_subclass_inherits_the_declared_dependencies(parent, identity_attribute):
    child = _subclass(parent, identity_attribute, "dependencies")

    assert {str(entry) for entry in child.component_dependencies} == {
        DECLARED_DEPENDENCY
    }


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS[:4])
def test_a_subclass_can_override_a_declared_value(parent, identity_attribute):
    child = _subclass(parent, identity_attribute, "override", version="2.0.0")

    assert str(child.version) == "2.0.0"


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS[:4])
def test_overriding_in_a_subclass_leaves_the_parent_untouched(
    parent,
    identity_attribute,
):
    _subclass(parent, identity_attribute, "isolation", version="3.0.0")

    assert str(parent.version) == DECLARED_VERSION


@pytest.mark.parametrize(("parent", "identity_attribute"), _DOMAINS_WITH_OPTIONS)
def test_a_subclass_inherits_options_reachable_by_name(parent, identity_attribute):
    child = _subclass(parent, identity_attribute, "options")

    assert child.options[DECLARED_OPTION_NAME].default_value == DECLARED_OPTION_DEFAULT


def test_an_event_hook_subclass_inherits_the_declared_event_types():
    child = _subclass(MockEventHook, "label", "event_types")

    # `subscribed_event_types` is live registration state read from the events service,
    # not the declaration, so it is not exercised here. See
    # tests/framework_tests/event_hooks_framework_tests/test_event_types.py.
    assert child.event_types == {DECLARED_EVENT_TYPE}


def test_a_plugin_subclass_inherits_the_declared_autostart():
    child = _subclass(MockPlugin, "label", "autostart")

    assert child.autostart is DECLARED_AUTOSTART


# ---------------------------------------------------------------------------
# The current failure, named
# ---------------------------------------------------------------------------

# CONTRACT (see issue #42): the xfail marks above record that three domains cannot be
# subclassed. These record *why*, so the cause is greppable rather than inferred from a
# mark. Expected to be deleted along with the marks when the declaration system stops
# normalizing in place.


@pytest.mark.parametrize(
    ("parent", "identity_attribute"),
    [
        pytest.param(MockListenerTemplate, "label", id="listener_template"),
        pytest.param(MockAgentTemplate, "label", id="agent_template"),
    ],
)
def test_component_subclassing_currently_fails_on_the_options_remap(
    parent,
    identity_attribute,
):
    with pytest.raises(InvalidComponentConfigurationParameterTypeError) as exc_info:
        _subclass(parent, identity_attribute, "cause")

    assert "options" in exc_info.value.message


def test_agent_capability_subclassing_currently_fails_on_the_options_remap():
    with pytest.raises(
        InvalidAgentCapabilityConfigurationParameterTypeError,
    ) as exc_info:
        _subclass(MockAgentCapability, "name", "cause")

    assert "options" in exc_info.value.message
