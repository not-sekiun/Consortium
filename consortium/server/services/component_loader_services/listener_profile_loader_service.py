import pathlib

from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.server.exceptions.framework_exceptions.listener_template_framework_exceptions import (
    ListenerTemplatesFrameworkError,
)
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
    ComponentLoadingError,
    ComponentType,
)


class ListenerProfileLoaderService(ComponentLoaderService[BaseListenerTemplate]):
    _component_type = BaseListenerTemplate
    _component_framework_error = ListenerTemplatesFrameworkError
    _manifest_json_schema = {
        "type": "object",
        "properties": {
            "entry_point": {"type": "string"},
            "enabled": {"type": "boolean"},
        },
        "required": ["entry_point", "enabled"],
        "additionalProperties": False,
    }

    @staticmethod
    def _post_validate_component_object(
        component_object: BaseListenerTemplate,
    ) -> ListenerProfile:
        # listener refers to the class of the listener that the template creates
        component_object.listener.creating_listener_template = component_object
        component_object.listener.listener_type = component_object.listener_type
        return ListenerProfile(
            listener=component_object.listener,
            listener_template=component_object,
            listener_type=component_object.listener_type,
        )

    # Change the return type to ListenerProfile for both methods
    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> ListenerProfile | None:
        return super().get_component_from_component_project_folder(
            component_project_folder=component_project_folder,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    def get_components_from_component_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[ComponentType],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]],
    ]:
        return super().get_components_from_component_project_folder_directories(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )
