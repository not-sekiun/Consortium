import pathlib
import uuid
from abc import ABC, abstractmethod

from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
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
    @abstractmethod
    def _get_component_project_folder(self, component: Component) -> pathlib.Path: ...

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

    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component:
        """Delegates to the component loader to instantiate a component from a project folder.

        Does not register the component. See `register_component_from_component_project_folder`
        or `load_component_from_component_project_folder` to instantiate and register in
        one step.

        Args:
            component_project_folder (pathlib.Path): Path to the directory containing
                the component project files and `manifest.json`.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.

        Returns:
            Component: The instantiated component, or `None` if the component is
                disabled and the enabled check is not overridden.

        Raises:
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol named in the manifest
                does not exist in the module.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the component is incompatible
                with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs during
                import or instantiation.
        """
        return (
            self._component_loader_service.get_component_from_component_project_folder(
                component_project_folder=component_project_folder,
                ignore_enabled_component_flag=ignore_enabled_component_flag,
            )
        )

    def get_components_from_component_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[Component],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]] | None,
    ]:
        """Delegates to the component loader to scan a directory and load all components found.

        Does not register the loaded components. See the individual `load_component*`
        methods to instantiate and register in one step.

        Args:
            directory (pathlib.Path): The root directory to recursively scan for
                component project folders.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in each manifest. Defaults to `False`.

        Returns:
            tuple[list[Component], list[pathlib.Path], list[tuple[pathlib.Path, ComponentLoadingError]] | None]:
                A three-element tuple of:
                    - A list of successfully loaded component instances.
                    - A list of paths for disabled (skipped) components.
                    - A list of `(path, error)` pairs for components that errored, or
                      `None`.
        """
        return self._component_loader_service.get_components_from_component_project_folder_directories(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    def register_component(self, component: Component) -> None:
        """Registers an already-instantiated component in the registry.

        Validates that the component's ID and label are unique and that all declared
        component dependencies are satisfied before registering.

        Args:
            component (Component): The component instance to register.

        Returns:
            None

        Raises:
            ComponentAlreadyRegisteredError: If a component with the same ID is already
                registered.
            DuplicateComponentLabelError: If another registered component has the same
                non-empty label.
            ComponentDependencyNotFoundError: If a declared dependency is not present in
                the registry.
            IncompatibleComponentDependencyVersionError: If a dependency's version does
                not satisfy the required specifier.
        """
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
                component=str(component),
                label=component.label,
            )
        self._component_loader_service.validate_component_component_dependencies(
            component=component,
            registered_components=self.get_all_components(),
        )
        self._components[str(component_id)] = component

    def register_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component | None:
        """Loads a component from a project folder and registers it in one step.

        Args:
            component_project_folder (pathlib.Path): Path to the directory containing
                the component project files and `manifest.json`.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.

        Returns:
            Component | None: The registered component instance, or `None` if the
                component is disabled.

        Raises:
            ComponentAlreadyRegisteredError: If a component with the same ID is already
                registered.
            DuplicateComponentLabelError: If another registered component has the same
                non-empty label.
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol named in the manifest
                does not exist in the module.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the component is incompatible
                with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs during
                import or instantiation.
        """
        component = self.get_component_from_component_project_folder(
            component_project_folder=component_project_folder,
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
        """Runs the component load procedure and registers the component.

        The load procedure (e.g. starting a listener or registering event handlers) is
        executed before the component is added to the registry.

        Args:
            component (Component): The component instance to load.
            context (dict | None): An optional context dictionary passed to
                `_component_load_procedure`. Defaults to an empty dict.

        Returns:
            Component: The loaded and registered component instance.

        Raises:
            ComponentAlreadyRegisteredError: If a component with the same ID is already
                registered.
        """
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

    async def load_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
        context: dict | None = None,
    ) -> Component | None:
        """Instantiates, runs the load procedure, and registers a component from a project folder.

        Args:
            component_project_folder (pathlib.Path): Path to the directory containing
                the component project files and `manifest.json`.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.
            context (dict | None): An optional context dictionary passed to
                `_component_load_procedure`. Defaults to an empty dict.

        Returns:
            Component | None: The loaded and registered component instance, or `None`
                if the component is disabled.

        Raises:
            ComponentAlreadyRegisteredError: If a component with the same ID is already
                registered.
            ComponentProjectManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidComponentProjectManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidComponentProjectManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            ComponentProjectEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            ComponentProjectSymbolNotFoundError: If the symbol named in the manifest
                does not exist in the module.
            ComponentProjectInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatibleComponentFrameworkVersionError: If the component is incompatible
                with the current framework version.
            InternalComponentProjectError: If an unhandled exception occurs during
                import or instantiation.
        """
        if context is None:
            context = {}
        component = self.get_component_from_component_project_folder(
            component_project_folder=component_project_folder,
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
        """Runs the component unload procedure and removes the component from the registry.

        Args:
            component_id (str | uuid.UUID): The ID of the component to unload.
            context (dict | None): An optional context dictionary passed to
                `_component_unload_procedure`. Defaults to an empty dict.

        Returns:
            None

        Raises:
            ComponentNotFoundError: If no component with the given ID is registered.
        """
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
        """Unloads a component then reloads it from its original project folder.

        If the component is disabled after reload and `ignore_enabled_component_flag`
        is `False`, the component will only be unloaded, not reloaded.

        Args:
            component_id (str | uuid.UUID): The ID of the component to reload.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in the manifest during reload. Defaults to `False`.
            load_context (dict | None): An optional context dictionary passed to
                `_component_load_procedure` during the load step. Defaults to an empty
                dict.
            unload_context (dict | None): An optional context dictionary passed to
                `_component_unload_procedure` during the unload step. Defaults to an
                empty dict.

        Returns:
            Component | None: The reloaded component instance, or `None` if the
                component was disabled and the enabled check was not overridden.

        Raises:
            ComponentNotFoundError: If no component with the given ID is registered.
        """
        if load_context is None:
            load_context = {}
        if unload_context is None:
            unload_context = {}
        component = self.get_component_by_component_id(component_id=component_id)
        component_project_folder = self._get_component_project_folder(
            component=component,
        )
        await self.unload_component_by_component_id(
            component_id=component_id,
            context=unload_context,
        )
        return await self.load_component_from_component_project_folder(
            component_project_folder=component_project_folder,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
            context=load_context,
        )

    def get_component_by_component_id(self, component_id: str | uuid.UUID) -> Component:
        """Returns a registered component by its ID.

        Args:
            component_id (str | uuid.UUID): The ID of the component to retrieve.

        Returns:
            Component: The requested component instance.

        Raises:
            ComponentNotFoundError: If no component with the given ID is registered.
        """
        component_id = normalize_uuid(component_id)

        try:
            return self._components[component_id]
        except KeyError:
            raise ComponentNotFoundError(component_id=component_id) from None

    def get_components_by_label(self, label: str) -> list[Component]:
        """Returns all registered components with a given label.

        Args:
            label (str): The label to filter by.

        Returns:
            list[Component]: All registered components whose `label` attribute matches.
                Empty if none match.
        """
        return [
            component
            for component in self._components.values()
            if getattr(component, "label", None) == label
        ]

    def get_all_components(self) -> list[Component]:
        """Returns all currently registered components.

        Returns:
            list[Component]: A list of all registered component instances. Empty if
                none are registered.
        """
        return list(self._components.values())
