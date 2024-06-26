import importlib
import json
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.server.exceptions.service_exceptions.listener_profiles_service_exceptions import (
    InternalListenerProjectError,
    InvalidListenerProjectFolderStructureError,
    InvalidListenerProjectImplementationError,
    InvalidListenerProjectManifestFileError,
    InvalidListenerProjectManifestFileJSONError,
    InvalidListenerProjectManifestFileSchemaError,
    ListenerProfileNotFoundError,
    ListenerProjectInterfaceError,
    ListenerProjectListenerFileNotFoundError,
    ListenerProjectListenerTemplateFileNotFoundError,
    ListenerProjectListenerTypeFileNotFoundError,
    ListenerProjectManifestFileNotFoundError,
    ListenerProjectSymbolNotFoundError,
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

    def __str__(self) -> str:
        return "Consortium Listener Profiles Service"

    def __repr__(self) -> str:
        return "ListenerProfilesService()"

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
            raise ListenerProjectManifestFileNotFoundError(
                listener_project_folder=str(listener_project_folder),
            )
        except json.JSONDecodeError:
            raise InvalidListenerProjectManifestFileJSONError(
                listener_project_folder=str(listener_project_folder),
            )
        except jsonschema.ValidationError as exc:
            raise InvalidListenerProjectManifestFileSchemaError(
                listener_project_folder=str(listener_project_folder),
                json_schema_error_message=exc.message,
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
            raise ListenerProjectListenerFileNotFoundError(
                listener_file=str(listener_file),
                listener_project_folder=str(listener_project_folder),
            )
        if not listener_template_file.exists():
            raise ListenerProjectListenerTemplateFileNotFoundError(
                listener_template_file=str(listener_template_file),
                listener_project_folder=str(listener_project_folder),
            )
        if not listener_type_file.exists():
            raise ListenerProjectListenerTypeFileNotFoundError(
                listener_type_file=str(listener_type_file),
                listener_project_folder=str(listener_project_folder),
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
            raise ListenerProjectSymbolNotFoundError(
                symbol_name=listener_symbol,
                listener_project_file=str(listener_file),
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener",
                internal_error_message=str(exc),
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
            raise ListenerProjectSymbolNotFoundError(
                symbol_name=listener_template_symbol,
                listener_project_file=str(listener_template_file),
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener template",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener template",
                internal_error_message=str(exc),
            )

        try:
            listener_type_module = importlib.import_module(listener_type_module_path)
            listener_type = getattr(
                listener_type_module,
                listener_type_symbol,
            )
        except (ImportError, AttributeError):
            raise ListenerProjectSymbolNotFoundError(
                symbol_name=listener_type_symbol,
                listener_project_file=str(listener_type_file),
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener type",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener type",
                internal_error_message=str(exc),
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(listener_class, BaseListener):
            raise ListenerProjectInterfaceError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener",
                listener_project_symbol=listener_symbol,
            )
        if not issubclass(listener_template_class, BaseListenerTemplate):
            raise ListenerProjectInterfaceError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener template",
                listener_project_symbol=listener_template_symbol,
            )
        if not isinstance(listener_type, ListenerType):
            raise ListenerProjectInterfaceError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener type",
                listener_project_symbol=listener_type_symbol,
            )

        try:
            listener_template_object = listener_template_class()
        except Exception as exc:
            raise InternalListenerProjectError(
                listener_project_folder=str(listener_project_folder),
                listener_project_file_type="listener template",
                internal_error_message=str(exc),
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
                self.listener_profiles_service_logger.error(exc)

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
            raise ListenerProfileNotFoundError(
                listener_profile_id=listener_profile_id,
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
            raise ListenerProfileNotFoundError(
                listener_profile_id=listener_profile_id,
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

        self.listener_profiles_service_logger.debug(
            f"Retrieved listener profile: {listener_profile!r}",
        )
        return listener_profile
