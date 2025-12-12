"""
Exception hierarchy for errors related to the event hooks service:

- BaseServiceException: Base class for all service-related exceptions.
  - EventHooksServiceException: Base class for all errors related to the event hooks
  service.
    - EventHookNotFoundError: Raised when an event hook is not found.
    - EventHookLoadingError: Raised when an event hook fails to load.
      - InvalidEventHookProjectManifestFileError: Raised when the event hook project
      manifest file is invalid.
        - InvalidEventHookProjectManifestFileJSONError: Raised when the event hook
        project manifest file is not a valid JSON file.
        - InvalidEventHookProjectManifestFileSchemaError: Raised when the event hook
        project manifest file does not conform to the expected schema.
      - InvalidEventHookProjectFolderStructureError: Raised when the event hook project
      folder structure is invalid.
        - EventHookProjectManifestFileNotFoundError: Raised when the event hook project
        manifest file is not found.
        - EventHookProjectEventHookFileNotFoundError: Raised when the event hook file
        specified in the manifest is not found.
      - InvalidEventHookProjectImplementationError: Raised when an event hook project's
      implementation is invalid.
        - EventHookProjectSymbolNotFoundError: Raised when the symbol name specified in
        the manifest is not found in the event hook file.
        - EventHookProjectInterfaceError: Raised when the event hook class does not
        implement the BaseEventHook interface.
        - InternalEventHookProjectError: Raised when an internal error occurs while
        handling an event hook project.
      - IncompatibleEventHookFrameworkVersionError: Raised when an event hook is
      incompatible with the version of the currently running framework.
    - EventHookUnloadingError: Raised when an event hook fails to unload.
"""

import consortium.server.exceptions.service_exceptions.component_service_exceptions as comp_svc_excs
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class EventHooksServiceError(BaseServiceException):
    code = "EVENT_HOOKS_SERVICE_ERROR"


class EventHookNotFoundError(
    EventHooksServiceError,
    comp_svc_excs.ComponentNotFoundError,
):
    """
    An error that is raised when an event hook with the specified ID is not found.
    """

    code = "EVENT_HOOK_NOT_FOUND_ERROR"
    _COMPONENT_TYPE = "event hook"

    def __init__(self, event_hook_id: str):
        super().__init__(component_id=event_hook_id)


class EventHookLoadingError(
    EventHooksServiceError,
    comp_svc_excs.ComponentLoadingError,
):
    """
    Base exception for all errors that occur during the loading of an event hook.
    """

    code = "EVENT_HOOK_LOADING_ERROR"
    _COMPONENT_TYPE = "event hook"


