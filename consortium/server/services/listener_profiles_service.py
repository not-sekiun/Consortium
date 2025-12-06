# import importlib
# import json
# from pathlib import Path
import pathlib

# import jsonschema
from loguru import logger

# from consortium.framework.listeners.base_listener import BaseListener
# from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
# from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.framework.utils.exception_utils import remap_exception
from consortium.server.exceptions.framework_exceptions.listener_template_framework_exceptions import (
    ListenerTemplatesFrameworkError,
)
from consortium.server.exceptions.service_exceptions import (
    component_loader_service_exceptions as comp_ldr_svc_excs,
)
from consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions import (  # InternalListenerProjectError,; InvalidListenerProjectFolderStructureError,; InvalidListenerProjectImplementationError,; InvalidListenerProjectManifestFileError,; InvalidListenerProjectManifestFileJSONError,; InvalidListenerProjectManifestFileSchemaError,; ListenerProjectInterfaceError,; ListenerProjectListenerFileNotFoundError,; ListenerProjectListenerTemplateFileNotFoundError,; ListenerProjectListenerTypeFileNotFoundError,; ListenerProjectManifestFileNotFoundError,; ListenerProjectSymbolNotFoundError,; InvalidListenerProfileProjectImplementationError,
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
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
    ListenerProfileProjectInterfaceError,
    ListenerProfileProjectListenerProfileFileNotFoundError,
    ListenerProfileProjectManifestFileNotFoundError,
    ListenerProfileProjectSymbolNotFoundError,
    ListenerProfilesServiceError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    CONSORTIUM_LISTENER_PROFILES_DIRECTORY_PATH,
)
from consortium.server.services.component_loader_services.listener_profile_loader_service import (
    ListenerProfileLoaderService,
)


