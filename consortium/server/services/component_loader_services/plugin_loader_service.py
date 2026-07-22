from consortium.framework._core.framework_exceptions.plugins_framework_exceptions import (
    PluginsFrameworkError,
)
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    ComponentDependencyNotFoundError,
    DuplicatePluginLabelError,
    IncompatibleComponentDependencyVersionError,
    IncompatiblePluginFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalPluginError,
    InvalidPluginManifestFileJSONError,
    InvalidPluginManifestFileSchemaError,
    InvalidPluginPyProjectFileDependencyError,
    InvalidPluginPyProjectFileTOMLError,
    PluginAlreadyRegisteredError,
    PluginDependsOnInvalidComponentDependencyError,
    PluginEntryPointModuleNotFoundError,
    PluginInterfaceError,
    PluginManifestFileNotFoundError,
    PluginNotFoundError,
    PluginSymbolNotFoundError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
    ComponentLoadingExceptions,
)


class PluginLoaderService(ComponentLoaderService[BasePlugin]):
    _component_type = BasePlugin
    _component_framework_error = PluginsFrameworkError
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }
    # Raise plugin exceptions directly from the shared loader/registry pipeline instead
    # of raising generic component exceptions and remapping them downstream.
    _component_exceptions = ComponentLoadingExceptions(
        manifest_file_not_found=PluginManifestFileNotFoundError,
        invalid_manifest_file_json=InvalidPluginManifestFileJSONError,
        invalid_manifest_file_schema=InvalidPluginManifestFileSchemaError,
        invalid_pyproject_file_toml=InvalidPluginPyProjectFileTOMLError,
        invalid_pyproject_file_dependency=InvalidPluginPyProjectFileDependencyError,
        third_party_dependency_not_found=ThirdPartyDependencyNotFoundError,
        incompatible_third_party_dependency_version=IncompatibleThirdPartyDependencyVersionError,
        entry_point_module_not_found=PluginEntryPointModuleNotFoundError,
        symbol_not_found=PluginSymbolNotFoundError,
        interface_error=PluginInterfaceError,
        internal_error=InternalPluginError,
        incompatible_framework_version=IncompatiblePluginFrameworkVersionError,
        component_dependency_not_found=ComponentDependencyNotFoundError,
        incompatible_component_dependency_version=IncompatibleComponentDependencyVersionError,
        depends_on_invalid_component_dependency=PluginDependsOnInvalidComponentDependencyError,
        not_found=PluginNotFoundError,
        already_registered=PluginAlreadyRegisteredError,
        duplicate_label=DuplicatePluginLabelError,
    )
