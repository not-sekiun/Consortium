import pathlib
import uuid

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework._core.framework_exceptions.listener_templates_framework_exceptions import (
    ListenerTemplatesFrameworkError,
)
from consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions import (
    ListenerProfileLoadingError,
    ListenerProfilesServiceError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.services.component_loader_services.listener_profile_loader_service import (
    ListenerProfileLoaderService,
)
from consortium.server.services.component_registry_services.listener_profile_registry_service import (
    ListenerProfileRegistryService,
)
from consortium.server.services.paths_service import PathsService
from consortium.server.services.release_service import ReleaseService
from consortium.server.utils import log_and_propagate_error_on_service_method


# The listener profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API does not have access to this service.
class ListenerProfilesService:
    def __init__(
        self,
        release_service: ReleaseService,
        paths_service: PathsService,
    ) -> None:
        self._listeners_directory = paths_service.listeners_directory
        self._listener_profile_loader_service = ListenerProfileLoaderService(
            release_service=release_service,
            paths_service=paths_service,
        )
        self._listener_profile_registry_service = ListenerProfileRegistryService(
            component_loader_service=self._listener_profile_loader_service,
            component_framework_directory=self._listeners_directory,
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
    def get_listener_profile_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> ListenerProfile | None:
        """Instantiates a listener profile from a directory without registering it.

        Disabled listener profiles (as indicated by `enabled: false` in their
        `manifest.json`) are not instantiated unless
        `ignore_enabled_flag` is `True`.

        Args:
            directory: Path to the directory
                containing the listener profile project files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in the manifest. Defaults to `False`.

        Returns:
            The instantiated listener profile, or `None` if the
                profile is disabled and the enabled check is not overridden.

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
        listener_profile = (
            self._listener_profile_registry_service.get_component_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        if listener_profile is None:
            self._logger.debug(
                "Skipped loading listener profile from '{}' because it was disabled",
                str(directory),
            )
        else:
            self._logger.debug(
                "Retrieved listener profile {} from listener profile project "
                "folder: {}",
                repr(listener_profile),
                str(directory),
            )
        return listener_profile

    @log_and_propagate_error_on_service_method
    def get_all_listener_profiles_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> tuple[
        list[ListenerProfile],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ListenerProfileLoadingError]] | None,
    ]:
        """Recursively scans a directory for listener profiles and instantiates them.

        Args:
            directory: The directory to scan for listener profiles.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in each profile's manifest. Defaults to `False`.

        Returns:
            A three-element tuple: (1) a list of successfully instantiated listener
            profiles, (2) a list of paths skipped because the profile was disabled,
            and (3) a list of `(path, error)` tuples for profiles that failed to
            load.
        """
        retrieved, skipped, errored = (
            self._listener_profile_registry_service.get_all_components_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
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
        """Registers and activates an already-instantiated listener profile.

        After loading, the compatible agent type index for this listener profile is
        updated.

        Args:
            listener_profile: The listener profile instance to load.
        """
        listener_profile = await self._listener_profile_registry_service.load_component(
            component=listener_profile,
        )
        server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles(
            listener_profile
        )
        self._logger.debug("Loaded listener profile: {}", listener_profile)

    @log_and_propagate_error_on_service_method
    async def load_listener_profile_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> ListenerProfile | None:
        """Loads a listener profile from a directory, registering and activating it.

        Disabled profiles are skipped unless `ignore_enabled_flag` is
        `True`. After a successful load, the compatible agent type index for this
        listener profile is updated.

        Args:
            directory: Path to the directory
                containing the listener profile project files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in the manifest. Defaults to `False`.

        Returns:
            The loaded listener profile, or `None` if the
                profile is disabled and the enabled check is not overridden.

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
        listener_profile = (
            await self._listener_profile_registry_service.load_component_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        if listener_profile is None:
            self._logger.warning(
                "Listener profile could not be loaded from {} because it is "
                "currently disabled. Either enable it in its manifest or force "
                "load it by setting the `ignore_enabled_flag` to "
                "`True`.",
                str(directory),
            )
        else:
            server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles(
                listener_profile
            )
        self._logger.debug("Loaded listener profile: {}", listener_profile)
        return listener_profile

    @log_and_propagate_error_on_service_method
    async def unload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str | uuid.UUID,
    ) -> None:
        """Deactivates and deregisters a loaded listener profile by its ID.

        Args:
            listener_profile_id: The ID of the listener profile to
                unload.

        Raises:
            ComponentNotFoundError: If no listener profile with the given ID is
                registered.
        """
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
        ignore_enabled_flag: bool = False,
    ) -> ListenerProfile:
        """Unloads and reloads a listener profile from its original directory.

        If the profile is disabled after reload and `ignore_enabled_flag`
        is `False`, the profile will only be unloaded, not reloaded.

        Args:
            listener_profile_id: The ID of the listener profile to
                reload.
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in the manifest during reload. Defaults to `False`.

        Returns:
            The reloaded listener profile instance, or `None` if the
                profile was disabled and the enabled check was not overridden.

        Raises:
            ComponentNotFoundError: If no listener profile with the given ID is
                registered.
        """
        listener_profile = await (
            self._listener_profile_registry_service.reload_component_by_component_id(
                component_id=listener_profile_id,
                ignore_enabled_component_flag=ignore_enabled_flag,
            )
        )
        if listener_profile is None:
            self._logger.warning(
                "Listener profile with ID '{}' could not be reloaded because it is "
                "currently disabled. Either enable it in its manifest or force "
                "reload it by setting the `ignore_enabled_flag` to "
                "`True`.",
                listener_profile_id,
            )
        else:
            server_singletons.c2_types_service._resolve_registered_compatible_agent_types_for_listener_profiles(
                listener_profile
            )
        self._logger.info("Reloaded listener profile: {}", listener_profile)
        self._logger.debug("Reloaded listener profile: {!r}", listener_profile)
        return listener_profile

    @log_and_propagate_error_on_service_method
    async def load_framework_listener_profiles(
        self,
        ignore_enabled_flag: bool = False,
    ) -> None:
        """Scans the framework's listener profiles directory and loads all enabled profiles.

        Disabled profiles and profiles that fail to load are logged and skipped without
        aborting the overall load.

        Args:
            ignore_enabled_flag: When `True`, bypasses the
                `enabled` check in each profile's manifest. Defaults to `False`.
        """
        self._logger.info("Loading framework listener profiles...")
        retrieved, skipped, errored = self.get_all_listener_profiles_from_directory(
            directory=self._listeners_directory,
            ignore_enabled_flag=ignore_enabled_flag,
        )
        for path in skipped:
            self._logger.info(
                "- Skipped loading listener profile from '{}' because it was disabled",
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
            "{} listener profile(s) skipped, {} listener profile(s) failed to load)",
            str(self._listeners_directory),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    @log_and_propagate_error_on_service_method
    async def unload_framework_listener_profiles(self) -> None:
        """Unloads all listener profiles that were loaded from the framework's profiles directory."""
        self._logger.info("Unloading framework listener profiles...")
        unloaded_listener_profiles = 0
        for listener_profile in self.get_all_listener_profiles():
            if listener_profile.root_directory.resolve().is_relative_to(
                self._listeners_directory.resolve()
            ):
                await self.unload_listener_profile_by_listener_profile_id(
                    listener_profile_id=str(listener_profile.listener_profile_id),
                )
                unloaded_listener_profiles += 1
        self._logger.info(
            "Unloaded framework listener profiles ({} listener profile(s) unloaded)",
            unloaded_listener_profiles,
        )

    @log_and_propagate_error_on_service_method
    async def reload_framework_listener_profiles(self) -> None:
        """Unloads all framework listener profiles then reloads them from the profiles directory."""
        self._logger.info("Reloading framework listener profiles...")
        await self.unload_framework_listener_profiles()
        await self.load_framework_listener_profiles()
        self._logger.info("Reloaded framework listener profiles")

    @log_and_propagate_error_on_service_method
    def get_all_listener_profiles(self) -> list[ListenerProfile]:
        """Returns all currently loaded listener profiles.

        Returns:
            A list of all loaded listener profiles. Empty if
                none are loaded.
        """
        listener_profiles = self._listener_profile_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all listener profiles ({} retrieved)",
            len(listener_profiles),
        )
        return listener_profiles

    @log_and_propagate_error_on_service_method
    def get_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str | uuid.UUID,
    ) -> ListenerProfile:
        """Returns a loaded listener profile by its ID.

        Args:
            listener_profile_id: The ID of the listener profile to
                retrieve.

        Returns:
            The requested listener profile.

        Raises:
            ComponentNotFoundError: If no listener profile with the given ID is
                registered.
        """
        listener_profile = (
            self._listener_profile_registry_service.get_component_by_component_id(
                component_id=listener_profile_id,
            )
        )
        self._logger.debug("Retrieved listener profile: {!r}", listener_profile)
        return listener_profile
