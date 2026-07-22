import pathlib
import uuid
from abc import ABC, abstractmethod

from consortium.server.exceptions.service_exceptions.components_service_exceptions import (
    ComponentAlreadyRegisteredError,
    ComponentNotFoundError,
    DuplicateComponentLabelError,
)
from consortium.server.services.component_loader_services.component_loader_service import (
    ComponentLoaderService,
)
from consortium.server.utils import normalize_uuid


class ComponentRegistryService[Component, ComponentLoadingError](ABC):
    _component_loader_service: ComponentLoaderService[Component]

    def __init__(
        self,
        component_loader_service: ComponentLoaderService[Component],
        component_framework_directory: pathlib.Path,
    ) -> None:
        self._component_loader_service = component_loader_service
        self._component_framework_directory = component_framework_directory
        self._components = {}

    # Each component has a different attribute name for the component ID. Provide an
    # override to get the component ID regardless of what its named.
    # TODO: ??? Consider maybe standardizing the component ID attribute name across
    #  all components. If so, remove this method.
    @abstractmethod
    def _get_component_id(self, component: Component) -> uuid.UUID: ...

    # TODO: ??? Consider maybe standardizing this attribute name across
    #  all components. If so, remove this method.
    # TODO: Update (Yes we are working on this, moving all attributes to
    #  self.root_directory after that change DELETE THIS DONT FORGET
    @abstractmethod
    def _get_component_directory(self, component: Component) -> pathlib.Path: ...

    # Runs after a component is registered.
    async def _component_load_procedure(
        self,
        component: Component,
        context: dict,
    ) -> Component:
        return component

    # Runs before a component is deregistered.
    async def _component_unload_procedure(
        self,
        component: Component,
        context: dict,
    ) -> Component:
        return component

    def get_component_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component:
        return self._component_loader_service.get_component_from_directory(
            component_directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    def get_all_components_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[Component],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]] | None,
    ]:
        return self._component_loader_service.get_all_components_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    def register_component(self, component: Component) -> None:
        component_id = self._get_component_id(component=component)
        if str(component_id) in self._components:
            raise ComponentAlreadyRegisteredError(
                component_str=str(component),
                component_id=str(component_id),
            )
        if component.label and component.label in [
            component.label
            for component in self._components.values()
            if component.label
        ]:
            raise DuplicateComponentLabelError(
                component_str=str(component),
                label=component.label,
            )
        self._component_loader_service.validate_component_component_dependencies(
            component=component,
            registered_components=self.get_all_components(),
        )
        self._components[str(component_id)] = component

    def register_component_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component | None:
        component = self.get_component_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )
        # If `component` is `None`, it implies a disabled component was attempted to be
        # registered.
        if component is None:
            return None

        self.register_component(component=component)
        return component

    async def load_component(
        self,
        component: Component,
        context: dict | None = None,
    ) -> Component:
        if context is None:
            context = {}
        if str(self._get_component_id(component=component)) in self._components:
            raise ComponentAlreadyRegisteredError(
                component_str=str(component),
                component_id=str(self._get_component_id(component=component)),
            )
        component = await self._component_load_procedure(
            component=component,
            context=context,
        )
        self._components[str(self._get_component_id(component=component))] = component
        return component

    async def load_component_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
        context: dict | None = None,
    ) -> Component | None:
        if context is None:
            context = {}
        component = self.get_component_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )
        if component is None:
            return None
        return await self.load_component(component=component, context=context)

    async def unload_component_by_component_id(
        self,
        component_id: str | uuid.UUID,
        context: dict | None = None,
    ) -> None:
        if context is None:
            context = {}
        component = self.get_component_by_component_id(component_id=component_id)
        await self._component_unload_procedure(component=component, context=context)
        del self._components[str(self._get_component_id(component=component))]

    async def reload_component_by_component_id(
        self,
        component_id: str | uuid.UUID,
        ignore_enabled_component_flag: bool = False,
        load_context: dict | None = None,
        unload_context: dict | None = None,
    ) -> Component | None:
        if load_context is None:
            load_context = {}
        if unload_context is None:
            unload_context = {}
        component = self.get_component_by_component_id(component_id=component_id)
        component_directory = self._get_component_directory(
            component=component,
        )
        await self.unload_component_by_component_id(
            component_id=component_id,
            context=unload_context,
        )
        return await self.load_component_from_directory(
            directory=component_directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
            context=load_context,
        )

    def get_component_by_component_id(self, component_id: str | uuid.UUID) -> Component:
        component_id = normalize_uuid(component_id)

        try:
            return self._components[component_id]
        except KeyError:
            raise ComponentNotFoundError(component_id=component_id) from None

    def get_components_by_label(self, label: str) -> list[Component]:
        return [
            component
            for component in self._components.values()
            if getattr(component, "label", None) == label
        ]

    def get_all_components(self) -> list[Component]:
        return list(self._components.values())
