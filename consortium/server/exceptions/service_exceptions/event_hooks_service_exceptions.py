"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`EventHooksServiceError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHooksServiceError]
        - [`EventHookNotFoundError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookNotFoundError]
        - [`EventHookLoadingError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookLoadingError]
            - [`InvalidEventHookProjectManifestFileError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectManifestFileError]
                - [`InvalidEventHookProjectManifestFileJSONError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectManifestFileJSONError]
                - [`InvalidEventHookProjectManifestFileSchemaError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectManifestFileSchemaError]
            - [`InvalidEventHookProjectPyProjectFileError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectPyProjectFileError]
            - [`InvalidEventHookProjectPyProjectFileTOMLError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectPyProjectFileTOMLError]
            - [`InvalidEventHookProjectPyProjectFileDependencyError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectPyProjectFileDependencyError]
            - [`InvalidEventHookProjectFolderStructureError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectFolderStructureError]
                - [`EventHookProjectManifestFileNotFoundError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookProjectManifestFileNotFoundError]
                - [`EventHookProjectEntryPointModuleNotFoundError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookProjectEntryPointModuleNotFoundError]
            - [`InvalidEventHookProjectImplementationError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InvalidEventHookProjectImplementationError]
                - [`EventHookProjectSymbolNotFoundError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookProjectSymbolNotFoundError]
                - [`EventHookProjectInterfaceError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookProjectInterfaceError]
                - [`InternalEventHookProjectError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.InternalEventHookProjectError]
            - [`IncompatibleEventHookFrameworkVersionError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.IncompatibleEventHookFrameworkVersionError]
            - [`EventHookAlreadyRegisteredError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookAlreadyRegisteredError]
            - [`DuplicateEventHookLabelError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.DuplicateEventHookLabelError]
        - [`EventHookDependencyError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookDependencyError]
            - [`ThirdPartyDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.ThirdPartyDependencyNotFoundError]
            - [`IncompatibleThirdPartyDependencyVersionError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.IncompatibleThirdPartyDependencyVersionError]
            - [`ComponentDependencyNotFoundError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.ComponentDependencyNotFoundError]
            - [`IncompatibleComponentDependencyVersionError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.IncompatibleComponentDependencyVersionError]
            - [`EventHookDependsOnInvalidComponentDependencyError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookDependsOnInvalidComponentDependencyError]
            - [`ComponentDependencyNotRunningError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.ComponentDependencyNotRunningError]
        - [`EventHookOperationError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookOperationError]
            - [`EventHookSetupError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookSetupError]
            - [`EventHookTriggerError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookTriggerError]
            - [`EventHookTeardownError`][consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions.EventHookTeardownError]
"""

from pydantic import JsonValue

from consortium.server.exceptions.service_exceptions import (
    components_service_exceptions as comp_excs,
)
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class EventHooksServiceError(BaseServiceError):
    """Base exception for all errors that occur within the event hooks service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "EVENT_HOOKS_SERVICE_ERROR"


class EventHookNotFoundError(
    EventHooksServiceError,
    comp_excs.ComponentNotFoundError,
):
    """Raised when the requested event hook with the provided event hook ID was not found in the
    event hooks service.
    """

    code = "EVENT_HOOK_NOT_FOUND_ERROR"
    _COMPONENT_TYPE = "event hook"

    def __init__(self, event_hook_id: str):
        super().__init__(component_id=event_hook_id)


class EventHookLoadingError(
    EventHooksServiceError,
    comp_excs.ComponentLoadingError,
):
    """Base exception for all errors that occur during the loading of an event hook."""

    code = "EVENT_HOOK_LOADING_ERROR"
    _COMPONENT_TYPE = "event hook"


class InvalidEventHookProjectManifestFileError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectManifestFileError,
):
    """Base exception for all errors that occur due to an invalid event hook project manifest
    `manifest.json` file during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_ERROR"


class InvalidEventHookProjectManifestFileJSONError(
    InvalidEventHookProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileJSONError,
):
    """Raised when the event hook project manifest file is not valid JSON during event hook
    loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_JSON_ERROR"

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_directory=event_hook_project_folder)


class InvalidEventHookProjectManifestFileSchemaError(
    InvalidEventHookProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the event hook project manifest file does not conform to the expected JSON
    schema during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    def __init__(self, event_hook_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_directory=event_hook_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidEventHookProjectPyProjectFileError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileError,
):
    """Base exception for all errors that occur due to an invalid `pyproject.toml` file
    during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidEventHookProjectPyProjectFileTOMLError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """Raised when the `pyproject.toml` file is not a valid TOML file during event hook loading."""

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_TOML_ERROR"

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_directory=event_hook_project_folder)


class InvalidEventHookProjectPyProjectFileDependencyError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    def __init__(self, event_hook_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_directory=event_hook_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidEventHookProjectFolderStructureError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid event hook project folder
    structure during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_FOLDER_STRUCTURE_ERROR"


class EventHookProjectManifestFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the event hook project manifest file is not found in the event hook project
    folder during event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_directory=event_hook_project_folder)


class EventHookProjectEntryPointModuleNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the event hook entry point module specified in the manifest is not found in
    the event hook project folder during event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    def __init__(self, event_hook_project_folder: str, event_hook_file: str):
        super().__init__(
            entry_point_module=event_hook_file,
            component_directory=event_hook_project_folder,
        )


class InvalidEventHookProjectImplementationError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectImplementationError,
):
    """Base exception for all errors that occur due to the event hook project not implementing
    the required interface during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_IMPLEMENTATION_ERROR"


class EventHookProjectSymbolNotFoundError(
    InvalidEventHookProjectImplementationError,
    comp_excs.ComponentProjectSymbolNotFoundError,
):
    """Raised when the event hook symbol name specified in the manifest is not found in the
    event hook entry point module during event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_SYMBOL_NOT_FOUND_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_directory=event_hook_project_folder,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class EventHookProjectInterfaceError(
    InvalidEventHookProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the event hook class does not implement the required interface during
    event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_directory=event_hook_project_folder,
            entry_point_symbol=entry_point_symbol,
        )


class InternalEventHookProjectError(
    InvalidEventHookProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the event hook is raised during event hook
    loading.
    """

    code = "INTERNAL_EVENT_HOOK_PROJECT_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_directory=event_hook_project_folder,
            internal_error_message=internal_error_message,
        )