class InvalidEventHookProjectManifestFileError(
    EventHookLoadingError,
    comp_svc_excs.InvalidComponentProjectManifestFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid event hook project
    manifest `manifest.json` file.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_ERROR"


class InvalidEventHookProjectManifestFileJSONError(
    InvalidEventHookProjectManifestFileError,
    comp_svc_excs.InvalidComponentProjectManifestFileJSONError,
):
    """
    An error that is raised when the event hook project manifest file is not a valid JSON
    file.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_JSON_ERROR"

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_project_folder=event_hook_project_folder)


class InvalidEventHookProjectManifestFileSchemaError(
    InvalidEventHookProjectManifestFileError,
    comp_svc_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """
    An error that is raised when the event hook project manifest file does not conform to
    the expected JSON schema.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"

    def __init__(self, event_hook_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidEventHookProjectPyProjectFileError(
    EventHookLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid `pyproject.toml`
    file.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_ERROR"


class InvalidEventHookProjectPyProjectFileTOMLError(
    EventHookLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """
    An error that is raised when the `pyproject.toml` file is not a valid TOML file
    """

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_TOML_ERROR"

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_project_folder=event_hook_project_folder)


class InvalidEventHookProjectPyProjectFileDependencyError(
    EventHookLoadingError,
    comp_svc_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """
    An error that is raised when the `pyproject.toml` file contains invalid dependency
    entries.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"

    def __init__(self, event_hook_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidEventHookProjectFolderStructureError(
    EventHookLoadingError,
    comp_svc_excs.InvalidComponentProjectFolderStructureError,
):
    """
    Base exception for all errors that occur due to the event hook being loaded having an
    invalid event hook project folder structure.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_FOLDER_STRUCTURE_ERROR"


class EventHookProjectManifestFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_svc_excs.ComponentProjectManifestFileNotFoundError,
):
    """
    An error that is raised when the event hook project manifest file is not found in the
    event hook project folder.
    """

    code = "EVENT_HOOK_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_project_folder=event_hook_project_folder)


class EventHookProjectEntryPointModuleNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_svc_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """
    An error that is raised when the event hook file specified in the manifest is not
    found in the event hook project folder.
    """

    code = "EVENT_HOOK_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"

    def __init__(self, event_hook_project_folder: str, event_hook_file: str):
        super().__init__(
            entry_point_module=event_hook_file,
            component_project_folder=event_hook_project_folder,
        )


class InvalidEventHookProjectImplementationError(
    EventHookLoadingError,
    comp_svc_excs.InvalidComponentProjectImplementationError,
):
    """
    Base exception for all errors that occur due to the event hook project not implementing
    the required interface for the event hook.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_IMPLEMENTATION_ERROR"


class EventHookProjectSymbolNotFoundError(
    InvalidEventHookProjectImplementationError,
    comp_svc_excs.ComponentProjectSymbolNotFoundError,
):
    """
    An error that is raised when the event hook symbol name specified in the manifest is not
    found in the event hook file.
    """

    code = "EVENT_HOOK_PROJECT_SYMBOL_NOT_FOUND_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        entry_point_symbol: str,
        entry_point_module: str,
    ):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            entry_point_symbol=entry_point_symbol,
            entry_point_module=entry_point_module,
        )


class EventHookProjectInterfaceError(
    InvalidEventHookProjectImplementationError,
    comp_svc_excs.ComponentProjectInterfaceError,
):
    """
    An error that is raised when the event hook class does not implement the required
    interface for the event hook.
    """

    code = "EVENT_HOOK_PROJECT_INTERFACE_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        entry_point_symbol: str,
    ):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            entry_point_symbol=entry_point_symbol,
        )


class InternalEventHookProjectError(
    InvalidEventHookProjectImplementationError,
    comp_svc_excs.InternalComponentProjectError,
):
    """
    An error that is raised when an unhandled exception from within the event hook is
    raised while loading an event hook project.
    """

    code = "INTERNAL_EVENT_HOOK_PROJECT_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        internal_error_message: str,
    ):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            internal_error_message=internal_error_message,
        )


class IncompatibleEventHookFrameworkVersionError(
    EventHookLoadingError,
    comp_svc_excs.IncompatibleComponentFrameworkVersionError,
):
    """
    An error that is raised when an event hook is incompatible with the current framework
    version.
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
    comp_svc_excs.ComponentAlreadyRegisteredError,
):
    """
    An error that is raised when an event hook with the same ID is already registered in the
    event hooks service.
    """

    code = "EVENT_HOOK_ALREADY_REGISTERED_ERROR"

    def __init__(self, event_hook_str: str, event_hook_id: str):
        super().__init__(component_str=event_hook_str, component_id=event_hook_id)


class DuplicateEventHookLabelError(
    EventHookLoadingError,
    comp_svc_excs.DuplicateComponentLabelError,
):
    """
    An error that is raised when an event hook with the same `label` as the event hook being
    registered has already been registered with the event hooks service.
    """

    code = "DUPLICATE_EVENT_HOOK_LABEL_ERROR"

    def __init__(self, event_hook_str: str, label: str):
        super().__init__(
            component_str=event_hook_str,
            label=label,
        )


# class InternalEventHookSetupError(
#     EventHookLoadingError,
#     # comp_excs.InternalComponentStartError,
# ):
#     """
#     An error that is raised when an unhandled exception from within the event hook is
#     raised while setting up an event hook.
#     """
#
#     def __init__(self, event_hook_str: str, internal_error_message: str):
#         super().__init__(
#             message=(
#                 f"Failed to load the event hook '{event_hook_str}'. An exception "
#                 f"occurred while setting up the event hook: {internal_error_message}"
#             )
#         )


class EventHookDependencyError(
    EventHooksServiceError,
    comp_svc_excs.ComponentDependencyError,
):
    """
    Base exception for all errors that occur during the resolution of an event hook's
    dependencies.
    """

    code = "EVENT_HOOK_DEPENDENCY_ERROR"
    _COMPONENT_TYPE = "event hook"


class ThirdPartyDependencyNotFoundError(
    EventHookDependencyError,
    comp_svc_excs.ThirdPartyDependencyNotFoundError,
):
    """
    An error that is raised when a third-party dependency required by an event hook is not
    installed.
    """

    code = "THIRD_PARTY_DEPENDENCY_NOT_FOUND_ERROR"

    def __init__(
        self,
        event_hook_project_folder: str,
        third_party_dependency_name: str,
    ):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            third_party_dependency_name=third_party_dependency_name,
        )


class IncompatibleThirdPartyDependencyVersionError(
    EventHookDependencyError,
    comp_svc_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """
    An error that is raised when a third-party dependency required by an event hook is
    incompatible with the event hook.
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
            component_project_folder=event_hook_project_folder,
            third_party_dependency_name=third_party_dependency_name,
            required_version=required_version,
            installed_version=installed_version,
        )


class ComponentDependencyNotFoundError(
    EventHookDependencyError,
    comp_svc_excs.ComponentDependencyNotFoundError,
):
    """
    An error that is raised when an event hook dependency required by an event hook is not
    installed.
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
    comp_svc_excs.IncompatibleComponentDependencyVersionError,
):
    """
    An error that is raised when an event hook dependency required by an event hook is
    incompatible with the event hook.
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
    comp_svc_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """
    An error that is raised when an event hook depends on another event hook dependency that
    itself has invalid dependencies.
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
    comp_svc_excs.ComponentDependencyNotRunningError,
):
    """
    An error that is raised when an event hook dependency required by an event hook is present but
    not currently running.
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
    code = "EVENT_HOOK_OPERATION_ERROR"


class EventHookSetupError(EventHookOperationError):
    code = "EVENT_HOOK_SETUP_ERROR"

    def __init__(self, event_hook_str: str, error_message: str):
        super().__init__(
            message=(
                f"Failed to load event hook '{event_hook_str}'. An error occurred "
                f"while the event hook was setting up: {error_message}"
            ),
        )


class EventHookTeardownError(EventHookOperationError):
    code = "EVENT_HOOK_TEARDOWN_ERROR"

    def __init__(self, event_hook_str: str, error_message: str):
        super().__init__(
            message=(
                f"Failed to unload event hook '{event_hook_str}'. An error occurred "
                f"while the event hook was tearing down: {error_message}"
            ),
        )
