import importlib
import json
from pathlib import Path
from typing import Type

import jsonschema
from loguru import logger

from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.base_listener_template import BaseListenerTemplate
from consortium.server.framework.framework_types import ListenerType
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    CONSORTIUM_LISTENERS_DIRECTORY_PATH,
)
from consortium.server.server_exceptions import (
    InternalListenerProjectError,
    InvalidListenerProjectFolderStructureError,
    InvalidListenerProjectImplementationError,
    InvalidListenerProjectManifestFileError,
)


class ListenerTemplatesService:
    def __init__(self):
        self._listener_templates = {}
        self._listener_templates_service_logger = logger.bind(
            logger_name="Consortium Listener Templates Service",
        )

        # Recursively search through the listeners directory to load all listener
        # projects.
        for listener_project_folder_path in CONSORTIUM_LISTENERS_DIRECTORY_PATH.rglob(
            "*",
        ):
            if listener_project_folder_path.name != "listener_project_manifest.json":
                continue

            try:
                # Instantiate and load the listener template into the listener templates
                # service. This represents the loading of a listener.
                listener_template = self._load_listener_from_listener_project_folder(
                    listener_project_folder_path.parent,
                )
                self._listener_templates[
                    str(listener_template.listener_template_id)
                ] = listener_template

                # Although we are explicitly loading the listener template here, the
                # loading of a listener template represents the framework loading an
                # entire listener.
                self._listener_templates_service_logger.debug(
                    f"Loaded listener: {listener_template!r}",
                )
                self._listener_templates_service_logger.info(
                    f"Loaded listener: {listener_template}",
                )
            except (
                InvalidListenerProjectFolderStructureError,
                InvalidListenerProjectManifestFileError,
                InvalidListenerProjectImplementationError,
                InternalListenerProjectError,
            ) as exc:
                self._listener_templates_service_logger.error(
                    f"Failed to load listener. {exc}",
                )

    # Loading a listener is represented by the loading of a listener template into the
    # listener templates service hence the naming of this method.
    @staticmethod
    def _load_listener_from_listener_project_folder(
        listener_project_folder: Path,
    ) -> BaseListenerTemplate:
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
        try:
            with listener_project_manifest_file.open("r") as file:
                listener_project_manifest_json = json.load(fp=file)
                jsonschema.validate(
                    instance=listener_project_manifest_json,
                    schema=listener_project_manifest_json_schema,
                )
        except FileNotFoundError:
            raise InvalidListenerProjectFolderStructureError(
                f"No listener project manifest file found in listener project folder: {listener_project_folder}",
            )
        except jsonschema.ValidationError:
            raise InvalidListenerProjectManifestFileError(
                f"Invalid listener_project_manifest.json file in listener project folder: {listener_project_folder}",
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
                f"The listener.py file is missing for listener project folder: {listener_project_folder}",
            )
        if not listener_template_file.exists():
            raise InvalidListenerProjectFolderStructureError(
                f"The listener_template.py file is missing for listener project folder: {listener_project_folder}",
            )
        if not listener_type_file.exists():
            raise InvalidListenerProjectFolderStructureError(
                f"The listener_type.py file is missing for listener project folder: {listener_project_folder}",
            )

        # Check for valid symbol names in the required listener project files.
        listener_module_path = ".".join(
            listener_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        listener_template_module_path = ".".join(
            listener_template_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]
        listener_type_module_path = ".".join(
            listener_type_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]

        try:
            listener_module = importlib.import_module(listener_module_path)
            listener_class = getattr(
                listener_module,
                listener_project_manifest_json["listener"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidListenerProjectFolderStructureError(
                f"Symbol name specified in listener_project_manifest.json was not found in the listener file for listener project folder: {listener_project_folder}",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                f"Failed to load listener from {listener_project_folder} due to an exception during import: {exc}",
            )

        try:
            listener_template_module = importlib.import_module(
                listener_template_module_path,
            )
            listener_template_class = getattr(
                listener_template_module,
                listener_project_manifest_json["listener_template"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidListenerProjectFolderStructureError(
                f"Symbol name specified in listener_project_manifest.json was not found in the listener template file for listener project folder: {listener_project_folder}",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                f"Failed to load listener template from {listener_project_folder} due to an exception during import: {exc}",
            )

        try:
            listener_type_module = importlib.import_module(listener_type_module_path)
            listener_type = getattr(
                listener_type_module,
                listener_project_manifest_json["listener_type"]["symbol"],
            )
        except (ImportError, AttributeError):
            raise InvalidListenerProjectFolderStructureError(
                f"Symbol name specified in listener_project_manifest.json was not found in the listener type file for listener project folder: {listener_project_folder}",
            )
        except Exception as exc:
            raise InternalListenerProjectError(
                f"Failed to load listener type from {listener_project_folder} due to an exception during import: {exc}",
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(listener_class, BaseListener):
            raise InvalidListenerProjectImplementationError(
                f"The listener class must inherit from the framework's base listener class for listener project folder: {listener_project_folder}",
            )
        if not issubclass(listener_template_class, BaseListenerTemplate):
            raise InvalidListenerProjectImplementationError(
                f"The listener template class must inherit from the framework's base listener template class for listener project folder: {listener_project_folder}",
            )
        if not isinstance(listener_type, ListenerType):
            raise InvalidListenerProjectImplementationError(
                f"The listener type must be an instance of the framework's listener type class for listener project folder: {listener_project_folder}",
            )

        # Return the instantiated listener template to be loaded into the service.
        return listener_template_class()

    def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> Type[BaseListenerTemplate]:
        try:
            listener_template = self._listener_templates[listener_template_id]
        except KeyError:
            raise ValueError(
                f"No listener template exists with the listener template ID: {listener_template_id}",
            )

        self._listener_templates_service_logger.debug(
            f"Retrieved listener template: {listener_template!r}",
        )
        return listener_template

    def get_all_listener_templates(self) -> list[Type[BaseListenerTemplate]]:
        all_listener_templates = list(self._listener_templates.values())
        self._listener_templates_service_logger.debug(
            f"Retrieved all listener templates ({len(all_listener_templates)} retrieved).",
        )
        return all_listener_templates
