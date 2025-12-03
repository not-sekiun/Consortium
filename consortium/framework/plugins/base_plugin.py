import pathlib
import sys
import traceback
import types
import uuid
from typing import Any

import loguru

import consortium.server.exceptions.framework_exceptions.components_framework_exceptions as comp_excs
import consortium.server.server_singletons as server_singletons
from consortium.framework._components import (
    ComponentLifeCycle,
    ComponentLifeCycleFatalContext,
    ComponentMetadata,
    ComponentModel,
)
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.components_framework_exceptions import (
    ComponentAlreadyStartedError,
    ComponentNotRunningError,
    ComponentStartError as LifeCycleStartFrameworkError,
    ComponentStopError as LifeCycleStopFrameworkError,
)
from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
    EmptyPluginLabelError,
    InvalidFrameworkVersionSpecifierError,
    InvalidPluginConfigurationParameterTypeError,
    InvalidPluginDependencyVersionSpecifierError,
    InvalidPluginVersionError,
    MissingPluginConfigurationParameterError,
    PluginAlreadyStartedError,
    PluginNotRunningError,
    PluginStartError as PluginStartFrameworkError,
    PluginStopError as PluginStopFrameworkError,
)
from consortium.server.server_logging import LoggerType
from consortium.server.utils.data_structure_utils import remap_exception


class _PluginModel(ComponentModel):
    autostart: bool = True


