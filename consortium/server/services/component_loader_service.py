import graphlib
import importlib.metadata
import json
import pathlib
import tomllib
from typing import Any, Generic, TypeVar

import jsonschema
import packaging.requirements as requirements
import packaging.version as version

from consortium.server.exceptions.framework_exceptions.components_framework_exceptions import (
    ComponentConfigurationError,
)
from consortium.server.exceptions.service_exceptions.component_loader_service_exceptions import (
    ComponentDependencyError,
    ComponentDependencyNotFoundError,
    ComponentDependsOnInvalidComponentDependencyError,
    ComponentLoadingError,
    ComponentProjectComponentFileNotFoundError,
    ComponentProjectInterfaceError,
    ComponentProjectManifestFileNotFoundError,
    ComponentProjectSymbolNotFoundError,
    IncompatibleComponentDependencyVersionError,
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

ComponentType = TypeVar("ComponentType")


class ComponentLoaderService(Generic[ComponentType]):
    def __init__(
        self,
        component_type: type[ComponentType],
        component_framework_error: type[Exception],
    ):
        self._component_type = component_type
        self._component_framework_error = component_framework_error

    @staticmethod
    def _validate_manifest_json_file(
        component_project_folder: pathlib.Path,
        manifest_file_path: pathlib.Path,
        manifest_json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        # Check if the manifest file exists and follows the correct JSON schema.
        try:
            with manifest_file_path.open(
                "r",
            ) as component_project_manifest_file:
                manifest_json = json.load(component_project_manifest_file)
                jsonschema.validate(
                    manifest_json,
                    manifest_json_schema,
                )
                return manifest_json
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
    def _get_enabled_status_from_manifest_json(
        manifest_json: dict[str, Any],
    ) -> bool:
        return manifest_json["enabled"]

    @staticmethod
    def _get_entry_point_from_manifest_json(
        component_project_folder: pathlib.Path,
        manifest_json: dict[str, Any],
    ) -> tuple[str, str]:
        entry_point = manifest_json["entry_point"]
        if ":" not in entry_point:
            raise InvalidComponentProjectManifestFileSchemaError(
                component_project_folder=str(component_project_folder),
                json_schema_error_message=(
                    "The 'entry_point' field must be in the format "
                    "'module_path:SymbolName'."
                ),
            )
        component_module, component_symbol = entry_point.split(":", 1)
        return component_module, component_symbol

    @staticmethod
    def _validate_component_enabled(
        enabled: bool,
        ignore_enabled_component_flag: bool,
    ) -> bool:
        # Check if the component project is enabled or not.
        if not enabled and not ignore_enabled_component_flag:
            return False
        return True

    @staticmethod
    def _validate_pyproject_toml_file_third_party_dependencies(
        component_project_folder: pathlib.Path,
        pyproject_filepath: pathlib.Path,
    ) -> set[requirements.Requirement]:
        # Check for any third party dependencies declared by the component. If they exist
        # check that they are importable and of the correct version before finally
        # loading the entire component in.
        if pyproject_filepath.exists():
            try:
                with pyproject_filepath.open("r") as pyproject_toml_file:
                    pyproject_toml = tomllib.loads(pyproject_toml_file.read())
            except tomllib.TOMLDecodeError:
                raise InvalidComponentProjectPyProjectFileTOMLError(
                    component_project_folder=str(component_project_folder),
                )
            dependency_entries = pyproject_toml.get("project", {}).get(
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
    ) -> type[ComponentType]:
        # Check for a valid component project folder structure as specified by the
        # manifest file.
        component_file = pathlib.Path(
            component_project_folder,
            *component_module.split("."),
        )
        # Append .py suffix
        component_file = component_file.parent / (component_file.name + ".py")

        # Check if the file exists first, don't try-catch for `ImportError` because
        # these can be raised by missing third party dependencies instead of a missing
        # component file.
        if not component_file.exists():
            raise ComponentProjectComponentFileNotFoundError(
                component_file=str(component_file),
                component_project_folder=str(component_project_folder),
            )

        # Check for valid symbol names in the required component project file.
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
            return component_class
        except AttributeError:
            raise ComponentProjectSymbolNotFoundError(
                symbol_name=component_symbol,
                component_project_folder=str(component_project_folder),
                component_file=str(component_file),
            )
        except self._component_framework_error as exc:
            raise exc from None
        # This should only catch errors that are not related to the component project.
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
    ) -> ComponentType:
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

    @staticmethod
    def _validate_component_framework_version_compatibility(
        component_object: Any,
    ) -> None:
        # Check the component's framework version compatibility if not specified, assume
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
    ) -> ComponentType | None:
        manifest_json = self._validate_manifest_json_file(
            component_project_folder=component_project_folder,
            manifest_file_path=component_project_folder / "manifest.json",
            manifest_json_schema={
                "type": "object",
                "properties": {
                    "entry_point": {"type": "string"},
                    "enabled": {"type": "boolean"},
                },
                "required": ["entry_point", "enabled"],
                "additionalProperties": False,
            },
        )
        enabled = self._get_enabled_status_from_manifest_json(
            manifest_json=manifest_json,
        )
        component_module, component_symbol = self._get_entry_point_from_manifest_json(
            component_project_folder=component_project_folder,
            manifest_json=manifest_json,
        )
        if not self._validate_component_enabled(
            enabled=enabled,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        ):
            return None
        dependencies = self._validate_pyproject_toml_file_third_party_dependencies(
            component_project_folder=component_project_folder,
            pyproject_filepath=component_project_folder / "pyproject.toml",
        )
        component_class = self._validate_component_project_folder_structure(
            component_project_folder=component_project_folder,
            component_module=component_module,
            component_symbol=component_symbol,
        )
        component_class.third_party_dependencies = dependencies
        component_object = self._validate_component_class_inheritance(
            component_class=component_class,
            component_project_folder=component_project_folder,
            component_symbol=component_symbol,
        )
        self._validate_component_framework_version_compatibility(
            component_object=component_object,
        )
        return component_object

    def get_components_from_component_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[ComponentType],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]],
    ]:
        # Recursively search through the directory to find all component project
        # folders and returns them.
        component_project_folder_paths = []
        for path in directory.rglob("*"):
            if path.name != "manifest.json":
                continue
            component_project_folder_paths.append(path.parent)
        retrieved_components = []
        skipped_components = []
        errored_components = []
        for component_project_folder_path in component_project_folder_paths:
            try:
                component = self.get_component_from_component_project_folder(
                    component_project_folder=component_project_folder_path,
                    ignore_enabled_component_flag=ignore_enabled_component_flag,
                )
                if component:
                    retrieved_components.append(component)
                else:
                    skipped_components.append(component_project_folder_path)
            except (ComponentLoadingError, ComponentConfigurationError) as exc:
                errored_components.append((component_project_folder_path, exc))
        return retrieved_components, skipped_components, errored_components

    @staticmethod
    def validate_component_component_dependencies(
        component: ComponentType,
        registered_components: list[ComponentType],
    ) -> bool:
        label_registered_component_map = {
            registered_component.label: registered_component
            for registered_component in registered_components
        }
        for dependency in component.component_dependencies:
            # Check dependency exists
            if dependency.name not in label_registered_component_map:
                raise ComponentDependencyNotFoundError(
                    component_str=str(component),
                    missing_dependency=dependency.name,
                )
            if (
                label_registered_component_map[dependency.name].version
                and label_registered_component_map[dependency.name].version
                not in dependency.specifier
            ):
                raise IncompatibleComponentDependencyVersionError(
                    component_str=str(component),
                    incompatible_dependency=dependency.name,
                    required_version=str(dependency.specifier),
                    installed_version=str(
                        label_registered_component_map[dependency.name].version,
                    ),
                )
        return True

    def resolve_component_load_order(
        # TODO: abstract load order across plugins listeners event hooks and generators.
        #  ie an event hook depends on a listener and a plugin to be installed. Keep as
        #  `Any` for now
        self,
        components: list[ComponentType],
        already_loaded_components: list[Any],
    ) -> tuple[
        list[ComponentType],
        list[tuple[ComponentType, ComponentDependencyError]],
    ]:
        already_loaded_label_component_map = {
            component.label: component for component in already_loaded_components
        }
        current_batch_label_component_map = {
            component.label: component for component in components
        }

        # Extract all invalid components that cannot be loaded due to missing or
        # incompatible dependencies first. Run first past to construct DAG from only
        # the valid components.
        skipped_components = []
        valid_component_labels_dag = {}
        for component in components:
            # Check if all plugin dependencies for a component are available and of
            # compatible versions. If not, skip loading that plugin entirely. But
            # continue to try loading other plugins
            try:
                self.validate_component_component_dependencies(
                    component=component,
                    registered_components=already_loaded_components + components,
                )
                valid_component_labels_dag[component.label] = set()
                for dependency in component.component_dependencies:
                    # Skip adding a dependency to the DAG if it is already loaded.
                    if dependency.name in already_loaded_label_component_map:
                        continue
                    valid_component_labels_dag[component.label].add(dependency.name)
            except ComponentDependencyError as exc:
                skipped_components.append((component, exc))

        def in_skipped_components(
            label: str,
        ) -> bool:
            for component, _ in skipped_components:
                if component.label == label:
                    return True
            return False

        # Construct DAG from only the valid components to resolve component start
        # order. The nodes of the DAG are the labels of the plugins being loaded.
        while True:
            clean_pass = True
            for (
                component_label,
                dependency_labels,
            ) in valid_component_labels_dag.copy().items():
                for dep_label in dependency_labels:
                    if in_skipped_components(dep_label):
                        skipped_component = current_batch_label_component_map[
                            component_label
                        ]
                        skipped_components.append(
                            (
                                skipped_component,
                                ComponentDependsOnInvalidComponentDependencyError(
                                    component_str=str(skipped_component),
                                    invalid_dependency=dep_label,
                                ),
                            ),
                        )
                        del valid_component_labels_dag[component_label]
                        clean_pass = False
                        break
            if clean_pass:
                break

        # Check for cyclic dependencies in the dependency graph before proceeding to
        # load plugins. Cyclic dependencies abort the entire load process by raising
        # `graphlib.CycleError` which should be handled upwards.
        topological_sorter = graphlib.TopologicalSorter(valid_component_labels_dag)
        ordered_load_components = [
            current_batch_label_component_map[label]
            for label in topological_sorter.static_order()
        ]  # Construct order of plugins to load
        return ordered_load_components, skipped_components
