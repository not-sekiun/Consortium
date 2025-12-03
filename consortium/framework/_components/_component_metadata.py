import sys
from typing import get_type_hints

from packaging import requirements, specifiers, version
from pydantic import BaseModel, ValidationError

from consortium.server.exceptions.framework_exceptions.components_framework_exceptions import (
    EmptyComponentLabelError,
    InvalidComponentConfigurationParameterTypeError,
    InvalidComponentDependencyVersionSpecifierError,
    InvalidComponentVersionError,
    InvalidFrameworkVersionSpecifierError,
    MissingComponentConfigurationParameterError,
)


class ComponentModel(BaseModel):
    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] = set()
    component_dependencies: set[str] = set()


class ComponentMetadata:
    _METADATA_MODEL = ComponentModel

    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] | None = None
    component_dependencies: set[str] | None = None

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
                label=cls.label,
                name=cls.name,
                description=cls.description,
                version=cls.version,
                compatible_framework_version=cls.compatible_framework_version,
                authors=cls.authors,
                component_dependencies=cls.component_dependencies,
            )
        except ValidationError as exc:
            attr = exc.errors()[0]["loc"][0]
            raise InvalidComponentConfigurationParameterTypeError(
                component_str=component_str,
                parameter_name=attr,
                parameter_type=str(expected_attrs_and_types_map[attr]),
            )

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
            )
        try:
            cls.compatible_framework_version = (
                specifiers.SpecifierSet(cls.compatible_framework_version)
                if cls.compatible_framework_version
                else None
            )
        except specifiers.InvalidSpecifier:
            raise InvalidFrameworkVersionSpecifierError(
                framework_version_specifier_str=cls.compatible_framework_version,
                component_str=cls.label,
            )
        new_dependencies = set()
        for entry in cls.component_dependencies:
            try:
                dependency = requirements.Requirement(entry)
            except requirements.InvalidRequirement:
                raise InvalidComponentDependencyVersionSpecifierError(
                    component_str=cls.label,
                    invalid_dependency_entry=entry,
                )
            new_dependencies.add(dependency)

        cls.component_dependencies = new_dependencies
