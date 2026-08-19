import pytest
from packaging import requirements, specifiers, version

from consortium.framework._core.components import (
    ComponentMetadata,
    ComponentMetadataDeclaration,
    ComponentMetadataExceptions,
    ComponentMetadataModel,
)
from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentConfigurationError,
    ComponentsFrameworkError,
    EmptyComponentLabelError,
    InvalidComponentConfigurationParameterTypeError,
    InvalidComponentDependencyVersionSpecifierError,
    InvalidComponentMetadataDeclarationError,
    InvalidComponentVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingComponentConfigurationParameterError,
    MissingComponentMetadataDeclarationError,
    UnknownComponentMetadataDeclarationError,
)

# Coverage for the shared metadata declaration machinery introduced by issue #42, before
# any real domain is moved onto it. Exercising it through a synthetic domain rather than
# through plugins or event hooks keeps these tests independent of what any one domain
# happens to declare, and lets the domain-specific parameter (`widget` below) stand in for
# whatever a real domain adds.

# ---------------------------------------------------------------------------
# A synthetic domain: declaration schema, model, exceptions and base class
# ---------------------------------------------------------------------------


class WidgetsFrameworkError(ComponentsFrameworkError):
    code = "WIDGETS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "widget"


class WidgetConfigurationError(ComponentConfigurationError, WidgetsFrameworkError):
    code = "WIDGET_CONFIGURATION_ERROR"


class MissingWidgetMetadataDeclarationError(
    MissingComponentMetadataDeclarationError,
    WidgetConfigurationError,
):
    code = "MISSING_WIDGET_METADATA_DECLARATION_ERROR"


class InvalidWidgetMetadataDeclarationError(
    InvalidComponentMetadataDeclarationError,
    WidgetConfigurationError,
):
    code = "INVALID_WIDGET_METADATA_DECLARATION_ERROR"


class UnknownWidgetMetadataDeclarationError(
    UnknownComponentMetadataDeclarationError,
    WidgetConfigurationError,
):
    code = "UNKNOWN_WIDGET_METADATA_DECLARATION_ERROR"


class MissingWidgetConfigurationParameterError(
    MissingComponentConfigurationParameterError,
    WidgetConfigurationError,
):
    code = "MISSING_WIDGET_CONFIGURATION_PARAMETER_ERROR"


class InvalidWidgetConfigurationParameterTypeError(
    InvalidComponentConfigurationParameterTypeError,
    WidgetConfigurationError,
):
    code = "INVALID_WIDGET_CONFIGURATION_PARAMETER_TYPE_ERROR"


class EmptyWidgetLabelError(EmptyComponentLabelError, WidgetConfigurationError):
    code = "EMPTY_WIDGET_LABEL_ERROR"


class InvalidWidgetVersionError(InvalidComponentVersionError, WidgetConfigurationError):
    code = "INVALID_WIDGET_VERSION_ERROR"


class InvalidWidgetFrameworkVersionSpecifierError(
    InvalidFrameworkVersionSpecifierError,
    WidgetConfigurationError,
):
    code = "INVALID_WIDGET_FRAMEWORK_VERSION_SPECIFIER_ERROR"


class InvalidWidgetDependencyVersionSpecifierError(
    InvalidComponentDependencyVersionSpecifierError,
    WidgetConfigurationError,
):
    code = "INVALID_WIDGET_DEPENDENCY_VERSION_SPECIFIER_ERROR"


class WidgetMetadata(ComponentMetadataDeclaration):
    widget: str = "default-widget"


class _WidgetMetadataModel(ComponentMetadataModel):
    widget: str = "default-widget"


