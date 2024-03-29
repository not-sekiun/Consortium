import importlib
import pathlib
from typing import Type

from loguru import logger

from consortium.server.framework.base_listener import BaseListener
from consortium.server.framework.base_listener_template import BaseListenerTemplate
from consortium.server.framework.framework_types import ListenerType
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    CONSORTIUM_LISTENERS_DIRECTORY_PATH,
)


class ListenerTemplatesService:
    def __init__(self):
        self._listener_templates = {}
        self._listener_templates_service_logger = logger.bind(
            logger_name="Consortium Listener Templates Service",
        )

        # attempt to recursively load each folder as a listener project folder
        visited_dir_paths = []
        for listener_project_folder_path in CONSORTIUM_LISTENERS_DIRECTORY_PATH.rglob(
            "*",
        ):
            if listener_project_folder_path.parent in visited_dir_paths:
                continue
            visited_dir_paths.append(listener_project_folder_path.parent)
            try:
                self._load_listener_project_folder(listener_project_folder_path.parent)
            # triggers for invalid project folder structure
            except ValueError:
                pass

    def _load_listener_project_folder(
        self,
        listener_project_folder_path: pathlib.Path,
    ) -> None:
        # A listener project folder is a folder that represents a valid listener that
        # can be loaded into the server. It is defined as a folder that contains a
        # listener.py file, a listener_template.py file, and a listener_type.py file.
        # The listener.py file must contain a class called Listener that inherits from
        # BaseListener. The listener_template.py file must contain a class called
        # ListenerTemplate that inherits from BaseListenerTemplate. The listener_type.py
        # file must contain the constant LISTENER_TYPE which is an instance of
        # ListenerType. The folder must be located at
        # consortium/server/framework/listeners with any arbitrary nested folder
        # structure. On top of that, the folder must be a valid python package reachable
        # from the root of the server. This means that the folder must contain
        # __init__.py files in all parent directories.
        files_in_directory = [
            file.name
            for file in listener_project_folder_path.iterdir()
            if file.is_file()
        ]

        # check for valid project folder structure
        if (
            "listener.py" not in files_in_directory
            or "listener_template.py" not in files_in_directory
            or "listener_type.py" not in files_in_directory
            or "__init__.py" not in files_in_directory
        ):
            raise ValueError(
                f"The folder {listener_project_folder_path} is not a valid listener project folder. It must contain the following files: listener.py, listener_template.py, listener_type.py, __init__.py",
            )

        relative_path = listener_project_folder_path.relative_to(
            CONSORTIUM_HOME_DIRECTORY_PATH,
        )
        module_name = ".".join(relative_path.parts)

        # Check to see if any errors arise during import.
        try:
            listener_template_module = importlib.import_module(
                f"{module_name}.listener_template",
            )
            listener_module = importlib.import_module(
                f"{module_name}.listener",
            )
            listener_type_module = importlib.import_module(
                f"{module_name}.listener_type",
            )
        except Exception as exc:
            self._listener_templates_service_logger.error(
                f"Failed to load listener from {listener_project_folder_path} due to exception: {exc}",
            )
            return

        # check for valid naming of classes
        try:
            listener_template = listener_template_module.ListenerTemplate
            listener = listener_module.Listener
            listener_type = listener_type_module.LISTENER_TYPE
        except AttributeError:
            self._listener_templates_service_logger.error(
                f"Failed to load listener from {listener_project_folder_path} due to missing classes",
            )
            return

        # check that classes inherit from the correct base classes
        if not issubclass(listener_template, BaseListenerTemplate):
            raise ValueError(
                f"Invalid listener project folder: {listener_project_folder_path}. The ListenerTemplate class does not inherit from BaseListenerTemplate",
            )
        if not issubclass(listener, BaseListener):
            raise ValueError(
                f"Invalid listener project folder: {listener_project_folder_path}. The Listener class does not inherit from BaseListener",
            )
        if not isinstance(listener_type, ListenerType):
            raise ValueError(
                f"Invalid listener project folder: {listener_project_folder_path}. The LISTENER_TYPE object is not of the ListenerType class",
            )

        instantiated_listener_template = listener_template()
        self._listener_templates[
            str(instantiated_listener_template.listener_template_id)
        ] = instantiated_listener_template

        # Although we are explicitly loading the listener template here, the loading of
        # a listener template represents the framework loading an entire listener.
        self._listener_templates_service_logger.debug(
            f'Loaded listener: "{instantiated_listener_template.name}" ({instantiated_listener_template.listener_template_id})',
        )

    def get_listener_template_by_listener_template_id(
        self,
        listener_template_id: str,
    ) -> Type[BaseListenerTemplate]:
        try:
            listener_template = self._listener_templates[listener_template_id]
        except KeyError:
            raise ValueError(
                f'Listener template with the listener template ID "{listener_template_id}" does not exist',
            )

        self._listener_templates_service_logger.debug(
            f'Retrieved listener template "{listener_template.name}" ({listener_template_id})',
        )
        return listener_template

    def get_all_listener_templates(self) -> list[Type[BaseListenerTemplate]]:
        all_listener_templates = list(self._listener_templates.values())
        self._listener_templates_service_logger.debug(
            f"Retrieved all listener templates ({len(all_listener_templates)} retrieved)",
        )
        return all_listener_templates
