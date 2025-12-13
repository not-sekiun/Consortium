import pathlib
import uuid

import consortium.server.exceptions.service_exceptions.components_service_exceptions as comp_ldr_svc_excs
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
    _EXCEPTION_MAP = {
        comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError: ListenerProfileProjectManifestFileNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError: InvalidListenerProfileProjectManifestFileJSONError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError: InvalidListenerProfileProjectManifestFileSchemaError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError: InvalidListenerProfileProjectPyProjectFileError,
        comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidListenerProfileProjectPyProjectFileDependencyError,
        comp_ldr_svc_excs.ComponentProjectEntryPointModuleNotFoundError: ListenerProfileProjectEntryPointModuleNotFoundError,
        comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError: ListenerProfileProjectSymbolNotFoundError,
        comp_ldr_svc_excs.ComponentProjectInterfaceError: ListenerProfileProjectInterfaceError,
        comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError: IncompatibleListenerProfileFrameworkVersionError,
        comp_ldr_svc_excs.InternalComponentProjectError: InternalListenerProfileProjectError,
        comp_ldr_svc_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_ldr_svc_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError: ListenerProfileDependsOnInvalidComponentDependencyError,
        comp_ldr_svc_excs.ComponentNotFoundError: ListenerProfileNotFoundError,
        comp_ldr_svc_excs.ComponentAlreadyRegisteredError: ListenerProfileAlreadyRegisteredError,
        comp_ldr_svc_excs.DuplicateComponentLabelError: DuplicateListenerProfileLabelError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "listener_profile_project_folder",
        "component_file": "listener_profile_file",
        "component_symbol": "listener_profile_symbol",
        "component_str": "listener_profile_str",
        "component_id": "listener_profile_id",
    }

    def _get_component_id(self, component: ListenerProfile) -> uuid.UUID:
        return component.listener_profile_id

    def _get_component_project_folder(self, component: ListenerProfile) -> pathlib.Path:
        return component.listener_project_folder
