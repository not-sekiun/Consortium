import pathlib
import uuid

import consortium.server.exceptions.service_exceptions.components_service_exceptions as comp_ldr_svc_excs
from consortium.framework.utils.exception_utils import remap_exception
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
    _EXCEPTION_MAP: dict[type[Exception], type[Exception]]
    _EXCEPTION_KWARGS_MAP: dict[str, str]

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
                # TODO: Move to ComponentServiceError
                comp_ldr_svc_excs.ComponentLoadingError,
                comp_ldr_svc_excs.ComponentDependencyError,
            ) as exc:
                raise remap_exception(
                    original_exception=exc,
                    original_kwargs=exc._kwargs,
                    exception_map=self._EXCEPTION_MAP,
                    exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
                ) from None

        return wrapper

    @_remap_exception_decorator
    def get_component_from_component_project_folder(
        self,
        component_project_folder: pathlib.Path,
        ignore_enabled_component_flag: bool = False,
    ) -> Component:
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
        list[tuple[pathlib.Path, ComponentLoadingError]] | None,
    ]:
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
                    comp_ldr_svc_excs.ComponentLoadingError,
                    comp_ldr_svc_excs.ComponentDependencyError,
                ),
            ):
                remapped_errored.append(
                    (
                        error_tuple[0],
                        remap_exception(
                            original_exception=error,
                            original_kwargs=error._kwargs,
                            exception_map=self._EXCEPTION_MAP,
                            exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
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
        return super().register_component(component=component)

    @_remap_exception_decorator
    def get_component_by_component_id(self, component_id: str | uuid.UUID) -> Component:
        return super().get_component_by_component_id(component_id=component_id)
