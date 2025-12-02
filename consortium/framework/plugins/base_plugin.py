import pathlib
import sys
import traceback
import types
import uuid
from typing import Any, get_type_hints

import loguru
import packaging.requirements as requirements
import packaging.specifiers as specifiers
import packaging.version as version
from pydantic import ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._life_cycles import LifeCycle, LifeCycleFatalContext
from consortium.framework.plugins._plugin_metadata_model import PluginMetadataModel
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.lifecycle_exceptions import (
    LifeCycleAlreadyStartedError,
    LifeCycleNotRunningError,
    LifeCycleStartError as LifeCycleStartFrameworkError,
    LifeCycleStopError as LifeCycleStopFrameworkError,
)
from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (  # IncompatiblePluginDependencyVersionError,; IncompatibleThirdPartyDependencyVersionError,; PluginDependencyNotFoundError,; PluginDependencyNotRunningError,; ThirdPartyDependencyNotFoundError,
    EmptyPluginLabelError,
    InvalidFrameworkVersionSpecifierError,
    InvalidPluginConfigurationParameterTypeError,
    InvalidPluginDependencyVersionSpecifierError,
    InvalidPluginVersionError,
    InvalidThirdPartyDependencyVersionSpecifierError,
    MissingPluginConfigurationParameterError,
    PluginAlreadyStartedError,
    PluginNotRunningError,
    PluginRuntimeError as PluginRuntimeFrameworkError,
    PluginStartError as PluginStartFrameworkError,
    PluginStopError as PluginStopFrameworkError,
)
from consortium.server.server_logging import LoggerType


class BasePlugin(LifeCycle):
    label: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    compatible_framework_version: str | None = None
    authors: set[str] | None = None
    autostart: bool = True
    plugin_dependencies: set[str] | None = None

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
            logger_name=f"Plugin {self}",
            logger_type=LoggerType.PLUGIN_LOGGER,
        )
        self.plugin_project_folder = pathlib.Path(
            sys.modules[self.__module__].__file__,
        ).parents[0]
        super().__init__()

    def __init_subclass__(cls, **kwargs):
        cls.authors = cls.authors or set()
        cls.plugin_dependencies = cls.plugin_dependencies or set()
        # Third-party dependencies get added in when the plugin is loaded if it declared
        # any in its `pyproject.toml` file
        cls.third_party_dependencies = set()

        # Use the module filepath as a reference to the plugin if its label is not defined
        plugin_str = (
            cls.label
            if hasattr(cls, "label")
            else f"{cls.__name__} ({sys.modules[cls.__module__].__file__})"
        )
        expected_attrs_and_types_map = get_type_hints(cls)

        # Check all attributes exist
        for attr in expected_attrs_and_types_map.keys():
            if not hasattr(cls, attr):
                raise MissingPluginConfigurationParameterError(
                    plugin_str=plugin_str,
                    parameter_name=attr,
                )

        # Check all class attributes are of the expected type
        try:
            PluginMetadataModel(
                label=cls.label,
                name=cls.name,
                description=cls.description,
                version=cls.version,
                compatible_framework_version=cls.compatible_framework_version,
                authors=cls.authors,
                autostart=cls.autostart,
                plugin_dependencies=cls.plugin_dependencies,
            )
        except ValidationError as exc:
            attr = exc.errors()[0]["loc"][0]
            raise InvalidPluginConfigurationParameterTypeError(
                plugin_str=plugin_str,
                parameter_name=attr,
                parameter_type=expected_attrs_and_types_map[attr],
            )

        # Perform semantic checking of specific attributes and reassign as needed
        if not cls.label:
            raise EmptyPluginLabelError(
                plugin_filepath=sys.modules[cls.__module__].__file__,
            )
        cls.name = cls.label if cls.name is None else cls.name
        try:
            cls.version = version.Version(cls.version) if cls.version else None
        except version.InvalidVersion:
            raise InvalidPluginVersionError(
                plugin_str=cls.label,
                version=cls.version,
            )
        try:
            cls.compatible_framework_version = (
                specifiers.SpecifierSet(cls.compatible_framework_version)
                if cls.compatible_framework_version
                else None
            )
        except specifiers.InvalidSpecifier:
            raise InvalidFrameworkVersionSpecifierError(
                framework_version_specifier_str=cls.compatible_framework_version,
                plugin_str=cls.label,
            )
        new_dependencies = set()
        for entry in cls.plugin_dependencies:
            try:
                dependency = requirements.Requirement(entry)
            except requirements.InvalidRequirement:
                raise InvalidPluginDependencyVersionSpecifierError(
                    plugin_str=cls.label,
                    invalid_dependency_entry=entry,
                )
            new_dependencies.add(dependency)

        cls.plugin_dependencies = new_dependencies

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"'{self.name}' [{self.label}] (ID: {str(self.plugin_id)})"

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
            f"autostart={self.autostart!r}, "
            f"plugin_dependencies={self.plugin_dependencies!r}, "
            f"third_party_dependencies={self.third_party_dependencies}"
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
        fatal_context: LifeCycleFatalContext,
    ) -> None:
        ctx_to_str_map = {
            LifeCycleFatalContext.START: "starting",
            LifeCycleFatalContext.RUNNING: "running",
            LifeCycleFatalContext.STOP: "stopping",
            LifeCycleFatalContext.CANCEL: "being cancelled",
            LifeCycleFatalContext.ERROR: "handling a runtime error",
        }
        self.plugin_logger.opt(ansi=True).error(
            "<bold><red>Fatal error occurred within plugin while it was {}:</></>\n{}",
            ctx_to_str_map[fatal_context],
            traceback.format_exc(),
        )

    async def start(self) -> None:
        try:
            await super().start()
        except LifeCycleAlreadyStartedError:
            raise PluginAlreadyStartedError(
                plugin_str=str(self),
            )
        except LifeCycleStartFrameworkError as exc:
            raise PluginStartFrameworkError(
                plugin_str=str(self),
                message=exc.message,
                detail=exc.detail,
            )

    async def stop(self) -> None:
        try:
            await super().stop()
        except LifeCycleNotRunningError:
            raise PluginNotRunningError(
                plugin_str=str(self),
            )
        except LifeCycleStopFrameworkError as exc:
            raise PluginStopFrameworkError(
                plugin_str=str(self),
                message=exc.message,
                detail=exc.detail,
            )

    async def cancel(self) -> None:
        try:
            await super().cancel()
        except LifeCycleNotRunningError:
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
            "autostart": self.autostart,
            "plugin_dependencies": list(map(str, self.plugin_dependencies)),
            "third_party_dependencies": list(map(str, self.third_party_dependencies)),
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
