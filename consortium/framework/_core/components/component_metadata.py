import sys
from dataclasses import dataclass
from typing import Any, get_type_hints

from packaging import requirements, specifiers, version
from pydantic import BaseModel, ValidationError

from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    EmptyComponentLabelError,
    InvalidComponentConfigurationParameterTypeError,
    InvalidComponentDependencyVersionSpecifierError,
    InvalidComponentVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingComponentConfigurationParameterError,
)


# A per-domain set of the configuration exception classes raised while validating component
# metadata. `_validate_metadata` raises from this set (via cls._component_metadata_exceptions
# .<slot>) so a domain (plugins, event hooks, agent templates, listener templates) can surface
# its own framework exception types directly, without a base class catching the generic error
# and remapping it into a domain error.
#
# Every slot defaults to the generic component framework exception, so a domain that does not
# override a slot transparently raises the generic type. A domain opts in by constructing a
# ComponentMetadataExceptions with the slots it wants replaced by its own subclasses.
@dataclass(frozen=True)
class ComponentMetadataExceptions:
    missing_configuration_parameter: type[
        MissingComponentConfigurationParameterError
    ] = MissingComponentConfigurationParameterError
    invalid_configuration_parameter_type: type[
        InvalidComponentConfigurationParameterTypeError
    ] = InvalidComponentConfigurationParameterTypeError
    empty_label: type[EmptyComponentLabelError] = EmptyComponentLabelError
    invalid_version: type[InvalidComponentVersionError] = InvalidComponentVersionError
    invalid_framework_version_specifier: type[InvalidFrameworkVersionSpecifierError] = (
        InvalidFrameworkVersionSpecifierError
    )
    invalid_dependency_version_specifier: type[
        InvalidComponentDependencyVersionSpecifierError
    ] = InvalidComponentDependencyVersionSpecifierError


class ComponentMetadataModel(BaseModel):
    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] = set()
    component_dependencies: set[str] = set()


class ComponentMetadata:
    _METADATA_MODEL = ComponentMetadataModel
    # The set of configuration exceptions raised while validating this component's metadata.
    # Defaults to the generic component framework exceptions; a domain base class overrides
    # slots with its own subclasses so domain errors are raised directly instead of being
    # remapped by the base class.
    _component_metadata_exceptions = ComponentMetadataExceptions()

    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] | None = None
    component_dependencies: set[str] | None = None

    @classmethod
    def _get_metadata_fields(cls) -> dict[str, Any]:
        return {
            key: getattr(cls, key)
            for key in cls._METADATA_MODEL.model_fields.keys()
            if hasattr(cls, key)
        }

    @classmethod
    def _validate_metadata(cls):
        cls.authors = cls.authors or set()
        cls.component_dependencies = cls.component_dependencies or set()
        # Third-party dependencies get added in when the component is loaded if it
        # declared any in its `pyproject.toml` file
        cls.third_party_dependencies = set()

        # Use the module filepath as a reference to the component if its label is not
        # defined
        component_str = (
            cls.label
            if hasattr(cls, "label")
            else f"{cls.__name__} ({sys.modules[cls.__module__].__file__})"
        )
        expected_attrs_and_types_map = get_type_hints(cls)

        # Check all attributes exist
        for attr in expected_attrs_and_types_map.keys():
            if not hasattr(cls, attr):
                raise cls._component_metadata_exceptions.missing_configuration_parameter(
                    component_str=component_str,
                    parameter_name=attr,
                )

        # Check all class attributes are of the expected type
        try:
            cls._METADATA_MODEL(
                **cls._get_metadata_fields(),
            )
        except ValidationError as exc:
            errors = exc.errors()
            # A field level error carries the offending field name in loc[0]. A model
            # level error has an empty loc, so fall back to the first declared field
            # rather than indexing into nothing.
            loc = errors[0]["loc"] if errors else ()
            attr = loc[0] if loc else next(iter(cls._get_metadata_fields()), "label")
            raise cls._component_metadata_exceptions.invalid_configuration_parameter_type(
                component_str=component_str,
                parameter_name=str(attr),
                parameter_type=str(expected_attrs_and_types_map.get(attr, attr)),
            ) from None

        # Perform semantic checking of specific attributes and reassign as needed
        if not cls.label:
            raise cls._component_metadata_exceptions.empty_label(
                component_filepath=sys.modules[cls.__module__].__file__,
            )
        cls.name = cls.label if cls.name is None else cls.name
        try:
            cls.version = version.Version(cls.version) if cls.version else None
        except version.InvalidVersion:
            raise cls._component_metadata_exceptions.invalid_version(
                component_str=cls.label,
                version=cls.version,
            ) from None
        try:
            cls.compatible_framework_version = (
                specifiers.SpecifierSet(cls.compatible_framework_version)
                if cls.compatible_framework_version
                else None
            )
        except specifiers.InvalidSpecifier:
            raise cls._component_metadata_exceptions.invalid_framework_version_specifier(
                framework_version_specifier=cls.compatible_framework_version,
                component_str=cls.label,
            ) from None
        new_dependencies = set()
        for entry in cls.component_dependencies:
            try:
                new_dependencies.add(requirements.Requirement(entry))
            except requirements.InvalidRequirement:
                raise cls._component_metadata_exceptions.invalid_dependency_version_specifier(
                    component_str=cls.label,
                    invalid_dependency_entry=entry,
                ) from None

        cls.component_dependencies = new_dependencies
