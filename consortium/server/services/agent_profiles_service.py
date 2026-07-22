import pathlib
import uuid

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions.agent_templates_framework_exceptions import (
    AgentTemplatesFrameworkError,
)
from consortium.server.exceptions.service_exceptions.agent_profiles_service_exceptions import (
    AgentProfileLoadingError,
    AgentProfilesServiceError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.services.component_loader_services.agent_profile_loader_service import (
    AgentProfileLoaderService,
)
from consortium.server.services.component_registry_services.agent_profile_registry_service import (
    AgentProfileRegistryService,
)
from consortium.server.services.paths_service import PathsService
from consortium.server.services.release_service import ReleaseService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


# The agent profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API should not have access to this service.
class AgentProfilesService:
    def __init__(
        self,
        release_service: ReleaseService,
        paths_service: PathsService,
    ) -> None:
        self._agents_directory = paths_service.agents_directory
        self._agent_profile_loader_service = AgentProfileLoaderService(
            paths_service=paths_service,
            release_service=release_service,
        )
        self._agent_profile_registry_service = AgentProfileRegistryService(
            component_loader_service=self._agent_profile_loader_service,
            component_framework_directory=self._agents_directory,
        )
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Agent Profiles Service"

    def __repr__(self) -> str:
        return "AgentProfilesService()"

    @log_and_propagate_error_on_service_method
    def get_agent_profile_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> AgentProfile | None:
        """Instantiates an agent profile from a project folder without registering it.

        Disabled agent profiles (as indicated by `enabled: false` in their
        `manifest.json`) are not instantiated unless `ignore_enabled_flag`
        is `True`.

        Args:
            directory: Path to the directory
                containing the agent profile project files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in the manifest. Defaults to `False`.

        Returns:
            The instantiated agent profile, or `None` if the
                profile is disabled and the enabled check is not overridden.

        Raises:
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                specified in the manifest cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol specified in the manifest
                is not found in the entry-point module.
            ComponentProjectInterfaceError: If the agent profile class does not
                correctly inherit from the expected base class.
            IncompatibleComponentFrameworkVersionError: If the profile is incompatible
                with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs while
                loading the profile.
        """
        agent_profile = (
            self._agent_profile_registry_service.get_component_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        if agent_profile is None:
            self._logger.debug(
                "Skipped loading agent profile from '{}' because it was disabled",
                str(directory),
            )
        else:
            self._logger.debug(
                "Retrieved agent profile {} from agent profile project folder: {}",
                repr(agent_profile),
                str(directory),
            )
        return agent_profile

    @log_and_propagate_error_on_service_method
    def get_all_agent_profiles_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> tuple[
        list[AgentProfile],
        list[pathlib.Path],
        list[tuple[pathlib.Path, AgentProfileLoadingError]] | None,
    ]:
        """Recursively scans a directory for agent profile project folders and instantiates them.

        Args:
            directory: The directory to scan for agent profile project
                folders.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in each profile's manifest. Defaults to `False`.

        Returns:
            A three-element tuple: (1) a list of successfully instantiated agent
            profiles, (2) a list of paths skipped because the profile was disabled,
            and (3) a list of `(path, error)` tuples for profiles that failed to
            load.
        """
        retrieved, skipped, errored = (
            self._agent_profile_registry_service.get_all_components_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        self._logger.debug(
            "Retrieved agent profiles from '{}' ({} agent profile(s) retrieved, "
            "{} agent profile(s) skipped, {} agent profile(s) failed to load)",
            directory,
            len(retrieved),
            len(skipped),
            len(errored),
        )
        return (
            retrieved,
            skipped,
            errored,
        )

    @log_and_propagate_error_on_service_method
    async def load_agent_profile(self, agent_profile: AgentProfile) -> None:
        """Registers and activates an already-instantiated agent profile.

        After loading, agent type references across all profiles are resolved, and the
        compatible agent type index for listener profiles is updated.

        Args:
            agent_profile: The agent profile instance to load.
        """
        agent_profile = await self._agent_profile_registry_service.load_component(
            component=agent_profile,
        )
        server_singletons.c2_types_service._resolve_agent_type_references()
        server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles()
        self._logger.debug("Loaded agent profile: {}", agent_profile)

    @log_and_propagate_error_on_service_method
    async def load_agent_profile_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> AgentProfile | None:
        """Loads an agent profile from a project folder, registering and activating it.

        Disabled profiles are skipped unless `ignore_enabled_flag` is
        `True`. After a successful load, agent type references and the compatible agent
        type index for listener profiles are updated.

        Args:
            directory: Path to the directory
                containing the agent profile project files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in the manifest. Defaults to `False`.

        Returns:
            The loaded agent profile, or `None` if the profile is
                disabled and the enabled check is not overridden.

        Raises:
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the profile is incompatible
                with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs while
                loading the profile.
        """
        agent_profile = (
            await self._agent_profile_registry_service.load_component_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        if agent_profile is None:
            self._logger.warning(
                "Agent profile could not be loaded from {} because it is "
                "currently disabled. Either enable it in its manifest or force "
                "load it by setting the `ignore_enabled_flag` to "
                "`True`.",
                str(directory),
            )
        else:
            server_singletons.c2_types_service._resolve_agent_type_references()
            server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles()
        self._logger.debug("Loaded agent profile: {}", agent_profile)
        return agent_profile

    @log_and_propagate_error_on_service_method
    async def unload_agent_profile_by_agent_profile_id(
        self,
        agent_profile_id: str | uuid.UUID,
    ) -> None:
        """Deactivates and deregisters a loaded agent profile by its ID.

        After unloading, the compatible agent type index for listener profiles is
        updated to reflect the removal.

        Args:
            agent_profile_id: The ID of the agent profile to unload.

        Raises:
            ComponentNotFoundError: If no agent profile with the given ID is registered.
        """
        agent_profile = await (
            self._agent_profile_registry_service.unload_component_by_component_id(
                component_id=agent_profile_id,
            )
        )
        server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles()
        self._logger.info("Unloaded agent profile: {}", agent_profile)
        self._logger.debug("Unloaded agent profile: {!r}", agent_profile)

    @log_and_propagate_error_on_service_method
    async def reload_agent_profile_by_agent_profile_id(
        self,
        agent_profile_id: str | uuid.UUID,
        ignore_enabled_flag: bool = False,
    ) -> AgentProfile:
        """Unloads and reloads an agent profile from its original project folder.

        After a successful reload, agent type references and the compatible agent type
        index for listener profiles are updated. If the profile is disabled after reload
        and `ignore_enabled_flag` is `False`, the profile will only be
        unloaded, not reloaded.

        Args:
            agent_profile_id: The ID of the agent profile to reload.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in the manifest during reload. Defaults to `False`.

        Returns:
            The reloaded agent profile instance, or `None` if the profile
                was disabled and the enabled check was not overridden.

        Raises:
            ComponentNotFoundError: If no agent profile with the given ID is registered.
        """
        agent_profile = await (
            self._agent_profile_registry_service.reload_component_by_component_id(
                component_id=agent_profile_id,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        if agent_profile is None:
            self._logger.warning(
                "Agent profile with ID '{}' could not be reloaded because it is "
                "currently disabled. Either enable it in its manifest or force "
                "reload it by setting the `ignore_enabled_flag` to "
                "`True`.",
                agent_profile_id,
            )
        else:
            server_singletons.c2_types_service._resolve_agent_type_references()
            server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles()
        self._logger.info("Reloaded agent profile: {}", agent_profile)
        self._logger.debug("Reloaded agent profile: {!r}", agent_profile)
        return agent_profile

    @log_and_propagate_error_on_service_method
    async def load_framework_agent_profiles(
        self,
        ignore_enabled_flag: bool = False,
    ) -> None:
        """Scans the framework's agent profiles directory and loads all enabled profiles.

        Disabled profiles and profiles that fail to load are logged and skipped without
        aborting the overall load.

        Args:
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in each profile's manifest. Defaults to `False`.
        """
        self._logger.info("Loading framework agent profiles...")
        retrieved, skipped, errored = self.get_all_agent_profiles_from_directory(
            directory=self._agents_directory,
            ignore_enabled_flag=ignore_enabled_flag,
        )
        for path in skipped:
            self._logger.info(
                "- Skipped loading agent profile from '{}' because it was disabled",
                str(path),
            )
        if errored:
            for _, error in errored:
                self._logger.error(
                    "- {}",
                    str(error),
                )

        # TODO: Build in topological sorting after figuring out how to implement the
        #  dependency system?
        failed_to_load = 0
        for agent_profile in retrieved:
            try:
                await self.load_agent_profile(agent_profile=agent_profile)
                self._logger.success("- Loaded agent profile: {}", agent_profile)
                self._logger.debug("- Loaded agent profile: {!r}", agent_profile)
            except (
                AgentTemplatesFrameworkError,
                AgentProfilesServiceError,
            ) as exc:
                failed_to_load += 1
                self._logger.error("- {}", exc)

        self._logger.info(
            "Loaded agent profiles from '{}' ({} agent profile(s) loaded, "
            "{} agent profile(s) skipped, {} agent profile(s) failed to load)",
            str(self._agents_directory),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    @log_and_propagate_error_on_service_method
    async def unload_framework_agent_profiles(self) -> None:
        """Unloads all agent profiles that were loaded from the framework's profiles directory."""
        self._logger.info("Unloading framework agent profiles...")
        unloaded_agent_profiles = 0
        for agent_profile in self.get_all_agent_profiles():
            if agent_profile.root_directory.resolve().relative_to(
                self._agents_directory.resolve()
            ):
                await self.unload_agent_profile_by_agent_profile_id(
                    agent_profile_id=str(agent_profile.agent_profile_id),
                )
                unloaded_agent_profiles += 1
        self._logger.info(
            "Unloaded framework agent profiles ({} agent profile(s) unloaded)",
            unloaded_agent_profiles,
        )

    @log_and_propagate_error_on_service_method
    async def reload_framework_agent_profiles(self) -> None:
        """Unloads all framework agent profiles then reloads them from the profiles directory."""
        self._logger.info("Reloading framework agent profiles...")
        await self.unload_framework_agent_profiles()
        await self.load_framework_agent_profiles()
        self._logger.info("Reloaded framework agent profiles")

    @log_and_propagate_error_on_service_method
    def get_all_agent_profiles(self) -> list[AgentProfile]:
        """Returns all currently loaded agent profiles.

        Returns:
            A list of all loaded agent profiles. Empty if none are
                loaded.
        """
        agent_profiles = self._agent_profile_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all agent profiles ({} retrieved)",
            len(agent_profiles),
        )
        return agent_profiles

    @log_and_propagate_error_on_service_method
    def get_agent_profile_by_agent_profile_id(
        self, agent_profile_id: str | uuid.UUID
    ) -> AgentProfile:
        """Returns a loaded agent profile by its ID.

        Args:
            agent_profile_id: The ID of the agent profile to retrieve.

        Returns:
            The requested agent profile.

        Raises:
            ComponentNotFoundError: If no agent profile with the given ID is registered.
        """
        agent_profile_id = normalize_uuid(agent_profile_id)

        agent_profile = (
            self._agent_profile_registry_service.get_component_by_component_id(
                component_id=agent_profile_id,
            )
        )
        self._logger.debug("Retrieved agent profile: {!r}", agent_profile)
        return agent_profile