class BaseWidget(ComponentMetadata):
    _component_metadata_declaration = WidgetMetadata
    _component_metadata_model = _WidgetMetadataModel
    _component_metadata_exceptions = ComponentMetadataExceptions(
        missing_configuration_parameter=MissingWidgetConfigurationParameterError,
        invalid_configuration_parameter_type=InvalidWidgetConfigurationParameterTypeError,
        empty_label=EmptyWidgetLabelError,
        invalid_version=InvalidWidgetVersionError,
        invalid_framework_version_specifier=InvalidWidgetFrameworkVersionSpecifierError,
        invalid_dependency_version_specifier=InvalidWidgetDependencyVersionSpecifierError,
        missing_metadata_declaration=MissingWidgetMetadataDeclarationError,
        invalid_metadata_declaration=InvalidWidgetMetadataDeclarationError,
        unknown_metadata_declaration=UnknownWidgetMetadataDeclarationError,
    )

    widget: str = "default-widget"

    def __init_subclass__(cls, **kwargs):
        cls._resolve_metadata()
        super().__init_subclass__(**kwargs)


# A second domain that overrides no exception slots, to check that a domain which opts out
# still raises the generic component types.
class GadgetMetadata(ComponentMetadataDeclaration):
    pass


class BaseGadget(ComponentMetadata):
    _component_metadata_declaration = GadgetMetadata

    def __init_subclass__(cls, **kwargs):
        cls._resolve_metadata()
        super().__init_subclass__(**kwargs)


DECLARED_LABEL = "consortium.widgets.declared"
DECLARED_VERSION = "1.2.3"
DECLARED_FRAMEWORK_VERSION = ">=0.1.0a1"
DECLARED_DEPENDENCY = "consortium.widgets.other==1.0.0"


# ---------------------------------------------------------------------------
# The nested Metadata class itself
# ---------------------------------------------------------------------------


def test_a_component_without_a_metadata_declaration_is_rejected():
    with pytest.raises(MissingWidgetMetadataDeclarationError) as exc_info:
        # Declaring metadata flat is the pre-#42 form, and is what an unmigrated component
        # looks like. It has to be rejected outright rather than silently resolving to
        # nothing.
        class UndeclaredWidget(BaseWidget):
            label = DECLARED_LABEL
            version = DECLARED_VERSION

    assert "does not declare a nested `Metadata` class" in str(exc_info.value)
    assert "WidgetMetadata" in str(exc_info.value)


def test_a_metadata_declaration_that_does_not_subclass_the_domain_schema_is_rejected():
    with pytest.raises(InvalidWidgetMetadataDeclarationError) as exc_info:

        class UnchainedWidget(BaseWidget):
            class Metadata:
                label = DECLARED_LABEL

    assert "must subclass `WidgetMetadata`" in str(exc_info.value)


def test_a_metadata_declaration_that_subclasses_the_wrong_domain_schema_is_rejected():
    with pytest.raises(InvalidWidgetMetadataDeclarationError):

        class WrongDomainWidget(BaseWidget):
            class Metadata(GadgetMetadata):
                label = DECLARED_LABEL


def test_a_metadata_declaration_that_is_not_a_class_is_rejected():
    with pytest.raises(InvalidWidgetMetadataDeclarationError):

        class NotAClassWidget(BaseWidget):
            Metadata = {"label": DECLARED_LABEL}


def test_an_unknown_metadata_parameter_is_rejected():
    with pytest.raises(UnknownWidgetMetadataDeclarationError) as exc_info:

        class TypoWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                label = DECLARED_LABEL
                # A typo the type checker cannot catch: a plain class accepts any
                # attribute name, so nothing but this check stands between the author and
                # a silently unset version.
                verison = DECLARED_VERSION

    message = str(exc_info.value)
    assert "`verison`" in message
    assert "`version`" in message


def test_a_private_name_in_a_metadata_declaration_is_not_a_parameter():
    # Authors sometimes build a declaration out of shared pieces. A private helper must
    # not be mistaken for a mistyped parameter.
    class PrivateHelperWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            _shared_authors = {"team"}

            label = DECLARED_LABEL
            authors = _shared_authors

    assert PrivateHelperWidget.authors == {"team"}


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def test_declared_metadata_resolves_onto_the_component():
    class ResolvedWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL
            name = "Resolved Widget"
            description = "A widget."
            version = DECLARED_VERSION
            compatible_framework_version = DECLARED_FRAMEWORK_VERSION
            component_dependencies = {DECLARED_DEPENDENCY}
            authors = {"test"}
            widget = "declared-widget"

    assert ResolvedWidget.label == DECLARED_LABEL
    assert ResolvedWidget.name == "Resolved Widget"
    assert ResolvedWidget.description == "A widget."
    assert ResolvedWidget.version == version.Version(DECLARED_VERSION)
    assert ResolvedWidget.compatible_framework_version == specifiers.SpecifierSet(
        DECLARED_FRAMEWORK_VERSION,
    )
    assert ResolvedWidget.component_dependencies == {
        requirements.Requirement(DECLARED_DEPENDENCY),
    }
    assert ResolvedWidget.authors == {"test"}
    assert ResolvedWidget.third_party_dependencies == set()
    # A domain parameter that needs no resolution is carried across as declared.
    assert ResolvedWidget.widget == "declared-widget"


