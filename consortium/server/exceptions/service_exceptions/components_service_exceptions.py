"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`ComponentsServiceError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentsServiceError]
        - [`ComponentLoadingError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentLoadingError]
            - [`InvalidComponentProjectManifestFileError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectManifestFileError]
                - [`InvalidComponentProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectManifestFileJSONError]
                - [`InvalidComponentProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectManifestFileSchemaError]
            - [`InvalidComponentProjectPyProjectFileError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectPyProjectFileError]
            - [`InvalidComponentProjectPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectPyProjectFileTOMLError]
            - [`InvalidComponentProjectPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectPyProjectFileDependencyError]
            - [`InvalidComponentProjectFolderStructureError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectFolderStructureError]
                - [`ComponentProjectManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentProjectManifestFileNotFoundError]
                - [`ComponentProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentProjectEntryPointModuleNotFoundError]
            - [`InvalidComponentProjectImplementationError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentProjectImplementationError]
                - [`ComponentProjectSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentProjectSymbolNotFoundError]
                - [`ComponentProjectInterfaceError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentProjectInterfaceError]
                - [`InternalComponentProjectError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InternalComponentProjectError]
            - [`IncompatibleComponentFrameworkVersionError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.IncompatibleComponentFrameworkVersionError]
            - [`ComponentAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentAlreadyRegisteredError]
            - [`DuplicateComponentLabelError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.DuplicateComponentLabelError]
        - [`ComponentDependencyError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentDependencyNotFoundError]
            - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.IncompatibleComponentDependencyVersionError]
            - [`ComponentDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentDependsOnInvalidComponentDependencyError]
            - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentDependencyNotRunningError]
        - [`ComponentNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class ComponentsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the components service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "COMPONENTS_SERVICE_ERROR"

    _COMPONENT_TYPE = "component"
    _MESSAGE_TEMPLATE = ""  # Holds the pure template string
    # Holds the template string that has the $COMPONENT_TYPE$ placeholder string
    # replaced by the particular component type.
    _MESSAGE = ""

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        super().__init__(message=self._MESSAGE.format(**kwargs))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._MESSAGE = cls._MESSAGE_TEMPLATE.replace(
            "$COMPONENT_TYPE$",
            cls._COMPONENT_TYPE.lower(),
        )


class ComponentLoadingError(ComponentsServiceError):
    """Base exception for all errors that occur during the loading of a component."""

    code = "COMPONENT_LOADING_ERROR"


class InvalidComponentProjectManifestFileError(ComponentLoadingError):
    """Base exception for all errors that occur due to an invalid component project manifest
    `manifest.json` file during component loading.
    """

    code = "INVALID_COMPONENT_PROJECT_MANIFEST_FILE_ERROR"


class InvalidComponentProjectManifestFileJSONError(
    InvalidComponentProjectManifestFileError,
):
    """Raised when the component project manifest file is not valid JSON during component
    loading.
    """

    code = "INVALID_COMPONENT_PROJECT_MANIFEST_FILE_JSON_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The $COMPONENT_TYPE$ project manifest file `manifest.json` is not a valid JSON "
        "file."
    )

    def __init__(self, component_project_folder: str):
        super().__init__(component_project_folder=component_project_folder)


class InvalidComponentProjectManifestFileSchemaError(
    InvalidComponentProjectManifestFileError,
):
    """Raised when the component project manifest file does not conform to the expected JSON
    schema during component loading.
    """

    code = "INVALID_COMPONENT_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The $COMPONENT_TYPE$ project manifest file `manifest.json` does not conform to the "
        "expected JSON schema. {json_schema_error_message}"
    )

    def __init__(self, component_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_project_folder=component_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidComponentProjectPyProjectFileError(ComponentLoadingError):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during component loading.
    """

    code = "INVALID_COMPONENT_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidComponentProjectPyProjectFileTOMLError(ComponentLoadingError):
    """Raised when the `pyproject.toml` file is not a valid TOML file during component loading."""

    code = "INVALID_COMPONENT_PROJECT_PYPROJECT_FILE_TOML_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The `pyproject.toml` file specified is not a valid TOML file."
    )

    def __init__(self, component_project_folder: str):
        super().__init__(component_project_folder=component_project_folder)


class InvalidComponentProjectPyProjectFileDependencyError(ComponentLoadingError):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    component loading.
    """

    code = "INVALID_COMPONENT_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The `pyproject.toml` file specified contains the invalid dependency "
        "entry '{invalid_dependency_entry}'. Check that the dependency "
        "parameter contains entries conforming to PEP 508."
    )

    def __init__(self, component_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_project_folder=component_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidComponentProjectFolderStructureError(ComponentLoadingError):
    """Base exception for all errors that occur due to an invalid component project folder
    structure during component loading.
    """

    code = "INVALID_COMPONENT_PROJECT_FOLDER_STRUCTURE_ERROR"


class ComponentProjectManifestFileNotFoundError(
    InvalidComponentProjectFolderStructureError,
):
    """Raised when the component project manifest file is not found in the component project
    folder during component loading.
    """

    code = "COMPONENT_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The $COMPONENT_TYPE$ project manifest file `manifest.json` was not found in the "
        "$COMPONENT_TYPE$ project folder. Create a `manifest.json` file in the root "
        "directory of the folder containing your $COMPONENT_TYPE$."
    )

    def __init__(self, component_project_folder: str):
        super().__init__(component_project_folder=component_project_folder)