class BasePlugin(ComponentMetadata, ComponentLifeCycle):
    _METADATA_MODEL = _PluginModel
    _EXCEPTION_MAP = {
        comp_excs.MissingComponentConfigurationParameterError: MissingPluginConfigurationParameterError,
        comp_excs.EmptyComponentLabelError: EmptyPluginLabelError,
        comp_excs.InvalidComponentVersionError: InvalidPluginVersionError,
        comp_excs.InvalidFrameworkVersionSpecifierError: InvalidFrameworkVersionSpecifierError,
        comp_excs.InvalidComponentDependencyVersionSpecifierError: InvalidPluginDependencyVersionSpecifierError,
        comp_excs.InvalidComponentConfigurationParameterTypeError: InvalidPluginConfigurationParameterTypeError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_str": "plugin_str",
        "component_filepath": "plugin_filepath",
    }

    autostart: bool = True

    def __init__(self):
        self.plugin_id = uuid.uuid4()
        self.environment = types.SimpleNamespace()
        self.server_services = types.SimpleNamespace(
            **{
                attr: getattr(server_singletons, attr)
                for attr in dir(server_singletons)
                if attr.endswith("_service")
            },
        )
        self.plugin_logger = loguru.logger.bind(
            logger_name=f"Plugin - {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        self.plugin_project_folder = pathlib.Path(
            sys.modules[self.__module__].__file__,
        ).parents[0]
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        try:
            cls._validate_metadata()
        except comp_excs.ComponentsFrameworkError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.exc_kwargs,
                exception_map=cls._EXCEPTION_MAP,
                exception_kwargs_map=cls._EXCEPTION_KWARGS_MAP,
            ) from None
        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({str(self.plugin_id)})"

    def __repr__(self) -> str:
        return (
            f"Plugin("
            f"plugin_id={self.plugin_id!r}, "
            f"label={self.label!r}, "
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"version={self.version!r}, "
            f"compatible_framework_version={self.compatible_framework_version!r}, "
            f"authors={self.authors!r}, "
            f"component_dependencies={self.component_dependencies!r}, "
            f"third_party_dependencies={self.third_party_dependencies}"
            f"autostart={self.autostart!r}, "
            f")"
        )

    async def on_started(self) -> None: ...

    async def on_running(self) -> None: ...

    async def on_stopped(self) -> None: ...

    async def on_completed(self) -> None: ...

    async def on_cancelled(self) -> None: ...

    async def on_errored(self, runtime_error: BaseFrameworkException) -> None: ...

    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        ctx_to_str_map = {
            ComponentLifeCycleFatalContext.START: "starting",
            ComponentLifeCycleFatalContext.RUNNING: "running",
            ComponentLifeCycleFatalContext.STOP: "stopping",
            ComponentLifeCycleFatalContext.CANCEL: "being cancelled",
            ComponentLifeCycleFatalContext.ERROR: "handling a runtime error",
        }
        self.plugin_logger.opt(ansi=True).error(
            "<bold><red>Fatal error occurred within plugin while it was {}:</></>\n{}",
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        try:
            await super().start()
        except ComponentAlreadyStartedError:
            raise PluginAlreadyStartedError(
                plugin_str=str(self),
            )
        except LifeCycleStartFrameworkError as exc:
            raise PluginStartFrameworkError(
                plugin_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )

    async def stop(self) -> None:
        try:
            await super().stop()
        except ComponentNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            )
        except LifeCycleStopFrameworkError as exc:
            raise PluginStopFrameworkError(
                plugin_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            )

    async def cancel(self) -> None:
        try:
            await super().cancel()
        except ComponentNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            )

    def to_json(self) -> dict[str, Any]:
        return {
            "plugin_id": str(self.plugin_id),
            "label": self.label,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "compatible_framework_version": str(self.compatible_framework_version),
            "authors": list(self.authors),
            "component_dependencies": list(map(str, self.component_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
            "autostart": self.autostart,
            "status": self.status.to_json(),
        }


# async def _runtime_loop(self) -> None:
#     try:
#         await self.on_running()
#         self.status._transition_to_completed()
#         await self.on_completed()
#     except asyncio.CancelledError:
#         return
#     except PluginRuntimeError as exc:
#         self.status._transition_to_errored(error=exc)
#         try:
#             await self.on_errored(
#                 runtime_error=PluginRuntimeFrameworkError(
#                     plugin_str=str(self),
#                     error_message=exc.message,
#                     detail=exc.detail,
#                 )
#             )
#         except Exception as exc:
#             self.plugin_logger.opt(ansi=True).error(
#                 "<bold><red>Fatal error occurred while handling plugin "
#                 "error:</></>\n{}",
#                 traceback.format_exc(),
#             )
#             self.status._transition_to_fatal(exception=exc)
#     except Exception as exc:
#         self.plugin_logger.opt(ansi=True).error(
#             "<bold><red>{}</></>",
#             traceback.format_exc(),
#         )
#         self.status._transition_to_fatal(exception=exc)


# import asyncio
# import importlib.metadata
# import importlib.util
# import pathlib
# import sys
# import traceback
# import types
# import uuid
#
# import loguru
# from packaging import specifiers, version
#
# import consortium.server.server_singletons as server_singletons
# from consortium.framework.exceptions.plugins_framework_exceptions import (
#     PluginRuntimeError,
#     PluginStartError,
#     PluginStopError,
# )
# from consortium.framework.plugins import _plugin_status

# from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
#     PluginNotFoundError,
# )
# from consortium.server.server_logging import LoggerType
#
#
# class BasePlugin:
#     """
#     Base class for all plugins in the Consortium framework.
#
#     Attributes:
#         plugin_id:
#             The primary identifier for running instances of the plugin. This identifier
#             is a UUID4 string represented as a `uuid.UUID` object. Plugin IDs are used
#             as primary identifiers when attempting to access specific instances of the
#             corresponding plugin throughout the framework.
#         label:
#             The primary identifier for the class of plugin. This identifier is used to
#             persistently refer to plugins across different instances of the Consortium
#             server, typically for specifying plugin dependencies. This identifier must
#             be unique amongst all loaded plugins for a particular instance of a
#             Consortium server. The property of uniqueness will be enforced by the
#             framework at runtime.
#         name:
#             A human-readable name for the plugin, does not need to be unique. If no
#             name is provided, it is automatically set to the plugin's label.
#         description:
#             A description of the plugin.
#         version:
#             The version of the plugin. This version is a `packaging.version.Version`
#             object that represents a version string. The version string must be a valid
#             version string according to the `PEP 440` specification.
#         compatible_framework_version:
#             A specifier string that specifies the compatible framework version for the
#             plugin. The specifier string must be a valid specifier string according to
#             the `PEP 440` specification.
#         authors:
#             The author(s) that wrote the plugin.
#         autostart:
#             Whether to automatically run the plugin after the plugin service has loaded
#             it successfully.
#         plugin_dependencies:
#             The set of plugins that this plugin depends on. The plugin dependencies are
#             a set of tuples of plugin `labels` and the particular version specifier
#             that this plugin depends on. These plugins will all be loaded ahead of the
#             plugin that depends on them.
#         third_party_dependencies:
#             The set of third-party library dependencies that this plugin depends on. The
#             third party dependencies are a set of tuples of the library name as it is
#             imported and the particular version specifier that this plugin depends on.
#             This plugin will not load if the plugin service cannot import these
#             third-party libraries.
#         status:
#             The status of the plugin. This contains the plugin's current state as a
#             [`PluginState`][plugin_status.PluginState] string enum as well as the
#             relevant exception if it happens to be in an `ERRORED` or `FATAL` state.
#     """
#
#     label: str
#     name: str | None = None
#     description: str = ""
#     version: str | None = None
#     compatible_framework_version: str | None = None
#     authors: set[str] | None = None
#     autostart: bool = True
#     plugin_dependencies: set[tuple[str, str]] | None = None
#     third_party_dependencies: set[tuple[str, str]] | None = None
#
#     def __init__(self):
#         self.plugin_id = uuid.uuid4()
#
#         # The plugin status `state` attribute is set to
#         # `plugin_status.PluginState.INITIALIZED` at instantiation.
#         self.status = _plugin_status.PluginStatus()
#         # self.environment is used to store any information that the plugin may need
#         # to store and share amongst its user defined methods.
#         self.environment = types.SimpleNamespace()
#         # self.stop_plugin_event used to signal to the plugin runtime loop to exit.
#         # The implementation of the plugin runtime loop should check this event
#         # periodically and exit if it is set.
#         self.stop_plugin_event = asyncio.Event()
#         # Dynamically construct the `server_services` simple namespace object by
#         # iterating over the attributes of the `server_singletons` module and adding
#         # any object with an attribute that ends with `_service`.
#         services_dict = {}
#         for attr in dir(server_singletons):
#             if attr.endswith("_service"):
#                 services_dict[attr] = getattr(server_singletons, attr)
#         self.server_services = types.SimpleNamespace(**services_dict)
#         self.plugin_logger = loguru.logger.bind(
#             logger_name=f"Plugin {self}",
#             logger_type=LoggerType.PLUGIN_LOGGER,
#         )
#         self.plugin_project_folder = pathlib.Path(
#             sys.modules[self.__module__].__file__,
#         ).parents[0]
#
#         self._plugin_task = None
#
#     def __init_subclass__(cls, **kwargs):
#         # Constructing new sets for `authors`, `plugin_dependencies`, and
#         # `third_party_dependencies` to avoid mutable default arguments.
#         cls.authors = set() if cls.authors is None else set(cls.authors)
#         cls.plugin_dependencies = (
#             set() if cls.plugin_dependencies is None else set(cls.plugin_dependencies)
#         )
#         cls.third_party_dependencies = (
#             set()
#             if cls.third_party_dependencies is None
#             else set(cls.third_party_dependencies)
#         )
#
#         # Check the existence of a provided plugin label first so that we can
#         # reference the plugin name for every other error message.
#         if not hasattr(cls, "label"):
#             # The plugin is identified by its label, but at this point we are still
#             # validating the name parameter, so we refer to it by its filepath for now.
#             raise RequiredPluginConfigurationParameterNotDeclaredError(
#                 plugin_str=sys.modules[cls.__module__].__file__,
#                 parameter_name="label",
#             )
#         if not isinstance(cls.label, str):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=sys.modules[cls.__module__].__file__,
#                 parameter_name="label",
#                 parameter_type="str",
#             )
#         if not cls.label:
#             raise EmptyPluginLabelError(
#                 plugin_filepath=sys.modules[cls.__module__].__file__,
#             )
#         cls.name = cls.label if cls.name is None else cls.name
#         if not isinstance(cls.name, str):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=sys.modules[cls.__module__].__file__,
#                 parameter_name="name",
#                 parameter_type="str",
#             )
#         if not isinstance(cls.description, str):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=cls.label,
#                 parameter_name="description",
#                 parameter_type="str",
#             )
#         if cls.version:
#             if not isinstance(cls.version, str):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     parameter_name="version",
#                     parameter_type="str",
#                 )
#             try:
#                 cls.version = version.Version(cls.version)
#             except version.InvalidVersion:
#                 raise InvalidPluginVersionError(
#                     plugin_str=cls.label,
#                     version=cls.version,
#                 )
#         if cls.compatible_framework_version:
#             if not isinstance(cls.compatible_framework_version, str):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     parameter_name="compatible_framework_version",
#                     parameter_type="str",
#                 )
#             try:
#                 cls.compatible_framework_version: specifiers.SpecifierSet = (
#                     specifiers.SpecifierSet(cls.compatible_framework_version)
#                 )
#             except specifiers.InvalidSpecifier:
#                 raise InvalidFrameworkVersionSpecifierError(
#                     framework_version_specifier_str=cls.compatible_framework_version,
#                     plugin_str=cls.label,
#                 )
#         if not isinstance(cls.authors, set):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=cls.label,
#                 parameter_name="authors",
#                 parameter_type="set",
#             )
#         for author in cls.authors:
#             if not isinstance(author, str):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     error_message=(
#                         "The elements in the authors set must be strings for plugin "
#                         f"'{cls.name}'."
#                     ),
#                 )
#         if not isinstance(cls.autostart, bool):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=cls.label,
#                 parameter_name="autostart",
#                 parameter_type="bool",
#             )
#         if not isinstance(cls.plugin_dependencies, set):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=cls.label,
#                 parameter_name="plugin_dependencies",
#                 parameter_type="set",
#             )
#         for plugin_dependency in cls.plugin_dependencies:
#             if not isinstance(plugin_dependency, tuple):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     error_message=(
#                         "The elements in the plugin dependencies set must be tuples "
#                         f"for plugin '{cls.name}'."
#                     ),
#                 )
#             if (
#                 len(plugin_dependency) != 2
#                 or not isinstance(plugin_dependency[0], str)
#                 or not isinstance(plugin_dependency[1], str)
#             ):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     error_message=(
#                         "The elements in the plugin dependencies set must be tuples "
#                         f"of strings of length 2 for plugin '{cls.name}'."
#                     ),
#                 )
#             try:
#                 cls.plugin_dependencies.remove(plugin_dependency)
#                 cls.plugin_dependencies.add(
#                     (
#                         plugin_dependency[0],
#                         specifiers.SpecifierSet(plugin_dependency[1]),
#                     ),
#                 )
#             except specifiers.InvalidSpecifier:
#                 raise InvalidPluginDependencyVersionSpecifierError(
#                     plugin_str=cls.label,
#                     plugin_dependency_name=plugin_dependency[0],
#                     plugin_dependency_version_specifier=plugin_dependency[1],
#                 )
#         if not isinstance(cls.third_party_dependencies, set):
#             raise InvalidPluginConfigurationParameterTypeError(
#                 plugin_str=cls.label,
#                 parameter_name="third_party_dependencies",
#                 parameter_type="set",
#             )
#         for third_party_dependency in cls.third_party_dependencies:
#             if not isinstance(third_party_dependency, tuple):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     error_message=(
#                         "The elements in the third party dependencies set must be "
#                         f"tuples for plugin '{cls.name}'."
#                     ),
#                 )
#             if (
#                 len(third_party_dependency) != 2
#                 or not isinstance(third_party_dependency[0], str)
#                 or not isinstance(third_party_dependency[1], str)
#             ):
#                 raise InvalidPluginConfigurationParameterTypeError(
#                     plugin_str=cls.label,
#                     error_message=(
#                         "The elements in the third party dependencies set must be "
#                         f"tuples of strings of length 2 for plugin '{cls.name}'."
#                     ),
#                 )
#             try:
#                 cls.third_party_dependencies.remove(third_party_dependency)
#                 cls.third_party_dependencies.add(
#                     (
#                         third_party_dependency[0],
#                         specifiers.SpecifierSet(third_party_dependency[1]),
#                     ),
#                 )
#             except specifiers.InvalidSpecifier:
#                 raise InvalidThirdPartyDependencyVersionSpecifierError(
#                     plugin_str=cls.label,
#                     third_party_dependency_name=third_party_dependency[0],
#                     third_party_dependency_version_specifier=third_party_dependency[1],
#                 )
#
#         super().__init_subclass__(**kwargs)
#
#     def __str__(self) -> str:
#         return f"'{self.name}' [{self.label}] (ID: {str(self.plugin_id)})"
#
#     def __repr__(self) -> str:
#         return (
#             f"Plugin("
#             f"plugin_id={self.plugin_id!r}, "
#             f"label={self.label!r}, "
#             f"name={self.name!r}, "
#             f"description={self.description!r}, "
#             f"version={self.version!r}, "
#             f"compatible_framework_version={self.compatible_framework_version!r}, "
#             f"authors={self.authors!r}, "
#             f"autostart={self.autostart!r}, "
#             f"plugin_dependencies={self.plugin_dependencies!r}, "
#             f"third_party_dependencies={self.third_party_dependencies!r}"
#             f")"
#         )
#
#     async def on_plugin_started(self) -> None: ...
#
#     async def on_plugin_running(self) -> None: ...
#
#     async def on_plugin_stopped(self) -> None: ...
#
#     async def on_plugin_cancelled(self) -> None: ...
#
#     async def on_plugin_errored(self, exception: Exception) -> None: ...
#
#     async def start_plugin(self) -> None:
#         if self.status.state == _plugin_status.PluginState.STARTED:
#             raise PluginAlreadyRunningError(
#                 plugin_str=str(self),
#                 error_message=(
#                     "The plugin cannot be started because it is already running"
#                 ),
#             )
#
#         # Check third party dependencies.
#         for dependency in self.third_party_dependencies:
#             # Check if the dependency exists. We use `find_spec` instead of trying to
#             # import the library directly because that has the side effect of executing
#             # code.
#             if importlib.util.find_spec(dependency[0]) is None:
#                 raise ThirdPartyDependencyNotFoundError(
#                     plugin_str=str(self),
#                     third_party_dependency_name=dependency[0],
#                 )
#             try:
#                 version_str = importlib.metadata.version(dependency[0])
#                 if version.Version(version_str) not in dependency[1]:
#                     raise IncompatibleThirdPartyDependencyVersionError(
#                         plugin_str=str(self),
#                         third_party_dependency_name=dependency[0],
#                         third_party_dependency_version_specifier=dependency[1],
#                         third_party_dependency_version=version_str,
#                     )
#             except importlib.metadata.PackageNotFoundError:
#                 # We have already checked for the import error above, so this should not
#                 # happen unless a library that was not installed via PyPi is being
#                 # used, in which case versioning support is not provided.
#                 pass
#
#         # Check plugin dependencies.
#         for dependency in self.plugin_dependencies:
#             try:
#                 dependency_plugin = (
#                     self.server_services.plugin_service.get_plugin_by_label(
#                         label=dependency[0],
#                     )
#                 )
#                 if dependency_plugin.status.state != _plugin_status.PluginState.STARTED:
#                     raise PluginDependencyNotRunningError(
#                         plugin_str=str(self),
#                         plugin_dependency_name=dependency[0],
#                     )
#             except PluginNotFoundError:
#                 raise PluginDependencyNotFoundError(
#                     plugin_str=str(self),
#                     plugin_dependency_name=dependency[0],
#                 )
#
#             if dependency[1] and dependency_plugin.version not in dependency[1]:
#                 raise IncompatiblePluginDependencyVersionError(
#                     plugin_str=str(self),
#                     plugin_dependency_name=dependency[0],
#                     plugin_dependency_version_specifier=dependency[1],
#                     plugin_dependency_version=str(dependency_plugin.version),
#                 )
#
#         # Clear the signal to the plugin to stop running if it is set, so it won't
#         # instantly stop.
#         self.stop_plugin_event.clear()
#
#         # The plugin is now started.
#         self.status._transition_to_started()
#         try:
#             await self.on_plugin_started()
#         # PluginStartError is raised within on_plugin_started() to abort the
#         # plugin start process if preconditions are not met.
#         except PluginStartError as exc:
#             # The plugin is now initialized.
#             self.status._transition_to_initialized()
#             raise PluginStartFrameworkError(
#                 plugin_str=str(self),
#                 error_message=exc.message,
#                 detail=exc.detail,
#             )
#         except Exception as exc:
#             self.plugin_logger.opt(ansi=True).error(
#                 "<bold><red>Fatal error occurred while starting plugin:</></>\n{}",
#                 traceback.format_exc(),
#             )
#             # The plugin is now fatally errored.
#             self.status._transition_to_fatal(
#                 plugin_str=str(self),
#                 exception=exc,
#             )
#             raise exc
#
#         self._plugin_task = asyncio.create_task(self._run_plugin())
#
#     async def stop_plugin(self) -> None:
#         if self.status.state != _plugin_status.PluginState.RUNNING:
#             raise PluginNotRunningError(
#                 plugin_str=str(self),
#                 error_message="The plugin cannot be stopped because it is not running.",
#             )
#
#         try:
#             await self.on_plugin_stopped()
#         # PluginStopError is raised within on_plugin_stopped() to abort the
#         # plugin stop process if preconditions are not met.
#         except PluginStopError as exc:
#             # The plugin has not changed from its running state.
#             self.status._transition_to_running()
#             raise PluginStopFrameworkError(
#                 plugin_str=str(self),
#                 error_message=exc.message,
#                 detail=exc.detail,
#             )
#         except Exception as exc:
#             self.plugin_logger.opt(ansi=True).error(
#                 "<bold><red>Fatal error occurred while stopping plugin:</></>\n{}",
#                 traceback.format_exc(),
#             )
#             # The plugin is now fatally errored.
#             self.status._transition_to_fatal(
#                 plugin_str=str(self),
#                 exception=exc,
#             )
#             raise exc
#
#         # Signal to the plugin to stop running.
#         self.stop_plugin_event.set()
#
#     async def cancel_plugin(self) -> None:
#         if self.status.state != _plugin_status.PluginState.RUNNING:
#             raise PluginNotRunningError(
#                 plugin_str=str(self),
#                 error_message=(
#                     "The plugin cannot be cancelled because it is not running."
#                 ),
#             )
#
#         self._plugin_task.cancel()
#
#         try:
#             # Wait for the task to finish whether by completing or cancelling.
#             await self._plugin_task
#         except asyncio.CancelledError:
#             # The task was cancelled as expected.
#             pass
#         except Exception as exc:
#             self.plugin_logger.opt(ansi=True).error(
#                 "<bold><red>Fatal error occurred while cancelling plugin:</></>\n{}",
#                 traceback.format_exc(),
#             )
#             # The plugin is now fatally errored due to an unexpected error during
#             # cancellation.
#             self.status._transition_to_fatal(
#                 plugin_str=str(self),
#                 exception=exc,
#             )
#             raise exc from None
#         finally:
#             try:
#                 await self.on_plugin_cancelled()
#             except Exception as exc:
#                 self.plugin_logger.opt(ansi=True).error(
#                     "<bold><red>{}</></>",
#                     traceback.format_exc(),
#                 )
#                 # The plugin is now fatally errored.
#                 self.status._transition_to_fatal(
#                     plugin_str=str(self),
#                     exception=exc,
#                 )
#                 raise exc
#
#     def to_json(self) -> dict[str, str | bool | dict | list[str]]:
#         return {
#             "plugin_id": str(self.plugin_id),
#             "label": self.label,
#             "name": self.name,
#             "description": self.description,
#             "version": str(self.version),
#             "compatible_framework_version": str(self.compatible_framework_version),
#             "authors": list(self.authors),
#             "autostart": self.autostart,
#             "plugin_dependencies": list(map(str, self.plugin_dependencies)),
#             "third_party_dependencies": list(map(str, self.third_party_dependencies)),
#             "status": self.status.to_json(),
#         }
#
#     async def _run_plugin(self):
#         try:
#             try:
#                 # The plugin is now running.
#                 self.status._transition_to_running()
#                 await self.on_plugin_running()
#
#                 # The plugin is now stopped.
#                 self.status._transition_to_stopped()
#                 self._plugin_task = None
#             except asyncio.CancelledError:
#                 # The plugin is now cancelled.
#                 self.status._transition_to_cancelled()
#                 self._plugin_task = None
#             except PluginRuntimeError as exc:
#                 # The plugin is now errored.
#                 self.status._transition_to_errored(
#                     error=PluginRuntimeFrameworkError(
#                         plugin_str=str(self),
#                         error_message=exc.message,
#                         detail=exc.detail,
#                     ),
#                 )
#                 try:
#                     await self.on_plugin_errored(exception=exc)
#                 except Exception as exc:
#                     self.plugin_logger.opt(ansi=True).error(
#                         "<bold><red>Fatal error occurred while handling plugin "
#                         "error:</></>\n{}",
#                         traceback.format_exc(),
#                     )
#                     # The plugin is now fatally errored due to some issue in the error
#                     # handling routine itself.
#                     self.status._transition_to_fatal(
#                         plugin_str=str(self),
#                         exception=exc,
#                     )
#         except Exception as exc:
#             self.plugin_logger.opt(ansi=True).error(
#                 "<bold><red>{}</></>",
#                 traceback.format_exc(),
#             )
#             self.status._transition_to_fatal(
#                 plugin_str=str(self),
#                 exception=exc,
#             )
#             # The plugin is now fatally errored due to some issue in the plugin runtime
#             # loop itself.
#             try:
#                 await self.on_plugin_errored(exc)
#             except Exception as exc:
#                 self.plugin_logger.opt(ansi=True).error(
#                     "<bold><red>Fatal error occurred within plugin runtime:</></>\n{}",
#                     traceback.format_exc(),
#                 )
#                 self.status._transition_to_fatal(
#                     plugin_str=str(self),
#                     exception=exc,
#                 )