def test_the_declaration_keeps_the_form_it_was_declared_in():
    # The point of the nested class: the declared value and the resolved value coexist,
    # each under its own name, so neither has to compromise its type for the other.
    class DeclaredFormWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL
            version = DECLARED_VERSION
            component_dependencies = {DECLARED_DEPENDENCY}

    assert DeclaredFormWidget.Metadata.version == DECLARED_VERSION
    assert isinstance(DeclaredFormWidget.Metadata.version, str)
    assert DeclaredFormWidget.Metadata.component_dependencies == {DECLARED_DEPENDENCY}
    assert isinstance(DeclaredFormWidget.version, version.Version)


def test_an_undeclared_parameter_falls_back_to_the_schema_default():
    class MinimalWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL

    assert MinimalWidget.description == ""
    assert MinimalWidget.version is None
    assert MinimalWidget.compatible_framework_version is None
    assert MinimalWidget.component_dependencies == set()
    assert MinimalWidget.authors == set()
    assert MinimalWidget.widget == "default-widget"


def test_an_undeclared_name_falls_back_to_the_label():
    class UnnamedWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL

    assert UnnamedWidget.name == DECLARED_LABEL


def test_the_resolved_declaration_is_returned_for_the_domain_to_finish():
    # Domains read the parameters only they know how to resolve (options, event types)
    # off this mapping rather than off the class, so they never see a half-resolved value.
    class ReturningWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL
            version = DECLARED_VERSION

    declared_metadata = ReturningWidget._resolve_metadata()

    assert declared_metadata["label"] == DECLARED_LABEL
    assert declared_metadata["version"] == DECLARED_VERSION
    assert declared_metadata["widget"] == "default-widget"


# ---------------------------------------------------------------------------
# Rejected declarations
# ---------------------------------------------------------------------------


def test_a_missing_required_parameter_is_rejected():
    with pytest.raises(MissingWidgetConfigurationParameterError) as exc_info:

        class LabellessWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                version = DECLARED_VERSION

    assert "`label`" in str(exc_info.value)


def test_an_empty_label_is_rejected():
    with pytest.raises(EmptyWidgetLabelError):

        class EmptyLabelWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                label = ""


def test_a_wrongly_typed_declaration_is_rejected():
    with pytest.raises(InvalidWidgetConfigurationParameterTypeError) as exc_info:

        class WronglyTypedWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                label = DECLARED_LABEL
                version = 1.23

    assert "`version`" in str(exc_info.value)


def test_an_invalid_version_is_rejected():
    with pytest.raises(InvalidWidgetVersionError):

        class BadVersionWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                label = DECLARED_LABEL
                version = "1.0.x"


def test_an_invalid_framework_version_specifier_is_rejected():
    with pytest.raises(InvalidWidgetFrameworkVersionSpecifierError):

        class BadFrameworkVersionWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                label = DECLARED_LABEL
                compatible_framework_version = "not a specifier"


def test_an_invalid_dependency_entry_is_rejected():
    with pytest.raises(InvalidWidgetDependencyVersionSpecifierError):

        class BadDependencyWidget(BaseWidget):
            class Metadata(WidgetMetadata):
                label = DECLARED_LABEL
                component_dependencies = {"not a requirement=="}


