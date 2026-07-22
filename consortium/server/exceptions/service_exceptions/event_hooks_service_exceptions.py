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

The loading, dependency, and registry exceptions below carry no `__init__` of their own: they
are constructed by the shared component loader/registry pipeline with the generic component
keyword arguments (`component_directory`, `component_str`, `component_id`, ...) inherited from
their `components_service_exceptions` base. Only the operation errors, which are raised directly
by the event hook registry with a bespoke message, define their own constructor.
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


class InvalidEventHookProjectManifestFileSchemaError(
    InvalidEventHookProjectManifestFileError,
    comp_excs.InvalidComponentProjectManifestFileSchemaError,
):
    """Raised when the event hook project manifest file does not conform to the expected JSON
    schema during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_MANIFEST_FILE_SCHEMA_ERROR"


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


class InvalidEventHookProjectPyProjectFileDependencyError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectPyProjectFileDependencyError,
):
    """Raised when the `pyproject.toml` file contains an invalid dependency entry during
    event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_PYPROJECT_FILE_DEPENDENCY_ERROR"


class InvalidEventHookProjectFolderStructureError(
    EventHookLoadingError,
    comp_excs.InvalidComponentProjectFolderStructureError,
):
    """Base exception for all errors that occur due to an invalid event hook root directory
    structure during event hook loading.
    """

    code = "INVALID_EVENT_HOOK_PROJECT_FOLDER_STRUCTURE_ERROR"


class EventHookProjectManifestFileNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_excs.ComponentProjectManifestFileNotFoundError,
):
    """Raised when the event hook project manifest file is not found in the event hook root
    directory during event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_MANIFEST_FILE_NOT_FOUND_ERROR"


class EventHookProjectEntryPointModuleNotFoundError(
    InvalidEventHookProjectFolderStructureError,
    comp_excs.ComponentProjectEntryPointModuleNotFoundError,
):
    """Raised when the event hook entry point module specified in the manifest is not found in
    the event hook root directory during event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_ENTRY_POINT_MODULE_NOT_FOUND_ERROR"


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


class EventHookProjectInterfaceError(
    InvalidEventHookProjectImplementationError,
    comp_excs.ComponentProjectInterfaceError,
):
    """Raised when the event hook class does not implement the required interface during
    event hook loading.
    """

    code = "EVENT_HOOK_PROJECT_INTERFACE_ERROR"


class InternalEventHookProjectError(
    InvalidEventHookProjectImplementationError,
    comp_excs.InternalComponentProjectError,
):
    """Raised when an unhandled exception from within the event hook is raised during event hook
    loading.
    """

    code = "INTERNAL_EVENT_HOOK_PROJECT_ERROR"


class IncompatibleEventHookFrameworkVersionError(
    EventHookLoadingError,
    comp_excs.IncompatibleComponentFrameworkVersionError,
):
    """Raised when an event hook's required framework version is incompatible with the current
    framework version during event hook loading.
    """

    code = "INCOMPATIBLE_EVENT_HOOK_FRAMEWORK_VERSION_ERROR"


class EventHookAlreadyRegisteredError(
    EventHookLoadingError,
    comp_excs.ComponentAlreadyRegisteredError,
):
    """Raised when an event hook with the same ID is already registered in the event hooks service
    during event hook loading.
    """

    code = "EVENT_HOOK_ALREADY_REGISTERED_ERROR"


class DuplicateEventHookLabelError(
    EventHookLoadingError,
    comp_excs.DuplicateComponentLabelError,
):
    """Raised when the label provided in the event hook's definition is already in use by
    another event hook during event hook loading.
    """

    code = "DUPLICATE_EVENT_HOOK_LABEL_ERROR"


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


class IncompatibleThirdPartyDependencyVersionError(
    EventHookDependencyError,
    comp_excs.IncompatibleThirdPartyDependencyVersionError,
):
    """Raised when a third-party dependency's installed version is incompatible with the
    version required by the event hook during event hook dependency resolution.
    """

    code = "INCOMPATIBLE_THIRD_PARTY_DEPENDENCY_VERSION_ERROR"


class ComponentDependencyNotFoundError(
    EventHookDependencyError,
    comp_excs.ComponentDependencyNotFoundError,
):
    """Raised when an event hook dependency required by the event hook is not found in the event hooks
    service during event hook dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_FOUND_ERROR"


class IncompatibleComponentDependencyVersionError(
    EventHookDependencyError,
    comp_excs.IncompatibleComponentDependencyVersionError,
):
    """Raised when an event hook dependency's version is incompatible with the version required
    by the event hook during event hook dependency resolution.
    """

    code = "INCOMPATIBLE_COMPONENT_DEPENDENCY_VERSION_ERROR"


class EventHookDependsOnInvalidComponentDependencyError(
    EventHookDependencyError,
    comp_excs.ComponentDependsOnInvalidComponentDependencyError,
):
    """Raised when an event hook depends on another event hook that itself has invalid dependencies
    during event hook dependency resolution.
    """

    code = "EVENT_HOOK_DEPENDS_ON_INVALID_COMPONENT_DEPENDENCY_ERROR"


class ComponentDependencyNotRunningError(
    EventHookDependencyError,
    comp_excs.ComponentDependencyNotRunningError,
):
    """Raised when an event hook dependency required by the event hook is present but not currently
    running during event hook dependency resolution.
    """

    code = "COMPONENT_DEPENDENCY_NOT_RUNNING_ERROR"


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
