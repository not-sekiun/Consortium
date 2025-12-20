import pathlib
import uuid

from loguru import logger

from consortium.server.exceptions.consortium_exceptions.listener_templates_consortium_exceptions import (
    ListenerTemplatesFrameworkError,
)
from consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions import (  # InternalListenerProjectError,; InvalidListenerProjectFolderStructureError,; InvalidListenerProjectImplementationError,; InvalidListenerProjectManifestFileError,; InvalidListenerProjectManifestFileJSONError,; InvalidListenerProjectManifestFileSchemaError,; ListenerProjectInterfaceError,; ListenerProjectListenerFileNotFoundError,; ListenerProjectListenerTemplateFileNotFoundError,; ListenerProjectListenerTypeFileNotFoundError,; ListenerProjectManifestFileNotFoundError,; ListenerProjectSymbolNotFoundError,; InvalidListenerProfileProjectImplementationError,
    ListenerProfileLoadingError,
    ListenerProfilesServiceError,
)
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.server_config import CONSORTIUM_LISTENERS_DIRECTORY_PATH
from consortium.server.server_logging import LoggerType
from consortium.server.services.component_loader_services.listener_profile_loader_service import (
    ListenerProfileLoaderService,
)
from consortium.server.services.component_registry_services.listener_profile_registry_service import (
    ListenerProfileRegistryService,
)
from consortium.server.utils import log_and_propagate_error_on_service_method


