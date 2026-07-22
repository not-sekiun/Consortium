import uuid

from consortium.server.exceptions.service_exceptions import (
    components_service_exceptions as comp_excs,
)
from consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    DuplicateListenerProfileLabelError,
    IncompatibleComponentDependencyVersionError,
    IncompatibleListenerProfileFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalListenerProfileProjectError,
    InvalidListenerProfileProjectManifestFileJSONError,
    InvalidListenerProfileProjectManifestFileSchemaError,
    InvalidListenerProfileProjectPyProjectFileDependencyError,
    InvalidListenerProfileProjectPyProjectFileError,
    ListenerProfileAlreadyRegisteredError,
    ListenerProfileDependsOnInvalidComponentDependencyError,
    ListenerProfileLoadingError,
    ListenerProfileNotFoundError,
    ListenerProfileProjectEntryPointModuleNotFoundError,
    ListenerProfileProjectInterfaceError,
    ListenerProfileProjectManifestFileNotFoundError,
    ListenerProfileProjectSymbolNotFoundError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.services.component_registry_services.exception_remapping_component_registry_service import (
    ExceptionRemappingComponentRegistryService,
)


class ListenerProfileRegistryService(
    ExceptionRemappingComponentRegistryService[
        ListenerProfile,
        ListenerProfileLoadingError,
    ],
):
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP = {
        comp_excs.ComponentProjectManifestFileNotFoundError: ListenerProfileProjectManifestFileNotFoundError,
        comp_excs.InvalidComponentProjectManifestFileJSONError: InvalidListenerProfileProjectManifestFileJSONError,
        comp_excs.InvalidComponentProjectManifestFileSchemaError: InvalidListenerProfileProjectManifestFileSchemaError,
        comp_excs.InvalidComponentProjectPyProjectFileError: InvalidListenerProfileProjectPyProjectFileError,
        comp_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidListenerProfileProjectPyProjectFileDependencyError,
        comp_excs.ComponentProjectEntryPointModuleNotFoundError: ListenerProfileProjectEntryPointModuleNotFoundError,
        comp_excs.ComponentProjectSymbolNotFoundError: ListenerProfileProjectSymbolNotFoundError,
        comp_excs.ComponentProjectInterfaceError: ListenerProfileProjectInterfaceError,
        comp_excs.IncompatibleComponentFrameworkVersionError: IncompatibleListenerProfileFrameworkVersionError,
        comp_excs.InternalComponentProjectError: InternalListenerProfileProjectError,
        comp_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_excs.ComponentDependsOnInvalidComponentDependencyError: ListenerProfileDependsOnInvalidComponentDependencyError,
        comp_excs.ComponentNotFoundError: ListenerProfileNotFoundError,
        comp_excs.ComponentAlreadyRegisteredError: ListenerProfileAlreadyRegisteredError,
        comp_excs.DuplicateComponentLabelError: DuplicateListenerProfileLabelError,
    }
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP = {
        "component_directory": "listener_profile_directory",
        "component_str": "listener_profile_str",
        "component_id": "listener_profile_id",
    }

    def _get_component_id(self, component: ListenerProfile) -> uuid.UUID:
        return component.listener_profile_id