class ComponentProjectEntryPointModuleNotFoundError(
    InvalidComponentProjectFolderStructureError,
):
    """Raised when the component entry point module specified in the manifest is not found in
    the component project folder during component loading.
    """

    code = "COMPONENT_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The $COMPONENT_TYPE$ entry point module '{entry_point_module}' specified in the "
        "$COMPONENT_TYPE$ project's manifest file was not found. Check that the module "
        "specified in the entry point parameter exists."
    )

    def __init__(self, component_project_folder: str, entry_point_module: str):
        super().__init__(
            component_project_folder=component_project_folder,
            entry_point_module=entry_point_module,
        )


class InvalidComponentProjectImplementationError(ComponentLoadingError):
    """Base exception for all errors that occur due to the component project not implementing
    the required interface during component loading.
    """

    code = "INVALID_COMPONENT_PROJECT_IMPLEMENTATION_ERROR"


class ComponentProjectSymbolNotFoundError(InvalidComponentProjectImplementationError):
    """Raised when the component symbol name specified in the manifest is not found in the
    component entry point module during component loading.
    """

    code = "COMPONENT_PROJECT_SYMBOL_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load $COMPONENT_TYPE$ project at '{component_project_folder}'. The "
        "entry point symbol '{entry_point_symbol}' specified in the $COMPONENT_TYPE$ project's "
        "manifest file was not found in the $COMPONENT_TYPE$ entry point module "
        "'{entry_point_module}'. Check that the class specified in the `entry_points` "
        "parameter exists for the module specified."
    )

    def __init__(
        self,
        component_project_folder: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class ComponentProjectInterfaceError(InvalidComponentProjectImplementationError):
    """Raised when the component class does not implement the required interface during
    component loading.
    """

    code = "COMPONENT_PROJECT_INTERFACE_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ project at '{component_project_folder}'. "
        "The entry point symbol '{entry_point_symbol}' in the $COMPONENT_TYPE$ project does "
        "not implement the required interface. Check that the symbol specified "
        "inherits from the appropriate base class."
    )

    def __init__(
        self,
        component_project_folder: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            entry_point_symbol=entry_point_symbol,
        )


class InternalComponentProjectError(InvalidComponentProjectImplementationError):
    """Raised when an unhandled exception from within the component is raised during component
    loading.
    """

    code = "INTERNAL_COMPONENT_PROJECT_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load $COMPONENT_TYPE$ project at '{component_project_folder}'. An "
        "exception occurred while loading the $COMPONENT_TYPE$: {internal_error_message}"
    )

    def __init__(
        self,
        component_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            internal_error_message=internal_error_message,
        )


class IncompatibleComponentFrameworkVersionError(ComponentLoadingError):
    """Raised when a component's required framework version is incompatible with the current
    framework version during component loading.
    """

    code = "INCOMPATIBLE_COMPONENT_FRAMEWORK_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ {component_str}. The $COMPONENT_TYPE$ requires a "
        "framework version of '{required_version}' which is incompatible "
        "with the current framework version '{current_version}'."
    )

    def __init__(
        self,
        component_str: str,
        required_version: str,
        current_version: str,
    ):
        super().__init__(
            component_str=component_str,
            required_version=required_version,
            current_version=current_version,
        )


class ComponentAlreadyRegisteredError(ComponentLoadingError):
    """Raised when a component with the same ID is already registered in the components service
    during component loading.
    """

    code = "COMPONENT_ALREADY_REGISTERED_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to register the $COMPONENT_TYPE$ {component_str}. A $COMPONENT_TYPE$ with the same "
        "ID '{component_id}' has already been registered in the $COMPONENT_TYPE$s service."
    )

    def __init__(self, component_str: str, component_id: str):
        super().__init__(
            component_str=component_str,
            component_id=component_id,
        )


