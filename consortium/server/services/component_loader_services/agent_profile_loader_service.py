import pathlib

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilitiesFrameworkError,
)
from consortium.framework._core.framework_exceptions.agent_generators_framework_exceptions import (
    AgentGeneratorsFrameworkError,
)
from consortium.framework._core.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplatesFrameworkError,
)
from consortium.framework.agents.base_agent_template import BaseAgentTemplate
from consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions import (
    AgentProfileAlreadyRegisteredError,
    AgentProfileDependsOnInvalidComponentDependencyError,
    AgentProfileEntryPointModuleNotFoundError,
    AgentProfileInterfaceError,
    AgentProfileManifestFileNotFoundError,
    AgentProfileNotFoundError,
    AgentProfileSymbolNotFoundError,
    ComponentDependencyNotFoundError,
    DuplicateAgentProfileLabelError,
    IncompatibleAgentProfileFrameworkVersionError,
    IncompatibleComponentDependencyVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalAgentProfileError,
    InvalidAgentProfileManifestFileJSONError,
    InvalidAgentProfileManifestFileSchemaError,
    InvalidAgentProfilePyProjectFileDependencyError,
    InvalidAgentProfilePyProjectFileTOMLError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.exceptions.service_exceptions.components_service_exceptions import (
    ComponentLoadingError,
)
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
    ComponentLoadingExceptions,
)


class AgentProfileLoaderService(ComponentLoaderService[BaseAgentTemplate]):
    _component_type = BaseAgentTemplate  # TODO: Fix type mismatch this only describes the input but not output type
    _component_framework_error = (
        AgentTemplatesFrameworkError,
        AgentGeneratorsFrameworkError,
        AgentCapabilitiesFrameworkError,
    )
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }
    # Raise agent profile exceptions directly from the shared loader/registry pipeline
    # instead of raising generic component exceptions and remapping them downstream.
    _component_exceptions = ComponentLoadingExceptions(
        manifest_file_not_found=AgentProfileManifestFileNotFoundError,
        invalid_manifest_file_json=InvalidAgentProfileManifestFileJSONError,
        invalid_manifest_file_schema=InvalidAgentProfileManifestFileSchemaError,
        invalid_pyproject_file_toml=InvalidAgentProfilePyProjectFileTOMLError,
        invalid_pyproject_file_dependency=InvalidAgentProfilePyProjectFileDependencyError,
        third_party_dependency_not_found=ThirdPartyDependencyNotFoundError,
        incompatible_third_party_dependency_version=IncompatibleThirdPartyDependencyVersionError,
        entry_point_module_not_found=AgentProfileEntryPointModuleNotFoundError,
        symbol_not_found=AgentProfileSymbolNotFoundError,
        interface_error=AgentProfileInterfaceError,
        internal_error=InternalAgentProfileError,
        incompatible_framework_version=IncompatibleAgentProfileFrameworkVersionError,
        component_dependency_not_found=ComponentDependencyNotFoundError,
        incompatible_component_dependency_version=IncompatibleComponentDependencyVersionError,
        depends_on_invalid_component_dependency=AgentProfileDependsOnInvalidComponentDependencyError,
        not_found=AgentProfileNotFoundError,
        already_registered=AgentProfileAlreadyRegisteredError,
        duplicate_label=DuplicateAgentProfileLabelError,
    )

    @staticmethod
    def _post_validate_component_object(
        component_object: BaseAgentTemplate,
    ) -> AgentProfile:
        # agent generator refers to the class of the agent generator that the
        # template creates
        component_object.agent_generator.creating_agent_template = component_object
        # Framework user passes in the agent type class, instantiate the agent type
        component_object.agent_type = component_object.agent_type()
        component_object.agent_generator.agent_type = component_object.agent_type
        component_object.agent_generator.compatible_listener_types = (
            component_object.compatible_listener_types
        )
        return AgentProfile(
            agent_generator=component_object.agent_generator,
            agent_template=component_object,
            agent_type=component_object.agent_type,
        )

    # Change the return type to AgentProfile for IDE type checking
    def get_component_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> AgentProfile | None:
        return super().get_component_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    # TODO: The return type does not match same type mismatch issue as above comment
    def get_all_components_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[AgentProfile],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]],
    ]:
        return super().get_all_components_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )
