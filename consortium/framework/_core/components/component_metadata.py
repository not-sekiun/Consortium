import sys
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
                raise MissingComponentConfigurationParameterError(
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
            raise InvalidComponentConfigurationParameterTypeError(
                component_str=component_str,
                parameter_name=str(attr),
                parameter_type=str(expected_attrs_and_types_map.get(attr, attr)),
            ) from None

        # Perform semantic checking of specific attributes and reassign as needed
        if not cls.label:
            raise EmptyComponentLabelError(
                component_filepath=sys.modules[cls.__module__].__file__,
            )
        cls.name = cls.label if cls.name is None else cls.name
        try:
            cls.version = version.Version(cls.version) if cls.version else None
        except version.InvalidVersion:
            raise InvalidComponentVersionError(
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
            raise InvalidFrameworkVersionSpecifierError(
                framework_version_specifier=cls.compatible_framework_version,
                component_str=cls.label,
            ) from None
        new_dependencies = set()
        for entry in cls.component_dependencies:
            try:
                new_dependencies.add(requirements.Requirement(entry))
            except requirements.InvalidRequirement:
                raise InvalidComponentDependencyVersionSpecifierError(
                    component_str=cls.label,
                    invalid_dependency_entry=entry,
                ) from None

        cls.component_dependencies = new_dependencies
