import graphlib
import importlib.metadata
import json
import pathlib
import sys
import tomllib
from typing import Any, TypeVar

import jsonschema
import packaging.requirements as requirements
import packaging.version as version

from consortium.framework._core.framework_exceptions.components_framework_exceptions import (
    ComponentConfigurationError,
)
from consortium.server.exceptions.service_exceptions.components_service_exceptions import (
    ComponentDependencyError,
    ComponentDependencyNotFoundError,
    ComponentDependsOnInvalidComponentDependencyError,
    ComponentLoadingError,
    ComponentProjectEntryPointModuleNotFoundError,
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
from consortium.server.services.release_service import ReleaseService

Component = TypeVar("Component")


# Default base service that loads components from component project folders. Expects to
# load a single component from each component project folder. Used by the plugins and
# event hooks system.
class ComponentLoaderService[Component]:
    _component_type: type[Component]
    # Domain-specific framework error(s) that can surface during import or
    # instantiation of a component. These are distinct from Component*Error, which
    # describes failures in the loader infrastructure itself (missing manifest,
    # bad entry point, etc.). Domain errors originate in the implementation being
    # loaded and carry their own precise semantics, so they must be re-raised
    # directly rather than wrapped as InternalComponentProjectError.
    _component_framework_error: type[Exception] | tuple[type[Exception], ...]
    _manifest_json_schema: dict[str, Any]

    def __init__(self, release_service: ReleaseService, consortium_root: pathlib.Path):
        self._consortium_root = consortium_root
        self._release = release_service.release

    @staticmethod
    def _get_manifest_json_file_path(
        component_project_folder: pathlib.Path,
    ) -> pathlib.Path:
        return component_project_folder / "manifest.json"

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
            ) from None
        except json.JSONDecodeError:
            raise InvalidComponentProjectManifestFileJSONError(
                component_project_folder=str(component_project_folder),
            ) from None
        except jsonschema.ValidationError as exc:
            raise InvalidComponentProjectManifestFileSchemaError(
                component_project_folder=str(component_project_folder),
                json_schema_error_message=exc.message,
            ) from None

    @staticmethod
    def _get_enabled_status_from_manifest_json(
        manifest_json: dict[str, Any],
    ) -> bool:
        return manifest_json["enabled"]

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
                    "'module_path:SymbolName'"
                ),
            )
        component_module, component_symbol = entry_point.split(":", 1)
        return component_module, component_symbol

    @staticmethod
    def _get_pyproject_toml_file_path(
        component_project_folder: pathlib.Path,
    ) -> pathlib.Path:
        return component_project_folder / "pyproject.toml"

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
                ) from None
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
                ) from None
            except requirements.InvalidRequirement:
                raise InvalidComponentProjectPyProjectFileDependencyError(
                    component_project_folder=str(component_project_folder),
                    invalid_dependency_entry=entry,
                ) from None
        return dependencies

    @staticmethod
    def _attach_third_party_dependencies_to_component_class(
        component_class: type[Component],
        dependencies: set[requirements.Requirement],
    ) -> type[Component]:
        component_class.third_party_dependencies = dependencies
        return component_class

    def _validate_component_project_folder_structure(
        self,
        component_project_folder: pathlib.Path,
        component_module: str,
        component_symbol: str,
    ) -> type[Component]:
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
            raise ComponentProjectEntryPointModuleNotFoundError(
                entry_point_module=str(component_file),
                component_project_folder=str(component_project_folder),
            )

        # Check for valid symbol names in the required component project file.
        component_module_path = ".".join(
            component_file.relative_to(self._consortium_root).parts
        )[: -len(".py")]

        # Check for exceptions that occur during import
        try:
            # Check to see if the module was already imported, if so reload it to get
            # latest changes.
            if component_module_path in sys.modules:
                component_module = importlib.reload(
                    sys.modules[component_module_path],
                )
            else:
                component_module = importlib.import_module(component_module_path)
        # Domain framework errors (e.g. a build step overriding a final method) are
        # raised via __init_subclass__ at class definition time, which fires during
        # import. Re-raise them directly so callers receive the precise domain error.
        except self._component_framework_error as exc:
            raise exc from None
        # This should only catch errors that are not related to the component project.
        except Exception as exc:
            raise InternalComponentProjectError(
                component_project_folder=str(component_project_folder),
                internal_error_message=str(exc),
            ) from None

        # Check to see if the symbol exists in the module
        try:
            component_class = getattr(
                component_module,
                component_symbol,
            )
            return component_class
        except AttributeError:
            raise ComponentProjectSymbolNotFoundError(
                entry_point_symbol=component_symbol,
                component_project_folder=str(component_project_folder),
                entry_point_module=str(component_file),
            ) from None

    @staticmethod
    def _get_component_framework_version_compatibility(
        component_class: type[Component],
    ) -> version.Version:
        return component_class.compatible_framework_version

    def _validate_component_framework_version_compatibility(
        self,
        component_class: type[Component],
    ) -> None:
        component_framework_version = (
            self._get_component_framework_version_compatibility(
                component_class=component_class,
            )
        )
        # Check the component's framework version compatibility if not specified, assume
        # it is compatible.
        if (
            component_framework_version
            and version.Version(self._release.version)
            not in component_framework_version
        ):
            raise IncompatibleComponentFrameworkVersionError(
                component_str=str(component_class),
                required_version=str(
                    component_class.compatible_framework_version,
                ),
                current_version=self._release.version,
            )

    def _validate_component_class(
        self,
        component_class: type,
        component_project_folder: pathlib.Path,
        component_symbol: str,
    ) -> Component:
        # Check for correct inheritance and instantiation of classes.
        if not issubclass(component_class, self._component_type):
            raise ComponentProjectInterfaceError(
                component_project_folder=str(component_project_folder),
                entry_point_symbol=component_symbol,
            )
        try:
            component_object = component_class()
            return component_object
        # Same reasoning as import: domain errors raised during instantiation are
        # precise and meaningful, not loader failures, so they must not be wrapped.
        except self._component_framework_error as exc:
            raise exc from None
        except Exception as exc:
            raise InternalComponentProjectError(
                component_project_folder=str(component_project_folder),
                internal_error_message=str(exc),
            ) from None

    @staticmethod
    def _post_validate_component_object(
        component_object: Component,
    ) -> Component:
        # Hook for any post validation steps that need to be performed on the component
        # class after all validation has been performed.
        return component_object

    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component | None:
        manifest_json = self._validate_manifest_json_file(
            component_project_folder=component_project_folder,
            manifest_file_path=self._get_manifest_json_file_path(
                component_project_folder=component_project_folder,
            ),
            manifest_json_schema=self._manifest_json_schema,
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
            pyproject_filepath=self._get_pyproject_toml_file_path(
                component_project_folder=component_project_folder,
            ),
        )
        component_class = self._validate_component_project_folder_structure(
            component_project_folder=component_project_folder,
            component_module=component_module,
            component_symbol=component_symbol,
        )
        component_class = self._attach_third_party_dependencies_to_component_class(
            component_class=component_class,
            dependencies=dependencies,
        )
        self._validate_component_framework_version_compatibility(
            component_class=component_class,
        )
        component_object = self._validate_component_class(
            component_class=component_class,
            component_project_folder=component_project_folder,
            component_symbol=component_symbol,
        )
        return self._post_validate_component_object(
            component_object=component_object,
        )

    def get_components_from_component_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[Component],
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
            except (
                ComponentLoadingError,
                ComponentConfigurationError,
                ComponentDependencyError,
            ) as exc:
                errored_components.append((component_project_folder_path, exc))
            # Domain framework errors escape the Component*Error hierarchy entirely,
            # so they need a separate clause to be collected rather than crashing
            # the batch load.
            except self._component_framework_error as exc:
                errored_components.append((component_project_folder_path, exc))
        return retrieved_components, skipped_components, errored_components

    @staticmethod
    def validate_component_component_dependencies(
        component: Component,
        registered_components: list[Component],
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
                ) from None
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
                ) from None
        return True

    def resolve_component_load_order(
        # TODO: abstract load order across plugins listeners event hooks and generators.
        #  ie an event hook depends on a listener and a plugin to be installed. Keep as
        #  `Any` for now
        self,
        components: list[Component],
        already_loaded_components: list[Any],
    ) -> tuple[
        list[Component],
        list[tuple[Component, ComponentDependencyError]],
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