class IncompatibleEventHookFrameworkVersionError(
    EventHookLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when an event hook's required framework version is incompatible with the current
    framework version during event hook loading.
    """

    code = "INCOMPATIBLE_EVENT_HOOK_FRAMEWORK_VERSION_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        required_version: str,
        current_version: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            required_version=required_version,
            current_version=current_version,
        )


class EventHookAlreadyRegisteredError(
    EventHookLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when an event hook with the same ID is already registered in the event hooks service
    during event hook loading.
    """

    code = "EVENT_HOOK_ALREADY_REGISTERED_ERROR"

    def __init__(self, event_hook_str: str, event_hook_id: str):
        super().__init__(component_str=event_hook_str, component_id=event_hook_id)


class DuplicateEventHookLabelError(
    EventHookLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the event hook's definition is already in use by
    another event hook during event hook loading.
    """

    code = "DUPLICATE_EVENT_HOOK_LABEL_ERROR"

    def __init__(self, event_hook_str: str, label: str):
        super().__init__(
            component_str=event_hook_str,
            label=label,
        )


class EventHookDependencyError(
    EventHooksServiceError,
    comp_excs.ComponentDependencyError,
):
    """Base exception for all errors that occur during the resolution of event hook
    dependencies.
    """

    code = "EVENT_HOOK_DEPENDENCY_ERROR"
    _COMPONENT_TYPE = "event hook"


class ThirdPartyDependencyNotFoundError(
    EventHookDependencyError,
    comp_excs.ThirdPartyDependencyNotFoundError,
):
    """Raised when a third-party dependency required by an event hook is not installed during
    event hook dependency resolution.
    """

    code = "THIRD_PARTY_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_directory=event_hook_project_folder,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(
    EventHookDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the event hook during event hook dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        third_party_dependency_name: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_directory=event_hook_project_folder,
            third_party_dependency_name=third_party_dependency_name,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependencyNotFoundError(
    EventHookDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when an event hook dependency required by the event hook is not found in the event hooks
    service during event hook dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        missing_dependency: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            missing_dependency=missing_dependency,
        )


class IncompatibleComponentDependencyVersionError(
    EventHookDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when an event hook dependency's version is incompatible with the version required
    by the event hook during event hook dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        incompatible_dependency: str,
        required_version: str,
        installed_version: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            incompatible_dependency=incompatible_dependency,
            required_version=required_version,
            installed_version=installed_version,
        )


class EventHookDependsOnInvalidComponentDependencyError(
    EventHookDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when an event hook depends on another event hook that itself has invalid dependencies
    during event hook dependency resolution.
    """

    code = "EVENT_HOOK_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        invalid_dependency: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            invalid_dependency=invalid_dependency,
        )


class ComponentDependencyNotRunningError(
    EventHookDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when an event hook dependency required by the event hook is present but not currently
    running during event hook dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        not_running_dependency: str,
    ):
        super().__init__(
            component_str=event_hook_str,
            not_running_dependency=not_running_dependency,
        )


class EventHookOperationError(EventHooksServiceError):
    """Base exception for all errors that occur during the operation of a particular
    event hook.
    """

    code = "EVENT_HOOK_OPERATION_ERROR"


class EventHookSetupError(EventHookOperationError):
    """Raised when an event hook fails to set up during event hook operation."""

    code = "EVENT_HOOK_SETUP_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to load event hook '{event_hook_str}'. An error occurred "
                f"while the event hook was setting up: {error_message}"
            ),
            detail=detail,
        )


class EventHookTriggerError(EventHookOperationError):
    """Raised when an event hook fails while handling a triggered event during event
    hook operation.
    """

    code = "EVENT_HOOK_TRIGGER_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=(
                f"Event hook '{event_hook_str}' failed while handling a triggered "
                f"event: {error_message}"
            ),
            detail=detail,
        )


class EventHookTeardownError(EventHookOperationError):
    """Raised when an event hook fails to tear down during event hook operation."""

    code = "EVENT_HOOK_TEARDOWN_ERROR"

    def __init__(
        self,
        event_hook_str: str,
        error_message: str,
        detail: dict[str, JsonValue] | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to unload event hook '{event_hook_str}'. An error occurred "
                f"while the event hook was tearing down: {error_message}"
            ),
            detail=detail,
        )
