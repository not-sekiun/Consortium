import pathlib
import uuid

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.consortium_exceptions.agent_profiles_consortium_exceptions import (
    AgentProfileLoadingError,
    AgentProfilesServiceError,
)
from consortium.server.exceptions.consortium_exceptions.agent_templates_consortium_exceptions import (
    AgentTemplatesFrameworkError,
)
from consortium.server.objects.c2_profile_objects import AgentProfile
from consortium.server.server_logging import LoggerType
from consortium.server.services.component_loader_services.agent_profile_loader_service import (
    AgentProfileLoaderService,
)
from consortium.server.services.component_registry_services.agent_profile_registry_service import (
    AgentProfileRegistryService,
)
from consortium.server.services.release_service import ReleaseService
from consortium.server.utils import log_and_propagate_error_on_service_method


# The agent profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API should not have access to this service.
class AgentProfilesService:
    def __init__(
        self,
        release_service: ReleaseService,
        agents_directory: pathlib.Path,
        consortium_root: pathlib.Path,
    ) -> None:
        self._agents_directory = agents_directory
        self._agent_profile_loader_service = AgentProfileLoaderService(
            consortium_root=consortium_root,
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
    def get_agent_profile_from_agent_profile_project_folder(
        self,
        agent_profile_project_folder: pathlib.Path,
        ignore_enabled_agent_profile_flag: bool = False,
    ) -> AgentProfile | None:
        agent_profile = self._agent_profile_registry_service.get_component_from_component_project_folder(
            component_project_folder=agent_profile_project_folder,
            ignore_enabled_component_flag=ignore_enabled_agent_profile_flag,
        )
        if agent_profile is None:
            self._logger.debug(
                "Skipped loading agent profile from '{}' because it was disabled.",
                str(agent_profile_project_folder),
            )
        else:
            self._logger.debug(
                "Retrieved agent profile {} from agent profile project folder: {}",
                repr(agent_profile),
                str(agent_profile_project_folder),
            )
        return agent_profile

    @log_and_propagate_error_on_service_method
    def get_agent_profiles_from_agent_profile_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_agent_profile_flag: bool = False,
    ) -> tuple[
        list[AgentProfile],
        list[pathlib.Path],
        list[tuple[pathlib.Path, AgentProfileLoadingError]] | None,
    ]:
        retrieved, skipped, errored = (
            self._agent_profile_registry_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_agent_profile_flag,
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
        agent_profile = await self._agent_profile_registry_service.load_component(
            component=agent_profile,
        )
        server_singletons.c2_types_service._resolve_agent_type_references()
        server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles()
        self._logger.debug("Loaded agent profile: {}", agent_profile)

    @log_and_propagate_error_on_service_method
    async def load_agent_profile_from_agent_profile_project_folder(
        self,
        agent_profile_project_folder: pathlib.Path,
        ignore_enabled_agent_profile_flag: bool = False,
    ) -> AgentProfile | None:
        agent_profile = await self._agent_profile_registry_service.load_component_from_component_project_folder(
            component_project_folder=agent_profile_project_folder,
            ignore_enabled_component_flag=ignore_enabled_agent_profile_flag,
        )
        if agent_profile is None:
            self._logger.warning(
                "Agent profile could not be loaded from {} because it is "
                "currently disabled. Either enable it in its manifest or force "
                "load it by setting the `ignore_enabled_agent_profile_flag` to "
                "`True`.",
                str(agent_profile_project_folder),
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
        ignore_enabled_agent_profile_flag: bool = False,
    ) -> AgentProfile:
        agent_profile = await (
            self._agent_profile_registry_service.reload_component_by_component_id(
                component_id=agent_profile_id,
                ignore_enabled_component_flag=ignore_enabled_agent_profile_flag,
            )
        )
        if agent_profile is None:
            self._logger.warning(
                "Agent profile with ID '{}' could not be reloaded because it is "
                "currently disabled. Either enable it in its manifest or force "
                "reload it by setting the `ignore_enabled_agent_profile_flag` to "
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
        ignore_enabled_agent_profile_flag: bool = False,
    ) -> None:
        self._logger.info("Loading framework agent profiles...")
        retrieved, skipped, errored = (
            self.get_agent_profiles_from_agent_profile_project_folder_directories(
                directory=self._agents_directory,
                ignore_enabled_agent_profile_flag=ignore_enabled_agent_profile_flag,
            )
        )
        for path in skipped:
            self._logger.info(
                "- Skipped loading agent profile from '{}' because it was disabled.",
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
            "{} agent profile(s) skipped, {} agent profile(s) failed to load).",
            str(self._agents_directory),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    @log_and_propagate_error_on_service_method
    async def unload_framework_agent_profiles(self) -> None:
        self._logger.info("Unloading framework agent profiles...")
        unloaded_agent_profiles = 0
        for agent_profile in self.get_all_agent_profiles():
            if agent_profile.agent_project_folder.parent == self._agents_directory:
                await self.unload_agent_profile_by_agent_profile_id(
                    agent_profile_id=str(agent_profile.agent_profile_id),
                )
                unloaded_agent_profiles += 1
        self._logger.info(
            "Unloaded framework agent profiles ({} agent profile(s) unloaded).",
            unloaded_agent_profiles,
        )

    @log_and_propagate_error_on_service_method
    async def reload_framework_agent_profiles(self) -> None:
        self._logger.info("Reloading framework agent profiles...")
        await self.unload_framework_agent_profiles()
        await self.load_framework_agent_profiles()
        self._logger.info("Reloaded framework agent profiles.")

    @log_and_propagate_error_on_service_method
    def get_all_agent_profiles(self) -> list[AgentProfile]:
        agent_profiles = self._agent_profile_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all agent profiles ({} retrieved).",
            len(agent_profiles),
        )
        return agent_profiles

    @log_and_propagate_error_on_service_method
    def get_agent_profile_by_agent_profile_id(
        self, agent_profile_id: str | uuid.UUID
    ) -> AgentProfile:
        agent_profile = (
            self._agent_profile_registry_service.get_component_by_component_id(
                component_id=agent_profile_id,
            )
        )
        self._logger.debug("Retrieved agent profile: {!r}", agent_profile)
        return agent_profile
