import pathlib
import uuid

from consortium.server.exceptions.service_exceptions import (
    components_service_exceptions as comp_excs,
)
from consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions import (
    AgentProfileAlreadyRegisteredError,
    AgentProfileDependsOnInvalidComponentDependencyError,
    AgentProfileLoadingError,
    AgentProfileNotFoundError,
    AgentProfileProjectEntryPointModuleNotFoundError,
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
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP = {
        comp_excs.ComponentProjectManifestFileNotFoundError: AgentProfileProjectManifestFileNotFoundError,
        comp_excs.InvalidComponentProjectManifestFileJSONError: InvalidAgentProfileProjectManifestFileJSONError,
        comp_excs.InvalidComponentProjectManifestFileSchemaError: InvalidAgentProfileProjectManifestFileSchemaError,
        comp_excs.InvalidComponentProjectPyProjectFileError: InvalidAgentProfileProjectPyProjectFileError,
        comp_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidAgentProfileProjectPyProjectFileDependencyError,
        comp_excs.ComponentProjectEntryPointModuleNotFoundError: AgentProfileProjectEntryPointModuleNotFoundError,
        comp_excs.ComponentProjectSymbolNotFoundError: AgentProfileProjectSymbolNotFoundError,
        comp_excs.ComponentProjectInterfaceError: AgentProfileProjectInterfaceError,
        comp_excs.IncompatibleComponentFrameworkVersionError: IncompatibleAgentProfileFrameworkVersionError,
        comp_excs.InternalComponentProjectError: InternalAgentProfileProjectError,
        comp_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_excs.ComponentDependsOnInvalidComponentDependencyError: AgentProfileDependsOnInvalidComponentDependencyError,
        comp_excs.ComponentNotFoundError: AgentProfileNotFoundError,
        comp_excs.ComponentAlreadyRegisteredError: AgentProfileAlreadyRegisteredError,
        comp_excs.DuplicateComponentLabelError: DuplicateAgentProfileLabelError,
    }
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP = {
        "component_directory": "agent_profile_directory",
        "component_str": "agent_profile_str",
        "component_id": "agent_profile_id",
    }

    def _get_component_id(self, component: AgentProfile) -> uuid.UUID:
        return component.agent_profile_id

    def _get_component_directory(self, component: AgentProfile) -> pathlib.Path:
        return component.root_directory