def test_a_domain_that_overrides_no_exception_slots_raises_the_generic_types():
    with pytest.raises(MissingComponentMetadataDeclarationError) as exc_info:

        class UndeclaredGadget(BaseGadget):
            label = DECLARED_LABEL

    # Specifically not a widget error: the slots are per domain, and a domain that opts
    # out gets the generic component type rather than another domain's.
    assert not isinstance(exc_info.value, WidgetsFrameworkError)


# ---------------------------------------------------------------------------
# Subclassing
# ---------------------------------------------------------------------------


@pytest.fixture
def parent_widget():
    class ParentWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL
            description = "The parent."
            version = DECLARED_VERSION
            compatible_framework_version = DECLARED_FRAMEWORK_VERSION
            authors = {"parent"}
            widget = "parent-widget"

    return ParentWidget


def test_a_subclass_chaining_its_parents_declaration_inherits_and_overrides(
    parent_widget,
):
    class ChildWidget(parent_widget):
        class Metadata(parent_widget.Metadata):
            label = "consortium.widgets.child"
            version = "2.0.0"

    assert ChildWidget.label == "consortium.widgets.child"
    assert ChildWidget.version == version.Version("2.0.0")
    # Inherited, not redeclared.
    assert ChildWidget.description == "The parent."
    assert ChildWidget.authors == {"parent"}
    assert ChildWidget.widget == "parent-widget"


def test_a_subclass_declaring_the_domain_schema_directly_still_inherits(parent_widget):
    # The merge walks the component MRO per parameter, so chaining the parent's
    # declaration is a convenience rather than a requirement. Both forms resolve alike.
    class ChildWidget(parent_widget):
        class Metadata(WidgetMetadata):
            label = "consortium.widgets.child"
            version = "2.0.0"

    assert ChildWidget.label == "consortium.widgets.child"
    assert ChildWidget.version == version.Version("2.0.0")
    assert ChildWidget.description == "The parent."
    assert ChildWidget.authors == {"parent"}
    assert ChildWidget.widget == "parent-widget"


def test_a_subclass_without_a_declaration_inherits_the_whole_declaration(parent_widget):
    class ChildWidget(parent_widget):
        pass

    assert ChildWidget.label == DECLARED_LABEL
    assert ChildWidget.version == version.Version(DECLARED_VERSION)
    assert ChildWidget.widget == "parent-widget"


def test_a_grandchild_inherits_through_two_levels(parent_widget):
    class ChildWidget(parent_widget):
        class Metadata(parent_widget.Metadata):
            version = "2.0.0"

    class GrandchildWidget(ChildWidget):
        class Metadata(ChildWidget.Metadata):
            authors = {"grandchild"}

    assert GrandchildWidget.label == DECLARED_LABEL
    assert GrandchildWidget.version == version.Version("2.0.0")
    assert GrandchildWidget.authors == {"grandchild"}
    assert GrandchildWidget.widget == "parent-widget"


def test_a_subclass_does_not_alter_its_parents_resolved_metadata(parent_widget):
    class ChildWidget(parent_widget):
        class Metadata(parent_widget.Metadata):
            label = "consortium.widgets.child"
            version = "2.0.0"

    assert parent_widget.label == DECLARED_LABEL
    assert parent_widget.version == version.Version(DECLARED_VERSION)


def test_resolution_is_idempotent(parent_widget):
    # The regression that opened #42: resolving a second time used to be handed the
    # already-resolved value and reject it against the declared type. Nothing here reads
    # a resolved value back, so repeat resolution is a no-op.
    parent_widget._resolve_metadata()
    parent_widget._resolve_metadata()

    assert parent_widget.version == version.Version(DECLARED_VERSION)
    assert parent_widget.compatible_framework_version == specifiers.SpecifierSet(
        DECLARED_FRAMEWORK_VERSION,
    )


def test_a_subclass_of_a_component_with_dependencies_keeps_them(parent_widget):
    class DependentWidget(BaseWidget):
        class Metadata(WidgetMetadata):
            label = DECLARED_LABEL
            component_dependencies = {DECLARED_DEPENDENCY}

    class ChildWidget(DependentWidget):
        class Metadata(DependentWidget.Metadata):
            label = "consortium.widgets.child"

    assert ChildWidget.component_dependencies == {
        requirements.Requirement(DECLARED_DEPENDENCY),
    }