# The listener profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API does not have access to this service.
class ListenerProfilesService:
    def __init__(self):
        self._listener_profile_loader_service = ListenerProfileLoaderService()
        self._listener_profile_registry_service = ListenerProfileRegistryService(
            component_loader_service=self._listener_profile_loader_service,
            component_framework_directory=CONSORTIUM_LISTENERS_DIRECTORY_PATH,
        )
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Listener Profiles Service"

    def __repr__(self) -> str:
        return "ListenerProfilesService()"

    @log_and_propagate_error_on_service_method
    def get_listener_profile_from_listener_profile_project_folder(
        self,
        listener_profile_project_folder: pathlib.Path,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> ListenerProfile | None:
        listener_profile = self._listener_profile_registry_service.get_component_from_component_project_folder(
            component_project_folder=listener_profile_project_folder,
            ignore_enabled_component_flag=ignore_enabled_listener_profile_flag,
        )
        if listener_profile is None:
            self._logger.debug(
                "Skipped loading listener profile from '{}' because it was disabled.",
                str(listener_profile_project_folder),
            )
        else:
            self._logger.debug(
                "Retrieved listener profile {} from listener profile project "
                "folder: {}",
                repr(listener_profile),
                str(listener_profile_project_folder),
            )
        return listener_profile

    @log_and_propagate_error_on_service_method
    def get_listener_profiles_from_listener_profile_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> tuple[
        list[ListenerProfile],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ListenerProfileLoadingError]] | None,
    ]:
        retrieved, skipped, errored = (
            self._listener_profile_registry_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_listener_profile_flag,
            )
        )
        self._logger.debug(
            "Retrieved listener profiles from '{}' ({} listener profile(s) "
            "retrieved, {} listener profile(s) skipped, {} listener profile(s) "
            "failed to load)",
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
    async def load_listener_profile(self, listener_profile: ListenerProfile) -> None:
        listener_profile = await self._listener_profile_registry_service.load_component(
            component=listener_profile,
        )
        self._logger.debug("Loaded listener profile: {}", listener_profile)

    @log_and_propagate_error_on_service_method
    async def load_listener_profile_from_listener_profile_project_folder(
        self,
        listener_profile_project_folder: pathlib.Path,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> ListenerProfile | None:
        listener_profile = await self._listener_profile_registry_service.load_component_from_component_project_folder(
            component_project_folder=listener_profile_project_folder,
            ignore_enabled_component_flag=ignore_enabled_listener_profile_flag,
        )
        if listener_profile is None:
            self._logger.warning(
                "Listener profile could not be loaded from {} because it is "
                "currently disabled. Either enable it in its manifest or force "
                "load it by setting the `ignore_enabled_listener_profile_flag` to "
                "`True`.",
                str(listener_profile_project_folder),
            )
        self._logger.debug("Loaded listener profile: {}", listener_profile)
        return listener_profile

    @log_and_propagate_error_on_service_method
    async def unload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str | uuid.UUID,
    ) -> None:
        listener_profile = await (
            self._listener_profile_registry_service.unload_component_by_component_id(
                component_id=listener_profile_id,
            )
        )
        self._logger.info("Unloaded listener profile: {}", listener_profile)
        self._logger.debug("Unloaded listener profile: {!r}", listener_profile)

    @log_and_propagate_error_on_service_method
    async def reload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str | uuid.UUID,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> ListenerProfile:
        listener_profile = await (
            self._listener_profile_registry_service.reload_component_by_component_id(
                component_id=listener_profile_id,
                ignore_enabled_component_flag=ignore_enabled_listener_profile_flag,
            )
        )
        if listener_profile is None:
            self._logger.warning(
                "Listener profile with ID '{}' could not be reloaded because it is "
                "currently disabled. Either enable it in its manifest or force "
                "reload it by setting the `ignore_enabled_listener_profile_flag` to "
                "`True`.",
                listener_profile_id,
            )
        self._logger.info("Reloaded listener profile: {}", listener_profile)
        self._logger.debug("Reloaded listener profile: {!r}", listener_profile)
        return listener_profile

    @log_and_propagate_error_on_service_method
    async def load_framework_listener_profiles(
        self,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> None:
        self._logger.info("Loading framework listener profiles...")
        retrieved, skipped, errored = (
            self.get_listener_profiles_from_listener_profile_project_folder_directories(
                directory=CONSORTIUM_LISTENERS_DIRECTORY_PATH,
                ignore_enabled_listener_profile_flag=ignore_enabled_listener_profile_flag,
            )
        )
        for path in skipped:
            self._logger.info(
                "- Skipped loading listener profile from '{}' because it was disabled.",
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
        for listener_profile in retrieved:
            try:
                await self.load_listener_profile(listener_profile=listener_profile)
                self._logger.success("- Loaded listener profile: {}", listener_profile)
                self._logger.debug("- Loaded listener profile: {!r}", listener_profile)
            except (
                ListenerTemplatesFrameworkError,
                ListenerProfilesServiceError,
            ) as exc:
                failed_to_load += 1
                self._logger.error("- {}", exc)

        self._logger.info(
            "Loaded listener profiles from '{}' ({} listener profile(s) loaded, "
            "{} listener profile(s) skipped, {} listener profile(s) failed to load).",
            str(CONSORTIUM_LISTENERS_DIRECTORY_PATH),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    @log_and_propagate_error_on_service_method
    async def unload_framework_listener_profiles(self) -> None:
        self._logger.info("Unloading framework listener profiles...")
        unloaded_listener_profiles = 0
        for listener_profile in self.get_all_listener_profiles():
            if (
                listener_profile.listener_project_folder.parent
                == CONSORTIUM_LISTENERS_DIRECTORY_PATH
            ):
                await self.unload_listener_profile_by_listener_profile_id(
                    listener_profile_id=str(listener_profile.listener_profile_id),
                )
                unloaded_listener_profiles += 1
        self._logger.info(
            "Unloaded framework listener profiles ({} listener profile(s) unloaded).",
            unloaded_listener_profiles,
        )

    @log_and_propagate_error_on_service_method
    async def reload_framework_listener_profiles(self) -> None:
        self._logger.info("Reloading framework listener profiles...")
        await self.unload_framework_listener_profiles()
        await self.load_framework_listener_profiles()
        self._logger.info("Reloaded framework listener profiles.")

    @log_and_propagate_error_on_service_method
    def get_all_listener_profiles(self) -> list[ListenerProfile]:
        listener_profiles = self._listener_profile_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all listener profiles ({} retrieved).",
            len(listener_profiles),
        )
        return listener_profiles

    @log_and_propagate_error_on_service_method
    def get_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str | uuid.UUID,
    ) -> ListenerProfile:
        listener_profile = (
            self._listener_profile_registry_service.get_component_by_component_id(
                component_id=listener_profile_id,
            )
        )
        self._logger.debug("Retrieved listener profile: {!r}", listener_profile)
        return listener_profile
