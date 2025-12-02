import importlib.metadata
import json
import pathlib
import tomllib
from typing import Any

import jsonschema
import loguru
import packaging.requirements as requirements
import packaging.version as version

from consortium.server.exceptions.service_exceptions.component_loader_service_exceptions import (
    ComponentProjectComponentFileNotFoundError,
    ComponentProjectInterfaceError,
    ComponentProjectManifestFileNotFoundError,
    ComponentProjectSymbolNotFoundError,
    IncompatibleComponentFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalComponentProjectError,
    InvalidComponentProjectManifestFileJSONError,
    InvalidComponentProjectManifestFileSchemaError,
    InvalidComponentProjectPyProjectFileDependencyError,
    InvalidComponentProjectPyProjectFileTOMLError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    SERVER_RELEASE,
)


class ComponentLoaderService:
    def __init__(
        self,
        component_logger: "loguru.Logger",
        component_name: str,
        component_type: type,
        component_framework_error: type[Exception],
    ):
        self._component_logger = component_logger
        self._component_name = component_name
        self._component_type = component_type
        self._component_framework_error = component_framework_error

    @staticmethod
    def _validate_manifest_json_file(
        component_project_folder: pathlib.Path,
    ) -> tuple[bool, str, str]:
        manifest_file_path = component_project_folder / "manifest.json"
        manifest_json_schema = {
            "type": "object",
            "properties": {
                "entry_point": {"type": "string"},
                "enabled": {"type": "boolean"},
            },
            "required": ["entry_point", "enabled"],
            "additionalProperties": False,
        }

        # Check if the manifest file exists and follows the correct JSON schema.
        try:
            with manifest_file_path.open(
                "r",
            ) as plugin_project_manifest_file:
                manifest_json = json.load(plugin_project_manifest_file)
                jsonschema.validate(
                    manifest_json,
                    manifest_json_schema,
                )
                enabled = manifest_json["enabled"]
                component_module, component_symbol = manifest_json["entry_point"].split(
                    ":",
                    1,
                )
                return enabled, component_module, component_symbol
        except FileNotFoundError:
            raise ComponentProjectManifestFileNotFoundError(
                component_project_folder=str(component_project_folder),
            )
        except json.JSONDecodeError:
            raise InvalidComponentProjectManifestFileJSONError(
                component_project_folder=str(component_project_folder),
            )
        except jsonschema.ValidationError as exc:
            raise InvalidComponentProjectManifestFileSchemaError(
                component_project_folder=str(component_project_folder),
                json_schema_error_message=exc.message,
            )

    @staticmethod
    def _check_component_enabled(
        enabled: bool,
        ignore_enabled_component_flag: bool,
    ) -> bool:
        # Check if the plugin project is enabled or not.
        if not enabled and not ignore_enabled_component_flag:
            return False
        return True

    @staticmethod
    def _validate_pyproject_toml_file_dependencies(
        component_project_folder: pathlib.Path,
    ) -> set[requirements.Requirement]:
        # Check for any third party dependencies declared by the plugin. If they exist
        # check that they are importable and of the correct version before finally
        # loading the entire plugin in.
        pyproject_toml = component_project_folder / "pyproject.toml"
        if pyproject_toml.exists():
            try:
                with pyproject_toml.open("r") as pyproject_toml_file:
                    pyproject_data = tomllib.loads(pyproject_toml_file.read())
            except tomllib.TOMLDecodeError:
                raise InvalidComponentProjectPyProjectFileTOMLError(
                    component_project_folder=str(component_project_folder),
                )
            dependency_entries = pyproject_data.get("project", {}).get(
                "dependencies",
                [],
            )
        else:
            dependency_entries = []

        dependencies = set()
        for entry in dependency_entries:
            try:
                # Check dependency entry is valid
                dependency = requirements.Requirement(entry)
                # Check dependency exists and is a compatible version without importing
                # the module.
                dependency_version = importlib.metadata.version(dependency.name)
                if dependency_version not in dependency.specifier:
                    raise IncompatibleThirdPartyDependencyVersionError(
                        component_project_folder=str(component_project_folder),
                        third_party_dependency_name=dependency.name,
                        required_version=str(dependency.specifier),
                        installed_version=dependency_version,
                    )
                dependencies.add(dependency)
            except importlib.metadata.PackageNotFoundError:
                raise ThirdPartyDependencyNotFoundError(
                    component_project_folder=str(component_project_folder),
                    third_party_dependency_name=dependency.name,
                )
            except requirements.InvalidRequirement:
                raise InvalidComponentProjectPyProjectFileDependencyError(
                    component_project_folder=str(component_project_folder),
                    invalid_dependency_entry=entry,
                )
        return dependencies

    def _validate_component_project_folder_structure(
        self,
        component_project_folder: pathlib.Path,
        component_module: str,
        component_symbol: str,
        dependencies: set[requirements.Requirement],
    ) -> type:
        # Check for a valid plugin project folder structure as specified by the
        # manifest file.
        component_file = pathlib.Path(
            component_project_folder,
            *component_module.split("."),
        )
        # Append .py suffix
        component_file = component_file.parent / (component_file.name + ".py")

        # Check if the file exists first, don't try-catch for `ImportError` because
        # these can be raised by missing third party dependencies instead of a missing
        # plugin file.
        if not component_file.exists():
            raise ComponentProjectComponentFileNotFoundError(
                component_file=str(component_file),
                component_project_folder=str(component_project_folder),
            )

        # Check for valid symbol names in the required plugin project file.
        component_module_path = ".".join(
            component_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]

        try:
            # Any import errors that arise should not be from third-party dependencies
            # because we checked for that earlier
            component_module = importlib.import_module(component_module_path)
            component_class = getattr(
                component_module,
                component_symbol,
            )
            component_class.third_party_dependencies = dependencies
            return component_class
        except AttributeError:
            raise ComponentProjectSymbolNotFoundError(
                symbol_name=component_symbol,
                component_project_folder=str(component_project_folder),
                component_file=str(component_file),
            )
        except self._component_framework_error as exc:
            raise exc from None
        # This should only catch errors that are not related to the plugin project.
        except Exception as exc:
            raise InternalComponentProjectError(
                component_project_folder=str(component_project_folder),
                internal_error_message=str(exc),
            )

    def _validate_component_class_inheritance(
        self,
        component_class: type,
        component_project_folder: pathlib.Path,
        component_symbol: str,
    ) -> Any:
        # Check for correct inheritance and instantiation of classes.
        if not issubclass(component_class, self._component_type):
            raise ComponentProjectInterfaceError(
                component_project_folder=str(component_project_folder),
                component_symbol=component_symbol,
            )
        try:
            component_object = component_class()
            return component_object
        except self._component_framework_error as exc:
            raise exc from None
        except Exception as exc:
            raise InternalComponentProjectError(
                component_project_folder=str(component_project_folder),
                internal_error_message=str(exc),
            )

    def _validate_component_framework_version_compatibility(
        self,
        component_object: Any,
    ) -> None:
        # Check the plugin's framework version compatibility if not specified, assume
        # it is compatible.
        if (
            component_object.compatible_framework_version
            and version.Version(SERVER_RELEASE.version)
            not in component_object.compatible_framework_version
        ):
            raise IncompatibleComponentFrameworkVersionError(
                component_str=str(component_object),
                required_version=str(
                    component_object.compatible_framework_version,
                ),
                current_version=SERVER_RELEASE.version,
            )

    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> type | None:
        enabled, component_module, component_symbol = self._validate_manifest_json_file(
            component_project_folder=component_project_folder,
        )
        if not self._check_component_enabled(
            enabled=enabled,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        ):
            self._component_logger.info(
                "Skipped loading {} from '{}' because it was disabled.",
                self._component_name,
                str(component_project_folder),
            )
            return None
        dependencies = self._validate_pyproject_toml_file_dependencies(
            component_project_folder=component_project_folder,
        )
        component_class = self._validate_component_project_folder_structure(
            component_project_folder=component_project_folder,
            component_module=component_module,
            component_symbol=component_symbol,
            dependencies=dependencies,
        )
        component_object = self._validate_component_class_inheritance(
            component_class=component_class,
            component_project_folder=component_project_folder,
            component_symbol=component_symbol,
        )
        self._validate_component_framework_version_compatibility(
            component_object=component_object,
        )
        self._component_logger.debug(
            "Retrieved {} {} from {} project folder: {}",
            self._component_name,
            repr(component_object),
            self._component_name,
            component_project_folder,
        )
        return component_object