class DuplicateComponentLabelError(ComponentLoadingError):
    """Raised when the label provided in the component's definition is already in use by
    another component during component loading.
    """

    code = "DUPLICATE_COMPONENT_LABEL_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to register the $COMPONENT_TYPE$ {component_str}. A $COMPONENT_TYPE$ with the same "
        "label '{label}' has already been registered in the $COMPONENT_TYPE$s "
        "service. Check that you are not registering an already registered "
        "$COMPONENT_TYPE$ or that the $COMPONENT_TYPE$ you are registering has a unique label."
    )

    def __init__(self, component_str: str, label: str):
        super().__init__(
            component_str=component_str,
            label=label,
        )


class ComponentDependencyError(ComponentsServiceError):
    """Base exception for all errors that occur during the resolution of component
    dependencies.
    """

    code = "COMPONENT_DEPENDENCY_ERROR"


class ThirdPartyDependencyNotFoundError(ComponentDependencyError):
    """Raised when a third-party dependency required by a component is not installed during
    component dependency resolution.
    """

    code = "THIRD_PARTY_DEPENDENCY_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ '{component_project_folder}' due to a dependency "
        "error. The third-party dependency '{third_party_dependency_name}' is required "
        "but not installed. Either install that dependency or remove it from the "
        "$COMPONENT_TYPE$'s definition."
    )

    def __init__(
        self,
        component_project_folder: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(ComponentDependencyError):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the component during component dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ '{component_project_folder}' due to a "
        "dependency error. The $COMPONENT_TYPE$ requires the third-party dependency "
        "'{third_party_dependency_name}' of version '{required_version}' but version "
        "'{installed_version}' was found. Either install the dependency of the correct "
        "version or change the dependency version in the $COMPONENT_TYPE$'s definition."
    )

    def __init__(
        self,
        component_project_folder: str,
        third_party_dependency_name: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            third_party_dependency_name=third_party_dependency_name,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependencyNotFoundError(ComponentDependencyError):
    """Raised when a component dependency required by the component is not found in the
    components service during component dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ {component_str} due to a dependency error. "
        "The component dependency '{missing_dependency}' is required but not "
        "installed. Either install that dependency or remove it from the $COMPONENT_TYPE$'s "
        "definition."
    )

    def __init__(
        self,
        component_str: str,
        missing_dependency: str,
    ):
        super().__init__(
            component_str=component_str,
            missing_dependency=missing_dependency,
        )


class IncompatibleComponentDependencyVersionError(ComponentDependencyError):
    """Raised when a component dependency's version is incompatible with the version required
    by the component during component dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ {component_str} due to a dependency error. "
        "The $COMPONENT_TYPE$ requires the component dependency '{incompatible_dependency}' of "
        "version '{required_version}' but version '{installed_version}' is installed. "
        "Either install the dependency of the correct version or change the dependency "
        "version in the $COMPONENT_TYPE$'s definition."
    )

    def __init__(
        self,
        component_str: str,
        incompatible_dependency: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_str=component_str,
            incompatible_dependency=incompatible_dependency,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependsOnInvalidComponentDependencyError(ComponentDependencyError):
    """Raised when a component depends on another component that itself has invalid dependencies
    during component dependency resolution.
    """

    code = "COMPONENT_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ {component_str} due to a dependency error. The "
        "component dependency '{invalid_dependency}' that the $COMPONENT_TYPE$ depends on is "
        "invalid."
    )

    def __init__(
        self,
        component_str: str,
        invalid_dependency: str,
    ):
        super().__init__(
            component_str=component_str,
            invalid_dependency=invalid_dependency,
        )


class ComponentDependencyNotRunningError(ComponentDependencyError):
    """Raised when a component dependency required by the component is present but not currently
    running during component dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ {component_str} due to a dependency error. The "
        "component dependency '{not_running_dependency}' that the $COMPONENT_TYPE$ depends on "
        "is installed but not currently running."
    )

    def __init__(
        self,
        component_str: str,
        not_running_dependency: str,
    ):
        super().__init__(
            component_str=component_str,
            not_running_dependency=not_running_dependency,
        )


class ComponentNotFoundError(ComponentsServiceError):
    """Raised when the requested component with the provided component ID was not found in the
    components service.
    """

    code = "COMPONENT_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to find the requested $COMPONENT_TYPE$. No $COMPONENT_TYPE$ was found with the "
        "provided $COMPONENT_TYPE$ ID '{component_id}'."
    )

    def __init__(self, component_id: str):
        super().__init__(component_id=component_id)
