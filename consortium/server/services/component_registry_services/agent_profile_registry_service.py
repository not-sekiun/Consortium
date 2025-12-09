import pathlib
import uuid

import consortium.server.exceptions.service_exceptions.component_service_exceptions as comp_ldr_svc_excs
from consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions import (
    AgentProfileAlreadyRegisteredError,
    AgentProfileDependsOnInvalidComponentDependencyError,
    AgentProfileLoadingError,
    AgentProfileNotFoundError,
    AgentProfileProjectAgentProfileFileNotFoundError,
    AgentProfileProjectInterfaceError,
    AgentProfileProjectManifestFileNotFoundError,
    AgentProfileProjectSymbolNotFoundError,
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    DuplicateAgentProfileLabelError,
    IncompatibleAgentProfileFrameworkVersionError,
    IncompatibleComponentDependencyVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalAgentProfileProjectError,
    InvalidAgentProfileProjectManifestFileJSONError,
    InvalidAgentProfileProjectManifestFileSchemaError,
    InvalidAgentProfileProjectPyProjectFileDependencyError,
    InvalidAgentProfileProjectPyProjectFileError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.services.component_registry_services.exception_remapping_component_registry_service import (
    ExceptionRemappingComponentRegistryService,
)


class AgentProfileRegistryService(
    ExceptionRemappingComponentRegistryService[AgentProfile, AgentProfileLoadingError],
):
    _EXCEPTION_MAP = {
        comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError: AgentProfileProjectManifestFileNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError: InvalidAgentProfileProjectManifestFileJSONError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError: InvalidAgentProfileProjectManifestFileSchemaError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError: InvalidAgentProfileProjectPyProjectFileError,
        comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidAgentProfileProjectPyProjectFileDependencyError,
        comp_ldr_svc_excs.ComponentProjectComponentFileNotFoundError: AgentProfileProjectAgentProfileFileNotFoundError,
        comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError: AgentProfileProjectSymbolNotFoundError,
        comp_ldr_svc_excs.ComponentProjectInterfaceError: AgentProfileProjectInterfaceError,
        comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError: IncompatibleAgentProfileFrameworkVersionError,
        comp_ldr_svc_excs.InternalComponentProjectError: InternalAgentProfileProjectError,
        comp_ldr_svc_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_ldr_svc_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError: AgentProfileDependsOnInvalidComponentDependencyError,
        comp_ldr_svc_excs.ComponentNotFoundError: AgentProfileNotFoundError,
        comp_ldr_svc_excs.ComponentAlreadyRegisteredError: AgentProfileAlreadyRegisteredError,
        comp_ldr_svc_excs.DuplicateComponentLabelError: DuplicateAgentProfileLabelError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "agent_profile_project_folder",
        "component_file": "agent_profile_file",
        "component_symbol": "agent_profile_symbol",
        "component_str": "agent_profile_str",
        "component_id": "agent_profile_id",
    }

    def _get_component_id(self, component: AgentProfile) -> uuid.UUID:
        return component.agent_profile_id

    def _get_component_project_folder(self, component: AgentProfile) -> pathlib.Path:
        return component.agent_project_folder