# The listener profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API does not have access to this service.
class ListenerProfilesService:
    _EXCEPTION_MAP = {
        comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError: ListenerProfileProjectManifestFileNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError: InvalidListenerProfileProjectManifestFileJSONError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError: InvalidListenerProfileProjectManifestFileSchemaError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError: InvalidListenerProfileProjectPyProjectFileError,
        comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidListenerProfileProjectPyProjectFileDependencyError,
        comp_ldr_svc_excs.ComponentProjectComponentFileNotFoundError: ListenerProfileProjectListenerProfileFileNotFoundError,
        comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError: ListenerProfileProjectSymbolNotFoundError,
        comp_ldr_svc_excs.ComponentProjectInterfaceError: ListenerProfileProjectInterfaceError,
        comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError: IncompatibleListenerProfileFrameworkVersionError,
        comp_ldr_svc_excs.InternalComponentProjectError: InternalListenerProfileProjectError,
        comp_ldr_svc_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_ldr_svc_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError: ListenerProfileDependsOnInvalidComponentDependencyError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "listener_profile_project_folder",
        "component_file": "listener_profile_file",
        "component_symbol": "listener_profile_symbol",
        "component_str": "listener_profile_str",
        "component_id": "listener_profile_id",
    }

    def __init__(self):
        self._listener_profiles = {}
        self._listener_profile_loader_service = ListenerProfileLoaderService()
        self.logger = logger.bind(
            logger_name=str(self),
        )
        self.logger.debug(
            f"Started {self}.",
        )

    def __str__(self) -> str:
        return "Listener Profiles Service"

    def __repr__(self) -> str:
        return "ListenerProfilesService()"

    def get_listener_profile_from_listener_profile_project_folder(
        self,
        listener_profile_project_folder: pathlib.Path,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> ListenerProfile | None:
        try:
            listener_profile = self._listener_profile_loader_service.get_component_from_component_project_folder(
                component_project_folder=listener_profile_project_folder,
                ignore_enabled_component_flag=ignore_enabled_listener_profile_flag,
            )
        except (
            comp_ldr_svc_excs.ComponentLoadingError,
            comp_ldr_svc_excs.ComponentDependencyError,
        ) as exc:
            print("ASDADAHIDHAJKDSHAKJDJKSA")
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=self._EXCEPTION_MAP,
                exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
            ) from None
        if listener_profile is None:
            self.logger.debug(
                "Skipped loading listener profile from '{}' because it was disabled.",
                str(listener_profile_project_folder),
            )
        else:
            self.logger.debug(
                "Retrieved listener profile {} from listener profile project folder: {}",
                repr(listener_profile),
                str(listener_profile_project_folder),
            )
        return listener_profile

    def get_listener_profiles_from_listener_profile_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> tuple[
        list[ListenerProfile],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ListenerProfileLoadingError]] | None,
    ]:
        """
        Retrieves all listener profiles from the specified directory containing listener profile project folders.

        Event Hooks that are specified to be disabled in their `manifest.json` will not be
        loaded unless `ignore_enabled_listener_profile_flag` is set to `True`. Valid listener profiles are
        instantiated and returned.

        Args:
            directory (pathlib.Path): The path of the directory containing listener profile
                project folders.
            ignore_enabled_listener_profile_flag (bool): If `True`, the method bypasses the
                enabled state check in the listener profile project manifests.

        Returns:
            tuple[list[BaseEventHook], list[pathlib.Path], list[tuple[pathlib.Path, EventHookLoadingError]] | None]:
                A tuple containing three elements:
                1. A list of successfully retrieved listener profile instances.
                2. A list of pathlib.Path objects representing the listener profile project
                    folders that were skipped because the listener profiles were disabled.
                3. A list of tuples, each containing a pathlib.Path object representing
                    the listener profile project folder that failed to load and the corresponding
                    `EventHookLoadingError` exception.

        Raises:
            See [get_listener_profile_from_listener_profile_project_folder][consortium.server.services.listener_profiles_service.EventHooksService.get_listener_profile_from_listener_profile_project_folder]
            for possible exceptions raised during listener profile retrieval.
        """
        retrieved, skipped, errored = (
            self._listener_profile_loader_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_listener_profile_flag,
            )
        )
        remapped_errored = []
        for error_tuple in errored:
            error = error_tuple[1]
            # A configuration error will raise a EventHookConfigurationError which is not
            # a ComponentLoadingError, so we only remap ComponentLoadingErrors here.
            if isinstance(
                error,
                (
                    comp_ldr_svc_excs.ComponentLoadingError,
                    comp_ldr_svc_excs.ComponentDependencyError,
                ),
            ):
                remapped_errored.append(
                    (
                        error_tuple[0],
                        remap_exception(
                            original_exception=error,
                            original_kwargs=error.kwargs,
                            exception_map=self._EXCEPTION_MAP,
                            exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
                        ),
                    ),
                )
            else:
                remapped_errored.append(error_tuple)
        self.logger.debug(
            "Retrieved listener profiles from '{}' ({} listener profile(s) retrieved, {} listener profile(s) "
            "skipped, {} listener profile(s) failed to load)",
            directory,
            len(retrieved),
            len(skipped),
            len(remapped_errored),
        )
        return (
            retrieved,
            skipped,
            remapped_errored,
        )

    def load_listener_profile(self, listener_profile: ListenerProfile) -> None:
        if str(listener_profile.listener_profile_id) in self._listener_profiles:
            raise ListenerProfileAlreadyRegisteredError(
                listener_profile_str=str(listener_profile),
                listener_profile_id=str(listener_profile.listener_profile_id),
            )
        self._listener_profiles[str(listener_profile.listener_profile_id)] = (
            listener_profile
        )
        self.logger.debug(
            f"Loaded listener profile: {listener_profile}",
        )

    def load_listener_profile_from_listener_profile_project_folder(
        self,
        listener_profile_project_folder: pathlib.Path,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> ListenerProfile | None:
        listener_profile = self.get_listener_profile_from_listener_profile_project_folder(
            listener_profile_project_folder,
            ignore_enabled_listener_profile_flag=ignore_enabled_listener_profile_flag,
        )
        if listener_profile is None:
            return None
        self.load_listener_profile(listener_profile=listener_profile)
        return listener_profile

    def unload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str,
    ) -> None:
        try:
            listener_profile = self._listener_profiles.pop(listener_profile_id)
        except KeyError:
            raise ListenerProfileNotFoundError(
                listener_profile_id=listener_profile_id,
            )
        self.logger.info("Unloaded listener profile: {}", listener_profile)
        self.logger.debug("Unloaded listener profile: {!r}", listener_profile)

    def reload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id: str,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> ListenerProfile:
        try:
            listener_profile = self._listener_profiles.pop(listener_profile_id)
        except KeyError:
            raise ListenerProfileNotFoundError(
                listener_profile_id=listener_profile_id,
            )
        listener_profile = self.load_listener_profile_from_listener_profile_project_folder(
            listener_profile_project_folder=listener_profile.listener_project_folder_path,
            ignore_enabled_listener_profile_flag=ignore_enabled_listener_profile_flag,
        )
        self.logger.info("Reloaded listener profile: {}", listener_profile)
        self.logger.debug("Reloaded listener profile: {!r}", listener_profile)
        return listener_profile

    def load_framework_listener_profiles(
        self,
        ignore_enabled_listener_profile_flag: bool = False,
    ) -> None:
        self.logger.info("Loading framework listener profiles...")
        retrieved, skipped, errored = (
            self.get_listener_profiles_from_listener_profile_project_folder_directories(
                directory=CONSORTIUM_LISTENER_PROFILES_DIRECTORY_PATH,
                ignore_enabled_listener_profile_flag=ignore_enabled_listener_profile_flag,
            )
        )
        for path in skipped:
            self.logger.info(
                "├─ Skipped loading listener profile from '{}' because it was disabled.",
                str(path),
            )
        if errored:
            for _, error in errored:
                self.logger.error(
                    "├─ {}",
                    str(error),
                )

        # TODO: Build in topological sorting after figuring out how to implement the
        #  dependency system?
        failed_to_load = 0
        for listener_profile in retrieved:
            try:
                self.load_listener_profile(listener_profile=listener_profile)
                self.logger.success("├─ Loaded listener profile: {}", listener_profile)
                self.logger.debug("├─ Loaded listener profile: {!r}", listener_profile)
            except (
                ListenerTemplatesFrameworkError,
                ListenerProfilesServiceError,
            ) as exc:
                failed_to_load += 1
                self.logger.error("├─ {}", exc)

        self.logger.info(
            "└─ Loaded listener profiles from '{}' ({} listener profile(s) loaded, {} listener profile(s) "
            "skipped, {} listener profile(s) failed to load).",
            str(CONSORTIUM_LISTENER_PROFILES_DIRECTORY_PATH),
            len(retrieved) - failed_to_load,
            len(skipped),
            len(errored) + failed_to_load,
        )

    def unload_framework_listener_profiles(self) -> None:
        self.logger.info("Unloading framework listener profiles...")
        unloaded_listener_profiles = 0
        for listener_profile in self.get_all_listener_profiles():
            if (
                listener_profile.event_hook_project_folder.parent
                == CONSORTIUM_LISTENER_PROFILES_DIRECTORY_PATH
            ):
                self.unload_listener_profile_by_listener_profile_id(
                    listener_profile_id=str(listener_profile.listener_profile_id),
                )
                unloaded_listener_profiles += 1
        self.logger.info(
            "Unloaded framework listener profiles ({} listener profile(s) unloaded).",
            unloaded_listener_profiles,
        )

    def reload_framework_listener_profiles(self) -> None:
        self.logger.info("Reloading framework listener profiles...")
        self.unload_framework_listener_profiles()
        self.load_framework_listener_profiles()
        self.logger.info("Reloaded framework listener profiles.")

    def get_all_listener_profiles(self):
        all_listener_profiles = list(self._listener_profiles.values())
        self.logger.debug(
            f"Retrieved all listener profiles ({len(all_listener_profiles)} "
            "retrieved).",
        )
        return all_listener_profiles

    def get_listener_profile_by_listener_profile_id(self, listener_profile_id):
        try:
            listener_profile = self._listener_profiles[listener_profile_id]
        except KeyError:
            raise ListenerProfileNotFoundError(
                listener_profile_id=listener_profile_id,
            )

        self.logger.debug(
            f"Retrieved listener profile: {listener_profile!r}",
        )
        return listener_profile
