import importlib
import json
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.server.exceptions.internal_server_exceptions import (
    InternalListenerProjectError,
    InvalidListenerProjectFolderStructureError,
    InvalidListenerProjectImplementationError,
    InvalidListenerProjectManifestFileError,
)
from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.base_listener_template import BaseListenerTemplate
from consortium.server.framework.c2_types import ListenerType
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    CONSORTIUM_LISTENERS_DIRECTORY_PATH,
)


# The listener profiles service is an internal service that is meant to only be
# accessed by the server's internal services, plugins, and event hooks. The external
# forward facing REST API should not have access to this service.
class ListenerProfilesService:
    def __init__(self):
        self._listener_profiles = {}
        self.listener_profiles_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.listener_profiles_service_logger.debug(
            f"Started {self}.",
        )

    @staticmethod
    def get_listener_profile_from_listener_project_folder(
        listener_project_folder: Path,
    ) -> ListenerProfile:
        # Check if project folder contains a valid manifest file.
        listener_project_manifest_file = (
            listener_project_folder / "listener_project_manifest.json"
        )
        listener_project_manifest_json_schema = {
            "type": "object",
            "properties": {
                "listener": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
                "listener_template": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
                "listener_type": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                },
            },
        }

        # Check if manifest file exists and follows the correct json schema.
        try:
            with listener_project_manifest_file.open("r") as file:
                listener_project_manifest_json = json.load(fp=file)
                jsonschema.validate(
                    instance=listener_project_manifest_json,
                    schema=listener_project_manifest_json_schema,
                )
        except FileNotFoundError:
            raise InvalidListenerProjectFolderStructureError(
                "The listener project manifest file (listener_project_manifest.json) "
                "was not found in the listener project folder: "
                f"{listener_project_folder}",
            )
        except json.JSONDecodeError:
            raise InvalidListenerProjectManifestFileError(
                "The listener project manifest file (listener_project_manifest.json) "
                f'in the listener project folder "{listener_project_folder}" is not a '
                f"valid JSON file.",
            )
        except jsonschema.ValidationError as exc:
            raise InvalidListenerProjectManifestFileError(
                "The listener project manifest file (listener_project_manifest.json) "
                f'in the listener project folder "{listener_project_folder}" does not '
                f"follow the correct JSON schema: {exc}",
            )

        # Check for valid project folder structure as specified by the manifest file.
        listener_file = listener_project_folder / Path(
            listener_project_manifest_json["listener"]["filepath"],
        )
        listener_template_file = listener_project_folder / Path(
            listener_project_manifest_json["listener_template"]["filepath"],
        )
        listener_type_file = listener_project_folder / Path(
            listener_project_manifest_json["listener_type"]["filepath"],
        )

        if not listener_file.exists():
            raise InvalidListenerProjectFolderStructureError(
                f'The listener file "{listener_file}" specified in the listener '
                "project manifest file (listener_project_manifest.json) is missing for "
                f"listener project folder: {listener_project_folder}",
            )
        if not listener_template_file.exists():
            raise InvalidListenerProjectFolderStructureError(
                f'The listener template file "{listener_template_file}" specified in '
                "the listener project manifest file (listener_project_manifest.json) "
                f"is missing for listener project folder: {listener_project_folder}",
            )
        if not listener_type_file.exists():
            raise InvalidListenerProjectFolderStructureError(
                f'The listener type file "{listener_type_file}" specified in the '
                "listener project manifest file (listener_project_manifest.json) is "
                f"missing for listener project folder: {listener_project_folder}",
            )

        # Check for valid symbol names in the required listener project files.
        listener_module_path = ".".join(
            listener_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        listener_symbol = listener_project_manifest_json["listener"]["symbol"]
        listener_template_module_path = ".".join(
            listener_template_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        listener_template_symbol = listener_project_manifest_json["listener_template"][
            "symbol"
        ]
        listener_type_module_path = ".".join(
            listener_type_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        listener_type_symbol = listener_project_manifest_json["listener_type"]["symbol"]

        try:
            listener_module = importlib.import_module(listener_module_path)
            listener_class = getattr(
                listener_module,
                listener_symbol,
            )
        except (ImportError, AttributeError):
            raise InvalidListenerProjectFolderStructureError(
                f'The symbol name "{listener_symbol}" specified in the listener '
                "project manifest file (listener_project_manifest.json) was not found "
                f'in the listener file "{listener_file}" for listener project folder: '
                f"{listener_project_folder}",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                f"Failed to load listener from {listener_project_folder} due to an "
                f"exception that occurred while importing the listener: {exc}",
            )

        try:
            listener_template_module = importlib.import_module(
                listener_template_module_path,
            )
            listener_template_class = getattr(
                listener_template_module,
                listener_template_symbol,
            )
        except (ImportError, AttributeError):
            raise InvalidListenerProjectFolderStructureError(
                f'The symbol name "{listener_template_symbol}" specified in the '
                "listener project manifest file (listener_project_manifest.json) was "
                f'not found in the listener template file "{listener_template_file}" '
                f"for listener project folder: {listener_project_folder}",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                f"Failed to load listener template from {listener_project_folder} due "
                f"to an exception that occurred while importing the listener template: "
                f"{exc}",
            )

        try:
            listener_type_module = importlib.import_module(listener_type_module_path)
            listener_type = getattr(
                listener_type_module,
                listener_type_symbol,
            )
        except (ImportError, AttributeError):
            raise InvalidListenerProjectFolderStructureError(
                f'The symbol name "{listener_type_symbol}" specified in the listener '
                "project manifest file (listener_project_manifest.json) was not found "
                f'in the listener type file "{listener_type_file}" for listener '
                f"project folder: {listener_project_folder}",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                f"Failed to load listener type from {listener_project_folder} due to "
                f"an exception that occurred while importing the listener type: {exc}",
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(listener_class, BaseListener):
            raise InvalidListenerProjectImplementationError(
                "The symbol name of the listener class specified in the listener "
                "project manifest file (listener_project_manifest.json) does not inherit "
                "from the framework's base listener class for the listener project "
                f"folder: {listener_project_folder}",
            )
        if not issubclass(listener_template_class, BaseListenerTemplate):
            raise InvalidListenerProjectImplementationError(
                "The symbol name of the listener template class specified in the "
                "listener project manifest file (listener_project_manifest.json) does "
                "not inherit from the framework's base listener template class for the "
                f"listener project folder: {listener_project_folder}",
            )
        if not isinstance(listener_type, ListenerType):
            raise InvalidListenerProjectImplementationError(
                "The symbol name of the listener type specified in the listener "
                "project manifest file (listener_project_manifest.json) does not "
                "inherit from the framework's base listener type for the listener "
                f"project folder: {listener_project_folder}",
            )

        try:
            listener_template_object = listener_template_class()
        except Exception as exc:
            raise InternalListenerProjectError(
                "Failed to load listener template for listener project folder "
                f"{listener_project_folder} due to an exception that occurred while "
                f"instantiating the listener template: {exc}",
            )

        # Return the instantiated listener template to be loaded into the service.
        return ListenerProfile(
            listener=listener_class,
            listener_template=listener_template_object,
            listener_type=listener_type,
            listener_project_folder_path=listener_project_folder,
        )

    def load_framework_listener_profiles(self) -> list[ListenerProfile]:
        self.listener_profiles_service_logger.info(
            "Loading framework listener profiles...",
        )

        listener_profiles = []
        for path in CONSORTIUM_LISTENERS_DIRECTORY_PATH.rglob("*"):
            if path.name != "listener_project_manifest.json":
                continue

            try:
                listener_profile = (
                    self.get_listener_profile_from_listener_project_folder(
                        path.parent,
                    )
                )
                listener_profiles.append(listener_profile)
                self._listener_profiles[str(listener_profile.listener_profile_id)] = (
                    listener_profile
                )
                self.listener_profiles_service_logger.info(
                    f"Loaded listener profile: {listener_profile}",
                )
                self.listener_profiles_service_logger.debug(
                    f"Loaded listener profile: {listener_profile!r}",
                )
            except (
                InvalidListenerProjectFolderStructureError,
                InvalidListenerProjectImplementationError,
                InvalidListenerProjectManifestFileError,
                InternalListenerProjectError,
            ) as exc:
                self.listener_profiles_service_logger.error(
                    f"Failed to load listener profile from listener project folder "
                    f"{path.parent}. {exc}",
                )

        self.listener_profiles_service_logger.info(
            f"Loaded framework listener profiles ({len(self._listener_profiles)} "
            "listener profile(s) loaded).",
        )
        return listener_profiles

    def unload_framework_listener_profiles(self) -> None:
        self.listener_profiles_service_logger.info(
            "Unloading framework listener profiles...",
        )
        number_of_listener_profiles = len(self._listener_profiles)
        self._listener_profiles = {}
        self.listener_profiles_service_logger.info(
            f"Unloaded framework listener profiles ({number_of_listener_profiles} "
            "listener profile(s) unloaded).",
        )

    def reload_framework_listener_profiles(self) -> list[ListenerProfile]:
        self.listener_profiles_service_logger.info(
            "Reloading framework listener profiles...",
        )
        self.unload_framework_listener_profiles()
        listener_profiles = self.load_framework_listener_profiles()
        self.listener_profiles_service_logger.info(
            f"Reloaded framework listener profiles.",
        )
        return listener_profiles

    def load_listener_profile_from_listener_project_folder(
        self,
        listener_project_folder: Path,
    ) -> ListenerProfile:
        listener_profile = self.get_listener_profile_from_listener_project_folder(
            listener_project_folder,
        )
        self._listener_profiles[str(listener_profile.listener_profile_id)] = (
            listener_profile
        )
        self.listener_profiles_service_logger.debug(
            f"Loaded listener profile: {listener_profile!r}",
        )
        return listener_profile

    def unload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id,
    ) -> None:
        try:
            listener_profile = self._listener_profiles.pop(listener_profile_id)
        except KeyError:
            raise ValueError(
                f"No listener profile exists with the provided listener profile ID: "
                f"{listener_profile_id}",
            )

        self.listener_profiles_service_logger.debug(
            f"Unloaded listener profile: {listener_profile!r}",
        )
        return listener_profile

    def reload_listener_profile_by_listener_profile_id(
        self,
        listener_profile_id,
    ) -> ListenerProfile:
        try:
            listener_profile = self._listener_profiles.pop(listener_profile_id)
        except KeyError:
            raise ValueError(
                f"No listener profile exists with the provided listener profile ID: "
                f"{listener_profile_id}",
            )

        listener_profile = self.load_listener_profile_from_listener_project_folder(
            listener_profile.listener_project_folder_path,
        )
        self.listener_profiles_service_logger.debug(
            f"Reloaded listener profile: {listener_profile!r}",
        )
        return listener_profile

    def get_all_listener_profiles(self):
        all_listener_profiles = list(self._listener_profiles.values())
        self.listener_profiles_service_logger.debug(
            f"Retrieved all listener profiles ({len(all_listener_profiles)} retrieved).",
        )
        return all_listener_profiles

    def get_listener_profile_by_listener_profile_id(self, listener_profile_id):
        try:
            listener_profile = self._listener_profiles[listener_profile_id]
        except KeyError:
            raise ValueError(
                f"No listener profile exists with the provided listener profile ID: "
                f"{listener_profile_id}",
            )

        self.listener_profiles_service_logger.debug(
            f"Retrieved listener profile: {listener_profile!r}",
        )
        return listener_profile

    def __str__(self) -> str:
        return "Consortium Listener Profiles Service"

    def __repr__(self) -> str:
        return "ListenerProfilesService()"
