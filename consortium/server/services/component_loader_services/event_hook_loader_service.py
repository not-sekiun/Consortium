from consortium.framework._core.framework_exceptions.event_hooks_framework_exceptions import (
    EventHooksFrameworkError,
)
from consortium.framework.event_hooks.base_event_hook import BaseEventHook
from consortium.server.exceptions.service_exceptions.event_hooks_service_exceptions import (
    ComponentDependencyNotFoundError,
    DuplicateEventHookLabelError,
    EventHookAlreadyRegisteredError,
    EventHookDependsOnInvalidComponentDependencyError,
    EventHookEntryPointModuleNotFoundError,
    EventHookInterfaceError,
    EventHookManifestFileNotFoundError,
    EventHookNotFoundError,
    EventHookSymbolNotFoundError,
    IncompatibleComponentDependencyVersionError,
    IncompatibleEventHookFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalEventHookError,
    InvalidEventHookManifestFileJSONError,
    InvalidEventHookManifestFileSchemaError,
    InvalidEventHookPyProjectFileDependencyError,
    InvalidEventHookPyProjectFileTOMLError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
    ComponentLoadingExceptions,
)


class EventHookLoaderService(ComponentLoaderService[BaseEventHook]):
    _component_type = BaseEventHook
    _component_framework_error = EventHooksFrameworkError
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }
    # Raise event hook exceptions directly from the shared loader/registry pipeline instead
    # of raising generic component exceptions and remapping them downstream.
    _component_exceptions = ComponentLoadingExceptions(
        manifest_file_not_found=EventHookManifestFileNotFoundError,
        invalid_manifest_file_json=InvalidEventHookManifestFileJSONError,
        invalid_manifest_file_schema=InvalidEventHookManifestFileSchemaError,
        invalid_pyproject_file_toml=InvalidEventHookPyProjectFileTOMLError,
        invalid_pyproject_file_dependency=InvalidEventHookPyProjectFileDependencyError,
        third_party_dependency_not_found=ThirdPartyDependencyNotFoundError,
        incompatible_third_party_dependency_version=IncompatibleThirdPartyDependencyVersionError,
        entry_point_module_not_found=EventHookEntryPointModuleNotFoundError,
        symbol_not_found=EventHookSymbolNotFoundError,
        interface_error=EventHookInterfaceError,
        internal_error=InternalEventHookError,
        incompatible_framework_version=IncompatibleEventHookFrameworkVersionError,
        component_dependency_not_found=ComponentDependencyNotFoundError,
        incompatible_component_dependency_version=IncompatibleComponentDependencyVersionError,
        depends_on_invalid_component_dependency=EventHookDependsOnInvalidComponentDependencyError,
        not_found=EventHookNotFoundError,
        already_registered=EventHookAlreadyRegisteredError,
        duplicate_label=DuplicateEventHookLabelError,
    )
