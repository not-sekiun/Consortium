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

import consortium.server.exceptions.service_exceptions.component_loader_service_exceptions as comp_excs
from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class EventHooksServiceError(BaseServiceException):
    pass


class EventHookNotFoundError(EventHooksServiceError):
    def __init__(self, event_hook_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested event hook. No event hook was found "
                f"with the provided event hook ID '{event_hook_id}'."
            ),
        )


class EventHookLoadingError(EventHooksServiceError, comp_excs.ComponentLoadingError):
    """
    Base exception for all errors that occur during the loading of an event hook.
    """

    _COMPONENT_TYPE = "event hook"


class InvalidEventHookProjectManifestFileError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectManifestFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid event hook project
    manifest `manifest.json` file.
    """


class InvalidEventHookProjectManifestFileJSONError(
    InvalidEventHookProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileJSONError,
):
    """
    An error that is raised when the event hook project manifest file is not a valid JSON
    file.
    """

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_project_folder=event_hook_project_folder)


class InvalidEventHookProjectManifestFileSchemaError(
    InvalidEventHookProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """
    An error that is raised when the event hook project manifest file does not conform to
    the expected JSON schema.
    """

    def __init__(self, event_hook_project_folder: str, json_schema_error_message: str):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            json_schema_error_message=json_schema_error_message,
        )


class InvalidEventHookProjectPyProjectFileError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileError,
):
    """
    Base exception for all errors that occur due to loading an invalid `pyproject.toml`
    file.
    """


class InvalidEventHookProjectPyProjectFileTOMLError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileTOMLError,
):
    """
    An error that is raised when the `pyproject.toml` file is not a valid TOML file
    """

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_project_folder=event_hook_project_folder)


class InvalidEventHookProjectPyProjectFileDependencyError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """
    An error that is raised when the `pyproject.toml` file contains invalid dependency
    entries.
    """

    def __init__(self, event_hook_project_folder: str, invalid_dependency_entry: str):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            invalid_dependency_entry=invalid_dependency_entry,
        )


class InvalidEventHookProjectFolderStructureError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """
    Base exception for all errors that occur due to the event hook being loaded having an
    invalid event hook project folder structure.
    """


class EventHookProjectManifestFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """
    An error that is raised when the event hook project manifest file is not found in the
    event hook project folder.
    """

    def __init__(self, event_hook_project_folder: str):
        super().__init__(component_project_folder=event_hook_project_folder)


class EventHookProjectEventHookFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_excs.ComponentProjectComponentFileNotFoundError,
):
    """
    An error that is raised when the event hook file specified in the manifest is not
    found in the event hook project folder.
    """

    def __init__(self, event_hook_project_folder: str, event_hook_file: str):
        super().__init__(
            component_file=event_hook_file,
            component_project_folder=event_hook_project_folder,
        )


class InvalidEventHookProjectImplementationError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectImplementationError,
):
    """
    Base exception for all errors that occur due to the event hook project not implementing
    the required interface for the event hook.
    """


class EventHookProjectSymbolNotFoundError(
    InvalidEventHookProjectImplementationError,
    comp_excs.ComponentProjectSymbolNotFoundError,
):
    """
    An error that is raised when the event hook symbol name specified in the manifest is not
    found in the event hook file.
    """

    def __init__(
        self,
        event_hook_project_folder: str,
        symbol_name: str,
        event_hook_file: str,
    ):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            symbol_name=symbol_name,
            component_file=event_hook_file,
        )


class EventHookProjectInterfaceError(
    InvalidEventHookProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """
    An error that is raised when the event hook class does not implement the required
    interface for the event hook.
    """

    def __init__(
        self,
        event_hook_project_folder: str,
        event_hook_symbol: str,
    ):
        super().__init__(
            component_project_folder=event_hook_project_folder,
            component_symbol=event_hook_symbol,
        )


class InternalEventHookProjectError(
    InvalidEventHookProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """
    An error that is raised when an unhandled exception from within the event hook is
    raised while loading an event hook project.
    """

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
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """
    An error that is raised when an event hook is incompatible with the current framework
    version.
    """

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
    """
    An error that is raised when an event hook with the same ID is already registered in the
    event hooks service.
    """

    def __init__(self, event_hook_str: str, event_hook_id: str):
        super().__init__(component_str=event_hook_str, component_id=event_hook_id)


class DuplicateEventHookLabelError(
    EventHookLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """
    An error that is raised when an event hook with the same `label` as the event hook being
    registered has already been registered with the event hooks service.
    """

    def __init__(self, event_hook_str: str, label: str):
        super().__init__(
            component_str=event_hook_str,
            label=label,
        )


class InternalEventHookStartError(
    EventHookLoadingError,
    comp_excs.InternalComponentStartError,
):
    """
    An error that is raised when an unhandled exception from within the event hook is
    raised while starting an event hook.
    """

    def __init__(self, event_hook_str: str, internal_error_message: str):
        super().__init__(
            component_str=event_hook_str,
            internal_error_message=internal_error_message,
        )


class EventHookDependencyError(
    EventHooksServiceError,
    comp_excs.ComponentDependencyError,
):
    """
    Base exception for all errors that occur during the resolution of an event hook's
    dependencies.
    """

    _COMPONENT_TYPE = "event hook"


class ThirdPartyDependencyNotFoundError(
    EventHookDependencyError,
    comp_excs.ThirdPartyDependencyNotFoundError,
):
    """
    An error that is raised when a third-party dependency required by an event hook is not
    installed.
    """

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
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """
    An error that is raised when a third-party dependency required by an event hook is
    incompatible with the event hook.
    """

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
    comp_excs.ComponentDependencyNotFoundError,
):
    """
    An error that is raised when an event hook dependency required by an event hook is not
    installed.
    """

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
    """
    An error that is raised when an event hook dependency required by an event hook is
    incompatible with the event hook.
    """

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
    """
    An error that is raised when an event hook depends on another event hook dependency that
    itself has invalid dependencies.
    """

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
    """
    An error that is raised when an event hook dependency required by an event hook is present but
    not currently running.
    """

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
    pass


class EventHookSetupError(EventHookOperationError):
    def __init__(self, event_hook_str: str, error_message: str):
        super().__init__(
            message=(
                f"Failed to load event hook '{event_hook_str}'. An error occurred "
                f"while the event hook was setting up: {error_message}"
            ),
        )


class EventHookTeardownError(EventHooksServiceError):
    def __init__(self, event_hook_str: str, error_message: str):
        super().__init__(
            message=(
                f"Failed to unload event hook '{event_hook_str}'. An error occurred "
                f"while the event hook was tearing down: {error_message}"
            ),
        )
