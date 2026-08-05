"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`ComponentsServiceError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentsServiceError]
        - [`ComponentLoadingError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentLoadingError]
            - [`InvalidComponentManifestFileError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentManifestFileError]
                - [`InvalidComponentManifestFileJSONError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentManifestFileJSONError]
                - [`InvalidComponentManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentManifestFileSchemaError]
            - [`InvalidComponentPyProjectFileError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentPyProjectFileError]
            - [`InvalidComponentPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentPyProjectFileTOMLError]
            - [`InvalidComponentPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentPyProjectFileDependencyError]
            - [`InvalidComponentDirectoryStructureError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentDirectoryStructureError]
                - [`ComponentManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentManifestFileNotFoundError]
                - [`ComponentEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentEntryPointModuleNotFoundError]
            - [`InvalidComponentImplementationError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InvalidComponentImplementationError]
                - [`ComponentSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentSymbolNotFoundError]
                - [`ComponentInterfaceError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentInterfaceError]
                - [`InternalComponentError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.InternalComponentError]
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
        - [`ComponentDiscoveryFileSystemError`][consortium.server.exceptions.service_exceptions.components_service_exceptions.ComponentDiscoveryFileSystemError]
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


class InvalidComponentManifestFileError(ComponentLoadingError):
    """Base exception for all errors that occur due to an invalid component manifest
    file during component loading.
    """

    code = "INVALID_COMPONENT_MANIFEST_FILE_ERROR"


class InvalidComponentManifestFileJSONError(
    InvalidComponentManifestFileError,
):
    """Raised when the component manifest file is not valid JSON during component
    loading.
    """

    code = "INVALID_COMPONENT_MANIFEST_FILE_JSON_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The $COMPONENT_TYPE$ manifest file is not a valid JSON "
        "file."
    )

    def __init__(self, component_directory: str):
        super().__init__(component_directory=component_directory)


class InvalidComponentManifestFileSchemaError(
    InvalidComponentManifestFileError,
):
    """Raised when the component manifest file does not conform to the expected JSON
    schema during component loading.
    """

    code = "INVALID_COMPONENT_MANIFEST_FILE_SCHEMA_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The $COMPONENT_TYPE$ manifest file does not conform to the "
        "expected JSON schema. {json_schema_error_message}"
    )

    def __init__(self, component_directory: str, json_schema_error_message: str):
        super().__init__(
            component_directory=component_directory,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidComponentPyProjectFileError(ComponentLoadingError):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during component loading.
    """

    code = "INVALID_COMPONENT_PYPROJECT_FILE_ERROR"


class InvalidComponentPyProjectFileTOMLError(ComponentLoadingError):
    """Raised when the `pyproject.toml` file is not a valid TOML file during component loading."""

    code = "INVALID_COMPONENT_PYPROJECT_FILE_TOML_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The `pyproject.toml` file provided is not a valid TOML file."
    )

    def __init__(self, component_directory: str):
        super().__init__(component_directory=component_directory)


class InvalidComponentPyProjectFileDependencyError(ComponentLoadingError):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    component loading.
    """

    code = "INVALID_COMPONENT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The `pyproject.toml` file provided contains the invalid dependency "
        "entry '{invalid_dependency_entry}'. Check that the dependency "
        "parameter contains entries conforming to PEP 508."
    )

    def __init__(self, component_directory: str, invalid_dependency_entry: str):
        super().__init__(
            component_directory=component_directory,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidComponentDirectoryStructureError(ComponentLoadingError):
    """Base exception for all errors that occur due to an invalid component directory
    structure during component loading.
    """

    code = "INVALID_COMPONENT_DIRECTORY_STRUCTURE_ERROR"


class ComponentManifestFileNotFoundError(
    InvalidComponentDirectoryStructureError,
):
    """Raised when the component manifest file is not found in the component
    directory during component loading.
    """

    code = "COMPONENT_MANIFEST_FILE_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The $COMPONENT_TYPE$ manifest file was not found in its "
        "root directory. Create a manifest file (`manifest.json`) in the root "
        "directory containing your $COMPONENT_TYPE$."
    )

    def __init__(self, component_directory: str):
        super().__init__(component_directory=component_directory)


class ComponentEntryPointModuleNotFoundError(
    InvalidComponentDirectoryStructureError,
):
    """Raised when the component entry point module specified in the manifest file is
    not found in the component directory during component loading.
    """

    code = "COMPONENT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The entry point module '{entry_point_module}' specified in the "
        "$COMPONENT_TYPE$ manifest file was not found. Check that the module "
        "specified in the entry point parameter exists."
    )

    def __init__(self, component_directory: str, entry_point_module: str):
        super().__init__(
            component_directory=component_directory,
            entry_point_module=entry_point_module,
        )


class InvalidComponentImplementationError(ComponentLoadingError):
    """Base exception for all errors that occur due to the component not implementing
    the required interface during component loading.
    """

    code = "INVALID_COMPONENT_IMPLEMENTATION_ERROR"


