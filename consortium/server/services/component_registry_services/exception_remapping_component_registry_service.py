import pathlib
import uuid

from consortium.framework._utils import remap_exception
from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as comp_excs,
)
from consortium.server.services.component_registry_services.component_registry_service import (
    ComponentRegistryService,
)
from consortium.server.services.component_registry_services.component_registry_service_types import (
    Component,
    ComponentLoadingError,
)


class ExceptionRemappingComponentRegistryService(
    ComponentRegistryService[Component, ComponentLoadingError],
):
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP: dict[type[Exception], type[Exception]]
    _COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP: dict[str, str]

    @staticmethod
    def _remap_exception_decorator(func):
        def wrapper(
            self,
            *args,
            **kwargs,
        ):
            try:
                return func(self, *args, **kwargs)
            except (
                comp_excs.ComponentLoadingError,
                comp_excs.ComponentDependencyError,
            ) as exc:
                raise remap_exception(
                    original_exception=exc,
                    original_kwargs=exc._kwargs,
                    exception_map=self._COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP,
                    exception_kwargs_map=self._COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP,
                ) from None

        return wrapper

    @_remap_exception_decorator
    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component:
        """Loads a component from a project folder with domain-specific exception remapping.

        Delegates to the base class and intercepts any `ComponentLoadingError` or
        `ComponentDependencyError`, remapping them to the subclass-defined
        domain-specific error types via `_COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP`.

        Args:
            component_project_folder (pathlib.Path): Path to the directory containing
                the component project files and `manifest.json`.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in the manifest. Defaults to `False`.

        Returns:
            Component: The instantiated component, or `None` if the component is
                disabled.
        """
        return super().get_component_from_component_project_folder(
            component_project_folder=component_project_folder,
            ignore_enabled_component_flag=ignore_enabled_component_flag,
        )

    def get_components_from_component_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> tuple[
        list[Component],
        list[pathlib.Path],
        list[tuple[pathlib.Path, ComponentLoadingError]],
    ]:
        """Scans a directory and loads all components, remapping errors to domain-specific types.

        Delegates to the base class then replaces each `ComponentLoadingError` or
        `ComponentDependencyError` in the errored list with the corresponding
        domain-specific exception type. Non-remappable errors are forwarded unchanged.

        Args:
            directory (pathlib.Path): The root directory to recursively scan for
                component project folders.
            ignore_enabled_component_flag (bool): When `True`, bypasses the `enabled`
                check in each manifest. Defaults to `False`.

        Returns:
            tuple[list[Component], list[pathlib.Path], list[tuple[pathlib.Path, ComponentLoadingError]]]:
                A three-element tuple of loaded components, skipped paths, and
                `(path, domain-error)` pairs for components that errored.
        """
        retrieved, skipped, errored = (
            super().get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_component_flag,
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
                    comp_excs.ComponentLoadingError,
                    comp_excs.ComponentDependencyError,
                ),
            ):
                remapped_errored.append(
                    (
                        error_tuple[0],
                        remap_exception(
                            original_exception=error,
                            original_kwargs=error._kwargs,
                            exception_map=self._COMPONENT_REGISTRY_SERVICE_EXCEPTION_MAP,
                            exception_kwargs_map=self._COMPONENT_REGISTRY_SERVICE_EXCEPTION_KWARGS_MAP,
                        ),
                    ),
                )
            else:
                remapped_errored.append(error_tuple)
        return (
            retrieved,
            skipped,
            remapped_errored,
        )

    @_remap_exception_decorator
    def register_component(self, component: Component) -> None:
        """Registers a component with domain-specific exception remapping.

        Delegates to the base class and intercepts any `ComponentLoadingError` or
        `ComponentDependencyError`, remapping them to domain-specific types.

        Args:
            component (Component): The component instance to register.

        Returns:
            None
        """
        return super().register_component(component=component)

    @_remap_exception_decorator
    def get_component_by_component_id(self, component_id: str | uuid.UUID) -> Component:
        """Returns a registered component by its ID with domain-specific exception remapping.

        Delegates to the base class and intercepts any `ComponentLoadingError` or
        `ComponentDependencyError`, remapping them to domain-specific types.

        Args:
            component_id (str | uuid.UUID): The ID of the component to retrieve.

        Returns:
            Component: The requested component instance.
        """
        return super().get_component_by_component_id(component_id=component_id)
