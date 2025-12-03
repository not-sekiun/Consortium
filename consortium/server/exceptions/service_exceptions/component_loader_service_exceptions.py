from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ComponentsLoaderServiceError(BaseServiceException):
    _COMPONENT_TYPE = "component"
    _MESSAGE_TEMPLATE = ""  # Holds the pure template string
    # Holds the template string that has the $C_LOWER$ and $C_CAPITAL$ replaced by the
    # particular component type.
    _MESSAGE = ""

    def __init__(self, **kwargs):
        self.exc_kwargs = kwargs
        super().__init__(message=self._MESSAGE.format(**kwargs))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        component_lower = cls._COMPONENT_TYPE.lower()
        component_capital = cls._COMPONENT_TYPE.capitalize()
        cls._MESSAGE = cls._MESSAGE_TEMPLATE.replace(
            "$C_LOWER$",
            component_lower,
        ).replace(
            "$C_CAPITAL$",
            component_capital,
        )


class ComponentLoadingError(ComponentsLoaderServiceError): ...


class InvalidComponentProjectManifestFileError(ComponentLoadingError): ...


class InvalidComponentProjectManifestFileJSONError(
    InvalidComponentProjectManifestFileError,
):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The $C_LOWER$ project manifest file 'manifest.json' is not a valid JSON "
        "file."
    )

    def __init__(self, component_project_folder: str):
        super().__init__(component_project_folder=component_project_folder)


class InvalidComponentProjectManifestFileSchemaError(
    InvalidComponentProjectManifestFileError,
):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The $C_LOWER$ project manifest file 'manifest.json' failed JSON schema "
        "validation: {json_schema_error_message}"
    )

    def __init__(self, component_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_project_folder=component_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidComponentProjectPyProjectFileError(ComponentLoadingError): ...


class InvalidComponentProjectPyProjectFileTOMLError(ComponentLoadingError):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The 'pyproject.toml' file specified is not a valid TOML file."
    )

    def __init__(self, component_project_folder: str):
        super().__init__(component_project_folder=component_project_folder)


class InvalidComponentProjectPyProjectFileDependencyError(ComponentLoadingError):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The 'pyproject.toml' file specified contains the invalid dependency "
        "entry '{invalid_dependency_entry}'. Check that the dependency "
        "parameter contains entries conforming to PEP 508."
    )

    def __init__(self, component_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_project_folder=component_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidComponentProjectFolderStructureError(ComponentLoadingError): ...


class ComponentProjectManifestFileNotFoundError(
    InvalidComponentProjectFolderStructureError,
):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The $C_LOWER$ project manifest file 'manifest.json' was not found in the "
        "$C_LOWER$ project folder. Create a 'manifest.json' file in the root "
        "directory of the folder containing your $C_LOWER$."
    )

    def __init__(self, component_project_folder: str):
        super().__init__(component_project_folder=component_project_folder)


class ComponentProjectComponentFileNotFoundError(
    InvalidComponentProjectFolderStructureError,
):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The $C_LOWER$ file '{component_file}' specified in the $C_LOWER$ project's "
        "manifest file was not found. Check that the module specified in the "
        "`entry_points` parameter exists."
    )

    def __init__(self, component_project_folder: str, component_file: str):
        super().__init__(
            component_project_folder=component_project_folder,
            component_file=component_file,
        )


class InvalidComponentProjectImplementationError(ComponentLoadingError): ...


class ComponentProjectSymbolNotFoundError(InvalidComponentProjectImplementationError):
    _MESSAGE_TEMPLATE = (
        "Failed to load $C_LOWER$ project at '{component_project_folder}'. The "
        "symbol name '{symbol_name}' specified in the $C_LOWER$ project's "
        "manifest file was not found in the $C_LOWER$ file '{component_file}'. "
        "Check that the class specified in the `entry_points` parameter exists"
        "for the module specified."
    )

    def __init__(
        self,
        component_project_folder: str,
        symbol_name: str,
        component_file: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            symbol_name=symbol_name,
            component_file=component_file,
        )


class ComponentProjectInterfaceError(InvalidComponentProjectImplementationError):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ project at '{component_project_folder}'. "
        "The $C_LOWER$ in the $C_LOWER$ project does not implement the required "
        "interface for its defined symbol '{component_symbol}'. Check that the "
        "$C_LOWER$ class inherits from `Base$C_CAPITAL$`."
    )

    def __init__(
        self,
        component_project_folder: str,
        component_symbol: str,
    ):
        super().__init__(
            component_project_folder=component_project_folder,
            component_symbol=component_symbol,
        )


class InternalComponentProjectError(InvalidComponentProjectImplementationError):
    _MESSAGE_TEMPLATE = (
        "Failed to load $C_LOWER$ project at '{component_project_folder}'. An "
        "exception occurred while loading the $C_LOWER$: {internal_error_message}"
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
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ {component_str}. The $C_LOWER$ requires a "
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
    _MESSAGE_TEMPLATE = (
        "Failed to register the $C_LOWER$ '{component_str}'. A $C_LOWER$ with the same "
        "ID '{component_id}' has already been registered in the $C_LOWER$s service."
    )

    def __init__(self, component_str: str, component_id: str):
        super().__init__(
            component_str=component_str,
            component_id=component_id,
        )


class DuplicateComponentLabelError(ComponentLoadingError):
    _MESSAGE_TEMPLATE = (
        "Failed to register the $C_LOWER$ '{component_str}'. A $C_LOWER$ with the same "
        "label '{label}' has already been registered in the $C_LOWER$s "
        "service. Check that you are not registering an already registered "
        "$C_LOWER$ or that the $C_LOWER$ you are registering has a unique label."
    )

    def __init__(self, component_str: str, label: str):
        super().__init__(
            component_str=component_str,
            label=label,
        )


class InternalComponentStartError(ComponentLoadingError):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ '{component_str}'. An exception occurred "
        "while starting the $C_LOWER$: {internal_error_message}"
    )

    def __init__(self, component_str: str, internal_error_message: str):
        super().__init__(
            component_str=component_str,
            internal_error_message=internal_error_message,
        )


class ComponentDependencyError(ComponentsLoaderServiceError): ...


class ThirdPartyDependencyNotFoundError(ComponentDependencyError):
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ '{component_project_folder}' due to a dependency "
        "error. The third-party dependency '{third_party_dependency_name}' is required "
        "but not installed. Either install that dependency or remove it from the "
        "$C_LOWER$'s definition."
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
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ '{component_project_folder}' due to a "
        "dependency error. The $C_LOWER$ requires the third-party dependency "
        "'{third_party_dependency_name}' of version '{required_version}' but version "
        "'{installed_version}' was found. Either install the dependency of the correct "
        "version or change the dependency version in the $C_LOWER$'s definition."
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
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ {component_str} due to a dependency error. "
        "The component dependency '{missing_dependency}' is required but not "
        "installed. Either install that dependency or remove it from the $C_LOWER$'s "
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
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ {component_str} due to a dependency error. "
        "The $C_LOWER$ requires the component dependency '{incompatible_dependency}' of "
        "version '{required_version}' but version '{installed_version}' is installed. "
        "Either install the dependency of the correct version or change the dependency "
        "version in the $C_LOWER$'s definition."
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
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ {component_str} due to a dependency error. The "
        "component dependency '{invalid_dependency}' that the $C_LOWER$ depends on is "
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
    _MESSAGE_TEMPLATE = (
        "Failed to load the $C_LOWER$ {component_str} due to a dependency error. The "
        "component dependency '{not_running_dependency}' that the $C_LOWER$ depends on "
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