class ComponentSymbolNotFoundError(InvalidComponentImplementationError):
    """Raised when the component symbol name specified in the manifest file is not found
    in the component entry point module during component loading.
    """

    code = "COMPONENT_SYMBOL_NOT_FOUND_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load $COMPONENT_TYPE$ at '{component_directory}'. The "
        "entry point symbol '{entry_point_symbol}' specified in the $COMPONENT_TYPE$ "
        "manifest file was not found within the entry point module "
        "'{entry_point_module}'. Check that the class specified in the `entry_points` "
        "parameter exists for the module specified."
    )

    def __init__(
        self,
        component_directory: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_directory=component_directory,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class ComponentInterfaceError(InvalidComponentImplementationError):
    """Raised when the component class does not implement the required interface during
    component loading.
    """

    code = "COMPONENT_INTERFACE_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. "
        "The entry point symbol '{entry_point_symbol}' in the $COMPONENT_TYPE$ does "
        "not implement the required interface. Check that the symbol specified "
        "inherits from the appropriate base class."
    )

    def __init__(
        self,
        component_directory: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_directory=component_directory,
            entry_point_symbol=entry_point_symbol,
        )


class InternalComponentError(InvalidComponentImplementationError):
    """Raised when an unhandled exception from within the component is raised during component
    loading.
    """

    code = "INTERNAL_COMPONENT_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}'. An "
        "unhandled exception occurred while loading the $COMPONENT_TYPE$: "
        "{internal_error_message}"
    )

    def __init__(
        self,
        component_directory: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_directory=component_directory,
            internal_error_message=internal_error_message,
        )


class IncompatibleComponentFrameworkVersionError(ComponentLoadingError):
    """Raised when a component's required framework version is incompatible with the current
    framework version during component loading.
    """

    code = "INCOMPATIBLE_COMPONENT_FRAMEWORK_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ '{component_str}'. The $COMPONENT_TYPE$ "
        "requires a framework version of '{required_version}' which is incompatible "
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
        "Failed to register the $COMPONENT_TYPE$ '{component_str}'. A $COMPONENT_TYPE$ "
        "with the same ID '{component_id}' has already been registered in the "
        "$COMPONENT_TYPE$s service."
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
        "Failed to register the $COMPONENT_TYPE$ '{component_str}'. A $COMPONENT_TYPE$ "
        "with the same label '{label}' has already been registered in the "
        "$COMPONENT_TYPE$s service. Check that you are not registering an already "
        "registered $COMPONENT_TYPE$ or that the $COMPONENT_TYPE$ you are registering "
        "has a unique label."
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
        "Failed to load the $COMPONENT_TYPE$ '{component_directory}' due to a "
        "dependency error. The third-party dependency '{third_party_dependency_name}' "
        "is required but not installed. Either install that dependency or remove it "
        "from the $COMPONENT_TYPE$'s definition."
    )

    def __init__(
        self,
        component_directory: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_directory=component_directory,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(ComponentDependencyError):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the component during component dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"

    _MESSAGE_TEMPLATE = (
        "Failed to load the $COMPONENT_TYPE$ at '{component_directory}' due to a "
        "dependency error. The $COMPONENT_TYPE$ requires the third-party dependency "
        "'{third_party_dependency_name}' of version '{required_version}' but version "
        "'{installed_version}' was found. Either install the dependency of the correct "
        "version or change the dependency version in the $COMPONENT_TYPE$'s definition."
    )

    def __init__(
        self,
        component_directory: str,
        third_party_dependency_name: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_directory=component_directory,
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
        "Failed to load the $COMPONENT_TYPE$ '{component_str}' due to a dependency error. "
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
        "Failed to load the $COMPONENT_TYPE$ '{component_str}' due to a dependency error. "
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
        "Failed to load the $COMPONENT_TYPE$ '{component_str}' due to a dependency error. The "
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
        "Failed to load the $COMPONENT_TYPE$ '{component_str}' due to a dependency error. The "
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
        "Failed to find the requested $COMPONENT_TYPE$. No $COMPONENT_TYPE$ was found "
        "with the provided $COMPONENT_TYPE$ ID '{component_id}'."
    )

    def __init__(self, component_id: str):
        super().__init__(component_id=component_id)


class ComponentDiscoveryFileSystemError(ComponentsServiceError):
    """Raised when a recursive filesystem scan for components fails at the filesystem level.

    Covers the whole-directory scan performed while discovering components (for
    example, scanning a framework components directory to find every plugin,
    agent profile, event hook, or listener profile living under it), not the
    loading of an individual component that has already been found. A scan
    failure aborts discovery entirely, so it is never one of the per-component
    errors collected while a directory is being loaded.
    """

    code = "COMPONENT_DISCOVERY_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        # Bypasses ComponentsServiceError's templated $COMPONENT_TYPE$ message
        # construction (calls BaseServiceError.__init__ directly) because this error
        # is not about a single component, it is about the directory scan itself, and
        # it needs a populated `detail` which the templated pattern does not build.
        # This also plugs it into the shared `wrap_filesystem_errors` context manager
        # in `consortium.server.utils`, which calls `error_type(operation=, path=,
        # underlying_error=)`.
        BaseServiceError.__init__(
            self,
            message=(
                f"Failed to {operation} at the path '{path}'. The underlying "
                f"filesystem operation failed. {underlying_error}"
            ),
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )
