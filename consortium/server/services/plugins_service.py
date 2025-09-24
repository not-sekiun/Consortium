from loguru import logger

from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    DuplicatePluginLabelError,
    IncompatiblePluginFrameworkVersionError,
    InternalPluginProjectError,
    InternalPluginStartError,
    InternalPluginStopError,
    InvalidPluginProjectManifestFileJSONError,
    InvalidPluginProjectManifestFileSchemaError,
    PluginAlreadyRegisteredError,
    PluginLabelNotFoundError,
    PluginLoadingError,
    PluginNotFoundError,
    PluginProjectInterfaceError,
    PluginProjectManifestFileNotFoundError,
    PluginProjectPluginFileNotFoundError,
    PluginProjectSymbolNotFoundError,
    PluginStopTimeoutError,
    PluginUnloadingError,
)


class PluginsService:
    def __init__(self):
        self._plugins = {}
        self.plugins_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.plugins_service_logger.debug("Started Plugins Service")
        self._restart_plugin_tasks = set()

    def __str__(self):
        return "Plugins Service"

    def __repr__(self):
        return "PluginsService()"

    def get_plugin_by_plugin_id(self, plugin_id: str) -> "BasePlugin":
        """
        Returns a plugin object by its plugin id. The plugin must be registered to the
        service.

        Args:
            plugin_id (str): The plugin id to search for.

        Returns:
            BasePlugin: The plugin object if found.

        Raises:
            PluginNotFoundError: If the plugin id is not found in the service.
        """
        try:
            plugin = self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFoundError(plugin_id=plugin_id)

        self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
        return plugin

    def get_plugins_by_label(self, label: str) -> list["BasePlugin"]:
        """
        Returns all plugins that have the provided label. Multiple plugins can have
        the same label. The plugins must be registered to the service.

        Args:
            label (str): The label to search for.

        Returns:
            BasePlugin: The plugin object if found.

        Raises:
            PluginLabelNotFoundError: If the plugin label is not found in the service.
        """
        plugins = []
        for plugin in self._plugins.values():
            if plugin.label == label:
                self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
                plugins.append(plugin)

        if plugins:
            return plugins

        raise PluginLabelNotFoundError(label=label)

    def get_all_plugins(self) -> list["BasePlugin"]:
        """
        Returns a list of all plugins registered to the service.

        Returns:
            list[BasePlugin]: A list of all plugins registered to the service.
        """
        self.plugins_service_logger.debug(
            f"Retrieved all plugins ({len(self._plugins)} plugin(s) retrieved).",
        )
        return list(self._plugins.values())


# import asyncio
# import importlib
# import importlib.metadata
# import json
# import pathlib
# import traceback
#
# import jsonschema
# from loguru import logger
# from packaging import version
#
# from consortium.framework.plugins._plugin_status import PluginState
# # from consortium.framework.plugins.base_plugin import BasePlugin
# from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
#     BaseFrameworkException,
# )
# from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
#     PluginsFrameworkError,
# )
# from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
#     DuplicatePluginLabelError,
#     IncompatiblePluginFrameworkVersionError,
#     InternalPluginProjectError,
#     InternalPluginStartError,
#     InternalPluginStopError,
#     InvalidPluginProjectManifestFileJSONError,
#     InvalidPluginProjectManifestFileSchemaError,
#     PluginAlreadyRegisteredError,
#     PluginLabelNotFoundError,
#     PluginLoadingError,
#     PluginNotFoundError,
#     PluginProjectInterfaceError,
#     PluginProjectManifestFileNotFoundError,
#     PluginProjectPluginFileNotFoundError,
#     PluginProjectSymbolNotFoundError,
#     PluginStopTimeoutError,
#     PluginUnloadingError,
# )
# from consortium.server.server_config import (
#     CONSORTIUM_HOME_DIRECTORY_PATH,
#     CONSORTIUM_PLUGINS_DIRECTORY_PATH,
#     SERVER_RELEASE,
# )
#
# class PluginsService:
#     def __init__(self):
#         self._plugins = {}
#         self.plugins_service_logger = logger.bind(
#             logger_name=str(self),
#         )
#         self.plugins_service_logger.debug("Started Plugins Service")
#         self._restart_plugin_tasks = set()
#
#     def __str__(self):
#         return "Plugins Service"
#
#     def __repr__(self):
#         return "PluginsService()"
#
#     def get_plugin_from_plugin_project_folder(
#         self,
#         plugin_project_folder: pathlib.Path,
#         ignore_enabled_plugin_flag: bool = False,
#     ) -> BasePlugin | None:
#         """
#         Retrieves a plugin instance from a specified plugin project folder. The method
#         performs multiple validation steps to ensure the plugin project structure,
#         manifest schema, and framework compatibility are correct. Ensures the plugin is
#         enabled unless overridden by an input flag. Valid plugins are initialized and
#         returned.
#
#         Args:
#             plugin_project_folder (pathlib.Path): The path of the folder containing the
#                 plugin project files.
#             ignore_enabled_plugin_flag (bool): If True, the method bypasses the
#                 enabled state check in the plugin project manifest. Defaults to False.
#
#         Returns:
#             BasePlugin | None: An instance of the plugin if successfully retrieved, or
#                 None if the plugin is disabled and the enabled check is not overridden.
#
#         Raises:
#             PluginProjectManifestFileNotFoundError: If the plugin project manifest
#                 file, `plugin_project_manifest.json`, is missing.
#             InvalidPluginProjectManifestFileJSONError: If the manifest file,
#                 `plugin_project_manifest.json`, contains invalid JSON.
#             InvalidPluginProjectManifestFileSchemaError: If the manifest file
#                 `plugin_project_manifest.json` doesn't follow the expected schema.
#             PluginProjectPluginFileNotFoundError: If the file specified in the plugin
#                 manifest, `plugin_project_manifest.json`, cannot be found.
#             PluginProjectSymbolNotFoundError: If the symbol specified in the plugin
#                 manifest, `plugin_project_manifest.json`, is not found in the specified
#                 file.
#             PluginProjectInterfaceError: If the plugin class does not correctly inherit
#                 from the [`BasePlugin`][consortium.framework.plugins.base_plugin.BasePlugin]
#                 class.
#             IncompatiblePluginFrameworkVersionError: If the plugin is incompatible with
#                 the current framework version.
#             InternalPluginProjectError: If an unhandled exception is raised within the
#                 plugin while initializing the plugin.
#         """
#         plugin_project_manifest_file_path = (
#             plugin_project_folder / "plugin_project_manifest.json"
#         )
#         plugin_project_manifest_json_schema = {
#             "type": "object",
#             "properties": {
#                 "plugin": {
#                     "type": "object",
#                     "properties": {
#                         "filepath": {"type": "string"},
#                         "symbol": {"type": "string"},
#                     },
#                     "required": ["filepath", "symbol"],
#                     "additionalProperties": False,
#                 },
#                 "enabled": {
#                     "type": "boolean",
#                 },
#             },
#             "required": ["plugin", "enabled"],
#             "additionalProperties": False,
#         }
#
#         # Check if the manifest file exists and follows the correct JSON schema.
#         try:
#             with plugin_project_manifest_file_path.open(
#                 "r",
#             ) as plugin_project_manifest_file:
#                 plugin_project_manifest_json = json.load(plugin_project_manifest_file)
#                 jsonschema.validate(
#                     plugin_project_manifest_json,
#                     plugin_project_manifest_json_schema,
#                 )
#         except FileNotFoundError:
#             raise PluginProjectManifestFileNotFoundError
#         except json.JSONDecodeError:
#             raise InvalidPluginProjectManifestFileJSONError(
#                 plugin_project_folder=str(plugin_project_folder),
#             )
#         except jsonschema.ValidationError as exc:
#             raise InvalidPluginProjectManifestFileSchemaError(
#                 plugin_project_folder=str(plugin_project_folder),
#                 json_schema_error_message=exc.message,
#             )
#
#         # Check if the plugin project is enabled or not.
#         if (
#             not plugin_project_manifest_json["enabled"]
#             and not ignore_enabled_plugin_flag
#         ):
#             self.plugins_service_logger.info(
#                 "Skipped loading plugin from '{}' because it was disabled.",
#                 str(plugin_project_folder),
#             )
#             return None
#
#         # Check for a valid plugin project folder structure as specified by the
#         # manifest file.
#         plugin_file = plugin_project_folder / pathlib.Path(
#             plugin_project_manifest_json["plugin"]["filepath"],
#         )
#         plugin_symbol = plugin_project_manifest_json["plugin"]["symbol"]
#
#         if not plugin_file.exists():
#             raise PluginProjectPluginFileNotFoundError(
#                 plugin_file=str(plugin_file),
#                 plugin_project_folder=str(plugin_project_folder),
#             )
#
#         # Check for valid symbol names in the required plugin project file.
#         plugin_module_path = ".".join(
#             plugin_file.relative_to(
#                 CONSORTIUM_HOME_DIRECTORY_PATH,
#             ).parts,
#         )[: -len(".py")]
#
#         try:
#             plugin_module = importlib.import_module(plugin_module_path)
#             plugin_class = getattr(
#                 plugin_module,
#                 plugin_symbol,
#             )
#         except AttributeError:
#             raise PluginProjectSymbolNotFoundError(
#                 symbol_name=plugin_symbol,
#                 plugin_project_folder=str(plugin_project_folder),
#                 plugin_file=str(plugin_file),
#             )
#         except PluginsFrameworkError as exc:
#             raise exc from None
#         # This should only catch errors that are not related to the plugin project.
#         except Exception as exc:
#             raise InternalPluginProjectError(
#                 plugin_project_folder=str(plugin_project_folder),
#                 internal_error_message=str(exc),
#             )
#
#         # Check for correct inheritance and instantiation of classes.
#         if not issubclass(plugin_class, BasePlugin):
#             raise PluginProjectInterfaceError(
#                 plugin_project_folder=str(plugin_project_folder),
#                 plugin_symbol=plugin_symbol,
#             )
#         try:
#             plugin_object = plugin_class()
#         except PluginsFrameworkError as exc:
#             raise exc from None
#         except Exception as exc:
#             raise InternalPluginProjectError(
#                 plugin_project_folder=str(plugin_project_folder),
#                 internal_error_message=str(exc),
#             )
#
#         # Check the plugin's framework version compatibility.
#         if (
#             version.Version(SERVER_RELEASE.version)
#             not in plugin_object.compatible_framework_version
#         ):
#             raise IncompatiblePluginFrameworkVersionError(
#                 plugin_str=str(plugin_object),
#                 plugin_framework_version=str(
#                     plugin_object.compatible_framework_version,
#                 ),
#                 framework_version=SERVER_RELEASE.version,
#             )
#
#         self.plugins_service_logger.debug(
#             f"Retrieved plugin {plugin_object!r} from plugin project folder: "
#             f"{plugin_project_folder}",
#         )
#         return plugin_object
#
#     def register_plugin(
#         self,
#         plugin: BasePlugin,
#     ) -> None:
#         """
#         Registers a plugin instance with the system.
#
#         This method registers a plugin by adding it to an internal storage
#         and logs the successful registration. Each plugin instance is
#         uniquely identified and referred to by its `plugin_id`. Note that registering a
#         plugin will not automatically start it.
#
#         Args:
#             plugin (BasePlugin): The plugin instance to register. It must
#                 have a unique `plugin_id` and conform to the `BasePlugin`
#                 interface. Additionally, if the plugin specifies a `label` attribute, it
#                 must be unique across all registered plugins.
#
#         Returns:
#             None
#
#         Raises:
#             PluginAlreadyRegisteredError: If a plugin with the same `plugin_id` is
#                 already registered.
#             DuplicatePluginLabelError: If a plugin with the same `label` attribute is
#                 already registered.
#         """
#         if str(plugin.plugin_id) in self._plugins:
#             raise PluginAlreadyRegisteredError(
#                 plugin_str=str(plugin),
#                 plugin_id=str(plugin.plugin_id),
#             )
#         if plugin.label and plugin.label in [
#             plugin.label for plugin in self._plugins if plugin.label
#         ]:
#             raise DuplicatePluginLabelError(
#                 plugin_str=str(plugin),
#                 plugin_label=plugin.label,
#             )
#
#         self._plugins[str(plugin.plugin_id)] = plugin
#         self.plugins_service_logger.debug(f"Registered plugin: {plugin!r}")
#
#     def register_plugin_from_plugin_project_folder(
#         self,
#         plugin_project_folder: pathlib.Path,
#         ignore_enabled_plugin_flag: bool = False,
#     ) -> BasePlugin | None:
#         """
#         Registers a plugin from the provided plugin project folder into the
#         plugin manager system. If the plugin is disabled and the
#         `ignore_enabled_plugin_project_flag` is set to False, the plugin will not be
#         registered. On successful registration, the plugin is added to the internal
#         plugin registry. Note that this method does not start the plugin; it only
#         registers it.
#
#         Args:
#             plugin_project_folder (pathlib.Path): The path to the folder containing the
#                 plugin project from which the plugin is to be registered.
#             ignore_enabled_plugin_flag (bool): Specifies whether to ignore the
#                 flag indicating whether the plugin is enabled in the provided project.
#                 Defaults to False.
#
#         Returns:
#             BasePlugin | None: Returns the registered plugin instance if the plugin is
#             successfully registered; otherwise, returns None.
#
#         Raises:
#             PluginProjectManifestFileNotFoundError: If the plugin project manifest
#                 file, `plugin_project_manifest.json`, is missing.
#             InvalidPluginProjectManifestFileJSONError: If the manifest file,
#                 `plugin_project_manifest.json`, contains invalid JSON.
#             InvalidPluginProjectManifestFileSchemaError: If the manifest file
#                 `plugin_project_manifest.json` doesn't follow the expected schema.
#             PluginProjectPluginFileNotFoundError: If the file specified in the plugin
#                 manifest, `plugin_project_manifest.json`, cannot be found.
#             PluginProjectSymbolNotFoundError: If the symbol specified in the plugin
#                 manifest, `plugin_project_manifest.json`, is not found in the specified
#                 file.
#             PluginProjectInterfaceError: If the plugin class does not correctly inherit
#                 from the [`BasePlugin`][consortium.framework.plugins.base_plugin.BasePlugin]
#                 class.
#             IncompatiblePluginFrameworkVersionError: If the plugin is incompatible with
#                 the current framework version.
#             InternalPluginProjectError: If an unhandled exception is raised within the
#                 plugin while initializing the plugin.
#             PluginAlreadyRegisteredError: If a plugin with the same `plugin_id` is
#                 already registered.
#             DuplicatePluginLabelError: If a plugin with the same `label` attribute is
#                 already registered.
#         """
#         plugin = self.get_plugin_from_plugin_project_folder(
#             plugin_project_folder=plugin_project_folder,
#             ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
#         )
#
#         # If `plugin` is `None`, it implies a disabled plugin was attempted to be
#         # registered.
#         if plugin is None:
#             return None
#
#         self.register_plugin(plugin=plugin)
#         return plugin
#
#     async def load_plugin_from_plugin_project_folder(
#         self,
#         plugin_project_folder: pathlib.Path,
#         ignore_enabled_plugin_flag: bool = False,
#     ) -> BasePlugin | None:
#         """
#         Loads a plugin from its project folder. The plugin is registered to the plugin
#         service and additionally started if its `autostart` attribute is set to True.
#
#         This function integrates with the plugin registration mechanism and ensures
#         that any plugin meeting the specified requirements is properly initialized
#         and prepared for further usage.
#
#         Args:
#             plugin_project_folder (pathlib.Path): The directory path where the plugin's
#                 project files are stored.
#             ignore_enabled_plugin_flag (bool): Optional flag indicating whether the
#                 'enabled' status of the plugin should be ignored. Defaults to False.
#
#         Returns:
#             BasePlugin | None: Returns the loaded plugin instance if successful, or
#             None if the plugin is disabled or cannot be loaded.
#
#         Raises:
#             PluginProjectManifestFileNotFoundError: If the plugin project manifest
#                 file, `plugin_project_manifest.json`, is missing.
#             InvalidPluginProjectManifestFileJSONError: If the manifest file,
#                 `plugin_project_manifest.json`, contains invalid JSON.
#             InvalidPluginProjectManifestFileSchemaError: If the manifest file
#                 `plugin_project_manifest.json` doesn't follow the expected schema.
#             PluginProjectPluginFileNotFoundError: If the file specified in the plugin
#                 manifest, `plugin_project_manifest.json`, cannot be found.
#             PluginProjectSymbolNotFoundError: If the symbol specified in the plugin
#                 manifest, `plugin_project_manifest.json`, is not found in the specified
#                 file.
#             PluginProjectInterfaceError: If the plugin class does not correctly inherit
#                 from the [`BasePlugin`][consortium.framework.plugins.base_plugin.BasePlugin]
#                 class.
#             IncompatiblePluginFrameworkVersionError: If the plugin is incompatible with
#                 the current framework version.
#             InternalPluginProjectError: If an unhandled exception is raised within the
#                 plugin while initializing the plugin.
#             PluginAlreadyRegisteredError: If a plugin with the same `plugin_id` is
#                 already registered.
#             DuplicatePluginLabelError: If a plugin with the same `label` attribute is
#                 already registered.
#             ThirdPartyDependencyNotFoundError: If the plugin requires a third party
#                 dependency that is not installed in the framework.
#             IncompatibleThirdPartyDependencyVersionError: If the plugin requires a
#                 third party dependency that has a version not compatible with the one
#                 installed in the framework.
#             PluginDependencyNotFoundError: If the plugin requires another plugin that
#                 is not installed in the framework.
#             IncompatiblePluginDependencyVersionError: If the plugin requires another
#                 plugin to be installed that has a version not compatible with the one
#                 installed in the framework.
#             PluginDependencyNotRunningError: If the plugin requires another plugin that
#                 is installed and of the appropriate version but is not currently
#                 running.
#             PluginAlreadyRunningError: If the plugin is already running.
#             PluginStartError: If the plugin failed to start for any reason.
#             InternalPluginStartError: If an unhandled exception is raised within the
#                 plugin while starting the plugin.
#         """
#         plugin = self.register_plugin_from_plugin_project_folder(
#             plugin_project_folder=plugin_project_folder,
#             ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
#         )
#
#         # `plugin` being `None` implies a disabled plugin was attempted to be loaded.
#         if plugin is None:
#             return None
#
#         if plugin.autostart:
#             try:
#                 await plugin.start_plugin()
#             except BaseFrameworkException:
#                 raise
#             except Exception as exc:
#                 raise InternalPluginStartError(
#                     plugin_str=str(plugin),
#                     internal_error_message=str(exc),
#                 ) from exc
#
#         self._plugins[str(plugin.plugin_id)] = plugin
#         self.plugins_service_logger.success(f"Loaded plugin: {plugin}")
#         self.plugins_service_logger.debug(f"Loaded plugin: {plugin!r}")
#         return plugin
#
#     async def unload_plugin_by_plugin_id(
#         self,
#         plugin_id: str,
#         force_unload: bool = False,
#         timeout: None | int = 5,
#     ) -> None:
#         """
#         Unloads a plugin identified by its `plugin_id`, stopping its execution if
#         necessary, and removing it from the internal plugin registry. The function
#         ensures that the plugin is stopped either gracefully or forcibly based on the
#         provided arguments. A timeout is used to wait for the plugin to stop, after
#         which it will be forcibly stopped if specified before being unloaded.
#
#         Args:
#             plugin_id: The unique identifier of the plugin to be unloaded.
#             force_unload: Whether to forcibly unload the plugin if it fails to stop
#                 within the timeout period. Default is False.
#             timeout: The maximum duration in seconds to wait for the plugin to stop
#                 gracefully. If set to None, it will wait indefinitely. Default is 5
#                 seconds.
#
#         Returns:
#             None
#
#         Raises:
#             InternalPluginStopError: If the plugin fails to stop and force_unload is set
#                 to False due to internal errors.
#             PluginStopTimeoutError: If the plugin fails to stop within the specified
#                 timeout, and force_unload is set to False.
#         """
#         # This call will implicitly do a check to see if the plugin id is valid or not
#         # so we do not need to check it again.
#         plugin = self.get_plugin_by_plugin_id(plugin_id)
#
#         if plugin.status.state == PluginState.RUNNING:
#             try:
#                 await plugin.stop_plugin()
#             except BaseFrameworkException:
#                 if not force_unload:
#                     raise
#             except Exception as exc:
#                 if not force_unload:
#                     raise InternalPluginStopError(
#                         plugin_str=str(plugin),
#                         internal_error_message=str(exc),
#                     ) from exc
#
#             # Ensure that the stop plugin event has been set before proceeding to wait
#             # on the timeout.
#             await plugin.stop_plugin_event.wait()
#             if timeout is None:
#                 while plugin.status.state == PluginState.RUNNING:
#                     await asyncio.sleep(1)
#             else:
#                 # Every second check if the plugin has stopped and break early if it
#                 # has.
#                 for _ in range(timeout):
#                     if plugin.status.state != PluginState.RUNNING:
#                         break
#                     await asyncio.sleep(1)
#
#             # Check the state after the timeout and determine if we forcefully need to
#             # cancel the plugin.
#             if plugin.status.state != PluginState.STOPPED:
#                 if not force_unload:
#                     raise PluginStopTimeoutError(plugin_str=str(plugin))
#                 else:
#                     self.plugins_service_logger.warning(
#                         f"Forcing plugin cancellation for plugin {plugin} because its "
#                         f"timeout exceeded the specified duration: {timeout} second(s).",
#                     )
#                     await plugin.cancel_plugin()
#
#         del self._plugins[plugin_id]
#         self.plugins_service_logger.info(f"Unloaded plugin: {plugin}")
#         self.plugins_service_logger.debug(f"Unloaded plugin: {plugin!r}")
#
#     async def reload_plugin_by_plugin_id(
#         self,
#         plugin_id: str,
#         ignore_enabled_plugin_flag: bool = False,
#     ) -> BasePlugin | None:
#         """
#         Reloads a plugin by its plugin ID. This operation consists of unloading the
#         plugin currently loaded and reloading it from the plugin project folder.
#
#         Args:
#             plugin_id: The unique identifier of the plugin to be reloaded.
#             ignore_enabled_plugin_flag: A flag indicating whether to ignore the
#                 enabled plugin status during the reloading process. Defaults to False.
#
#         Returns:
#             BasePlugin: The reloaded plugin instance if successful, or None if the
#                 plugin is disabled and the enabled check is not overridden.
#
#         Raises:
#             PluginNotFoundError: If the plugin ID is not found in the service.
#             InternalPluginStopError: If the plugin fails to stop and force_unload is set
#                 to False due to internal errors.
#             PluginStopTimeoutError: If the plugin fails to stop within the specified
#                 timeout, and force_unload is set to False.
#             PluginProjectManifestFileNotFoundError: If the plugin project manifest
#                 file, `plugin_project_manifest.json`, is missing.
#             InvalidPluginProjectManifestFileJSONError: If the manifest file,
#                 `plugin_project_manifest.json`, contains invalid JSON.
#             InvalidPluginProjectManifestFileSchemaError: If the manifest file
#                 `plugin_project_manifest.json` doesn't follow the expected schema.
#             PluginProjectPluginFileNotFoundError: If the file specified in the plugin
#                 manifest, `plugin_project_manifest.json`, cannot be found.
#             PluginProjectSymbolNotFoundError: If the symbol specified in the plugin
#                 manifest, `plugin_project_manifest.json`, is not found in the specified
#                 file.
#             PluginProjectInterfaceError: If the plugin class does not correctly inherit
#                 from the [`BasePlugin`][consortium.framework.plugins.base_plugin.BasePlugin]
#                 class.
#             IncompatiblePluginFrameworkVersionError: If the plugin is incompatible with
#                 the current framework version.
#             InternalPluginProjectError: If an unhandled exception is raised within the
#                 plugin while initializing the plugin.
#             PluginAlreadyRegisteredError: If a plugin with the same `plugin_id` is
#                 already registered.
#             DuplicatePluginLabelError: If a plugin with the same `label` attribute is
#                 already registered.
#             ThirdPartyDependencyNotFoundError: If the plugin requires a third party
#                 dependency that is not installed in the framework.
#             IncompatibleThirdPartyDependencyVersionError: If the plugin requires a
#                 third party dependency that has a version not compatible with the one
#                 installed in the framework.
#             PluginDependencyNotFoundError: If the plugin requires another plugin that
#                 is not installed in the framework.
#             IncompatiblePluginDependencyVersionError: If the plugin requires another
#                 plugin to be installed that has a version not compatible with the one
#                 installed in the framework.
#             PluginDependencyNotRunningError: If the plugin requires another plugin that
#                 is installed and of the appropriate version but is not currently
#                 running.
#             PluginAlreadyRunningError: If the plugin is already running.
#             PluginStartError: If the plugin failed to start for any reason.
#             InternalPluginStartError: If an unhandled exception is raised within the
#                 plugin while starting the plugin.
#         """
#         plugin = self.get_plugin_by_plugin_id(plugin_id)
#         plugin_project_folder = plugin.plugin_project_folder
#         await self.unload_plugin_by_plugin_id(plugin_id)
#         plugin = await self.load_plugin_from_plugin_project_folder(
#             plugin_project_folder=plugin_project_folder,
#             ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
#         )
#         self.plugins_service_logger.info(f"Reloaded plugin: {plugin}")
#         self.plugins_service_logger.debug(f"Reloaded plugin: {plugin!r}")
#         return plugin
#
#     async def load_framework_plugins(
#         self,
#         ignore_enabled_plugin_flag: bool = False,
#     ) -> None:
#         self.plugins_service_logger.info(f"Loading framework plugins...")
#
#         # Recursively search through the plugins directory to find all plugin project
#         # folders and register their plugins.
#         plugin_project_folder_paths = []
#         for path in CONSORTIUM_PLUGINS_DIRECTORY_PATH.rglob("*"):
#             if path.name != "plugin_project_manifest.json":
#                 continue
#             plugin_project_folder_paths.append(path.parent)
#         for plugin_project_folder_path in plugin_project_folder_paths:
#             try:
#                 self.register_plugin_from_plugin_project_folder(
#                     plugin_project_folder=plugin_project_folder_path,
#                     ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
#                 )
#             except PluginsFrameworkError as exc:
#                 self.plugins_service_logger.error(
#                     f"Failed to load plugin from plugin project folder "
#                     f"'{plugin_project_folder_path}': {exc}",
#                 )
#
#         print(self.get_all_plugins())
#
#         # # def _remove_plugin_from_plugin_dependency_graph(
#         # #     plugin: str, plugin_dependency_graph: dict[str, set[str]]
#         # # ) -> None:
#         # #     plugins_to_remove = {plugin}
#         # #     removed_plugins = set()
#         # #
#         # #     while plugins_to_remove:
#         # #         plugin_to_remove = plugins_to_remove.pop()
#         # #         if plugin_to_remove in plugin_dependency_graph:
#         # #             del plugin_dependency_graph[plugin_to_remove]
#         # #             removed_plugins.add(plugin_to_remove)
#         # #             # Find plugins that depend on the removed plugin
#         # #             for dependent_plugin, dependencies in list(plugin_dependency_graph.items()): # Iterate over a copy to allow deletion
#         # #                 if plugin_to_remove in dependencies:
#         # #                     plugins_to_remove.add(dependent_plugin)
#         # #
#         # #
#         # # class FakePlugin:
#         # #     def __init__(self, fake_plugin_id, label=None, dependencies=None):
#         # #         self.plugin_id = fake_plugin_id
#         # #         self.plugin_project_folder = None
#         # #         self.label = label
#         # #         self.plugin_dependencies = [dependencies, None] if dependencies else []
#         # #         self.autostart = False
#         # #         self.status = PluginState.STOPPED
#         # #
#         # # fakes = [
#         # #     FakePlugin("id_a", label="a", dependencies=["a", "b", "c"]),
#         # #     FakePlugin("id_b", label="b", dependencies=["d"]),
#         # #     FakePlugin("id_c", label="c", dependencies=["d", "e"]),
#         # #     FakePlugin("id_d", label="d"),
#         # # ]
#         # # for fake in fakes:
#         # #     self._plugins[fake.plugin_id] = fake
#         #
#         # # Construct start order for plugins based on their dependencies, referencing
#         # # each plugin by its plugin_id. Each plugin that is to be started is present in
#         # # this dictionary and has values that are sets of plugin_ids that are required
#         # # to be started before it.
#         # plugins_to_start = {}
#         # label_to_plugin_id_map = {}
#         # unloadable_plugins = set()
#         # # Construct a mapping of plugin labels to plugin ids. This is used to resolve
#         # # plugin dependencies that are specified by label instead of plugin id.
#         # for plugin_id, plugin in self._plugins.items():
#         #     if plugin.label and plugin.label not in label_to_plugin_id_map:
#         #         label_to_plugin_id_map[plugin.label] = plugin_id
#         #
#         # def _recursively_remove_plugin_from_plugin_dependency_graph(
#         #     plugin: str,
#         #     plugin_dependency_graph: dict[str, set[str]],
#         # ) -> set[str]:
#         #     plugins_to_remove = {plugin}
#         #     removed_plugins = set()
#         #
#         #     while plugins_to_remove:
#         #         plugin_to_remove = plugins_to_remove.pop()
#         #         if plugin_to_remove in plugin_dependency_graph:
#         #             del plugin_dependency_graph[plugin_to_remove]
#         #             removed_plugins.add(plugin_to_remove)
#         #             # Find plugins that depend on the removed plugin
#         #             for dependent_plugin, dependencies in list(
#         #                 plugin_dependency_graph.items(),
#         #             ):  # Iterate over a copy to allow deletion
#         #                 if plugin_to_remove in dependencies:
#         #                     plugins_to_remove.add(dependent_plugin)
#         #
#         #     return removed_plugins
#         #
#         # def _remove_plugins_with_missing_dependencies(
#         #     plugin_dependency_graph: dict[str, set[str]],
#         # ) -> None:
#         #     plugins_to_remove = set()
#         #
#         #     for plugin, dependencies in plugin_dependency_graph.items():
#         #         for dependency in dependencies:
#         #             if dependency not in plugin_dependency_graph:
#         #                 plugins_to_remove.add(plugin)
#         #
#         #     for plugin in plugins_to_remove:
#         #         removed_plugins = (
#         #             _recursively_remove_plugin_from_plugin_dependency_graph(
#         #                 plugin,
#         #                 plugin_dependency_graph,
#         #             )
#         #         )
#         #         if removed_plugins:
#         #             print(
#         #                 f"The plugin dependency '{plugin}' that was not installed "
#         #                 f"either directly or indirectly caused the following plugins to be "
#         #                 f"removed: {", ".join([f"'{plugin}'" for plugin in removed_plugins])}",
#         #             )
#         #
#         # def _remove_plugins_with_circular_dependencies(
#         #     plugin_dependency_graph: dict[str, set[str]],
#         # ) -> None:
#         #     visited_nodes = set()
#         #     dependency_path = []  # Holds our current recursion path through the graph.
#         #     circular_dependencies = []
#         #
#         #     def _visit_node(node: str) -> None:
#         #         dependency_path.append(node)
#         #         # Algorithm has arrived at a leaf node.
#         #         if not plugin_dependency_graph[node]:
#         #             dependency_path.pop()
#         #             visited_nodes.add(node)
#         #             return
#         #         # There are more nodes to explore, so start checking them.
#         #         for neighbor in plugin_dependency_graph[node]:
#         #             # Skip fully explored nodes.
#         #             if neighbor in visited_nodes:
#         #                 continue
#         #             # Algorithm has found a circular dependency.
#         #             if neighbor in dependency_path:
#         #                 circular_dependencies.append(
#         #                     dependency_path[dependency_path.index(neighbor) :]
#         #                     + [neighbor],
#         #                 )
#         #                 continue
#         #             _visit_node(neighbor)
#         #         # After visiting all our neighbor nodes this current node is marked as fully
#         #         # explored. We are about to return up one recursion level so we need to remove
#         #         # the last node from the path as well.
#         #         dependency_path.pop()
#         #         visited_nodes.add(node)
#         #
#         #     for plugin in plugin_dependency_graph:
#         #         if plugin in visited_nodes:  # Skip fully explored nodes.
#         #             continue
#         #         _visit_node(plugin)
#         #
#         #     # Remove plugins with circular dependencies.
#         #     for cycle in circular_dependencies:
#         #         unique_plugins = set(list(cycle))
#         #         removed_plugins = []
#         #         for plugin in unique_plugins:
#         #             removed_plugins += (
#         #                 _recursively_remove_plugin_from_plugin_dependency_graph(
#         #                     plugin,
#         #                     plugin_dependency_graph,
#         #                 )
#         #             )
#         #         if removed_plugins:
#         #             print(
#         #                 f"The detected circular plugin dependency "
#         #                 f"{" -> ".join([f"'{plugin}'" for plugin in cycle])} either directly "
#         #                 f"or indirectly caused the following plugins to be removed: "
#         #                 f"{", ".join([f"'{plugin}'" for plugin in removed_plugins])}",
#         #             )
#
#         # # Construct the mapping of plugin ids to plugin dependencies. This is used to
#         # # determine the order in which plugins should be started.
#         # for plugin_id, plugin in self._plugins.items():
#         #     plugins_to_start[plugin_id] = set()
#         #     for dependency, dependency_specifier_set in plugin.plugin_dependencies:
#         #         if dependency in label_to_plugin_id_map:
#         #             dependent_plugin = self.get_plugin_by_plugin_id(
#         #                 plugin_id=label_to_plugin_id_map[dependency]
#         #             )
#         #             if dependency_specifier_set and dependent_plugin.version in dependency_specifier_set:
#         #                 plugins_to_start[plugin_id].add(
#         #                     label_to_plugin_id_map[dependency],
#         #                 )
#         #             else:
#         #                 # Plugin requires a plugin dependency that is installed but of
#         #                 # an incompatible version.
#         #                 self.plugins_service_logger.warning(
#         #                     f"Plugin '{plugin}' requires plugin dependency "
#         #                     f"'{dependency}' with version specifier "
#         #                     f"'{dependency_specifier_set}' that is not installed in "
#         #                     f"the framework. This plugin will not be started but "
#         #                     f"will remain registered."
#         #                 )
#         #                 unloadable_plugins.add(plugin_id)
#         #                 break
#         #         # Plugin requires a plugin dependency that is not installed.
#         #         else:
#         #             self.plugins_service_logger.warning(
#         #                 f"Plugin '{plugin}' requires plugin dependency '{dependency}' "
#         #                 f"that is not installed in the framework. This plugin will not "
#         #                 f"be started but will remain registered."
#         #             )
#         #             unloadable_plugins.add(plugin_id)
#         #             break
#         # # Check for circular dependencies in the plugins to start.
#         # for plugin_id, dependencies in plugins_to_start.items():
#         #     for dependency in dependencies:
#         #         # Plugin is dependent on itself.
#         #         if dependency == plugin_id:
#         #             plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
#         #             self.plugins_service_logger.warning(
#         #                 f"Plugin '{plugin}' has a circular dependency with itself. "
#         #                 f"This plugin will not be started but will remain registered."
#         #             )
#         #             unloadable_plugins.add(plugin_id)
#         #             break
#         #         # Plugin is dependent on another plugin that is dependent on itself in
#         #         # turn.
#         #         if plugin_id in plugins_to_start[dependency]:
#         #             plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
#         #             dependent_plugin = self.get_plugin_by_plugin_id(plugin_id=dependency)
#         #             self.plugins_service_logger.warning(
#         #                 f"Plugin '{plugin}' has a circular dependency with plugin "
#         #                 f"'{dependent_plugin}'. These plugins will not be started but "
#         #                 f"will remain registered."
#         #             )
#         #             unloadable_plugins.add(plugin_id)
#         #             unloadable_plugins.add(dependency)
#         #             break
#
#         # print("Plugins to start:")
#         # for plugin_id, dependencies in plugins_to_start.items():
#         #     print(f"{plugin_id}: {dependencies}")
#         # print("Unloadable plugins:", unloadable_plugins)
#
#         exit()
#
#         # load_plugins_tasks = []
#         #
#         # for plugin_project_folder_path in plugin_project_folder_paths:
#         #     load_plugins_tasks.append(
#         #         asyncio.create_task(
#         #             asyncio.sleep(1)
#         #         ),
#         #     )
#         #
#         # number_of_loaded_plugins = 0
#         # load_plugins_tasks_results = await asyncio.gather(
#         #     *load_plugins_tasks,
#         #     return_exceptions=True,
#         # )
#         # for result in load_plugins_tasks_results:
#         #     if isinstance(result, (PluginLoadingError, PluginsFrameworkError)):
#         #         self.plugins_service_logger.error(result)
#         #     elif isinstance(result, Exception):
#         #         self.plugins_service_logger.error(
#         #             "Fatal error occurred while loading plugin.",
#         #         )
#         #         self.plugins_service_logger.opt(colors=True, raw=True).error(
#         #             "<bold><red>{}</></>",
#         #             "".join(traceback.format_exception(result)),
#         #         )
#         #     elif result is None:
#         #         continue
#         #     else:
#         #         number_of_loaded_plugins += 1
#         #
#         # self.plugins_service_logger.info(
#         #     f"Loaded framework plugins ({number_of_loaded_plugins} plugin(s) "
#         #     f"loaded).",
#         # )
#
#     async def reload_framework_plugins(
#         self,
#         force_reload: bool = False,
#         timeout: None | int = 5,
#         ignore_enabled_plugin_flag: bool = False,
#     ) -> None:
#         self.plugins_service_logger.info(f"Reloading framework plugins...")
#
#         unload_plugin_tasks = []
#         load_plugin_tasks = []
#
#         for plugin_id in self._plugins:
#             unload_plugin_tasks.append(
#                 asyncio.create_task(
#                     self.unload_plugin_by_plugin_id(
#                         plugin_id=plugin_id,
#                         force_unload=force_reload,
#                         timeout=timeout,
#                     ),
#                 ),
#             )
#
#         unload_plugin_tasks_results = await asyncio.gather(
#             *unload_plugin_tasks,
#             return_exceptions=True,
#         )
#         for result in unload_plugin_tasks_results:
#             # A successful plugin unload will log the plugin load message. We only want
#             # to log errors here.
#             if isinstance(result, PluginUnloadingError):
#                 self.plugins_service_logger.error(result)
#
#         # Recursively search through the framework's plugin project folders directory
#         # to find all plugin project folders. If a plugin project folder is found that
#         # is not already loaded (it failed to unload), load it.
#         for plugin_project_folder in CONSORTIUM_PLUGINS_DIRECTORY_PATH.rglob("*"):
#             if plugin_project_folder.name != "plugin_project_manifest.json":
#                 continue
#             plugin_loaded = False
#             for plugin in self.get_all_plugins():
#                 if plugin.plugin_project_folder.parent == plugin_project_folder.parent:
#                     plugin_loaded = True
#                     break
#             if not plugin_loaded:
#                 load_plugin_tasks.append(
#                     asyncio.create_task(
#                         self.load_plugin_from_plugin_project_folder(
#                             plugin_project_folder=plugin_project_folder.parent,
#                             ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
#                         ),
#                     ),
#                 )
#         load_plugin_tasks_results = await asyncio.gather(
#             *load_plugin_tasks,
#             return_exceptions=True,
#         )
#         for result in load_plugin_tasks_results:
#             # A successful plugin load will log the plugin load message. We only want to
#             # log errors here.
#             if isinstance(result, PluginLoadingError):
#                 self.plugins_service_logger.error(result)
#
#         self.plugins_service_logger.info(
#             f"Reloaded framework plugins.",
#         )
#
#     async def unload_framework_plugins(
#         self,
#         force_unload: bool = False,
#         timeout: None | int = 5,
#     ) -> None:
#         self.plugins_service_logger.info(f"Unloading framework plugins...")
#
#         number_of_unloaded_plugins = 0
#         unload_plugin_tasks = []
#         for plugin in self.get_all_plugins():
#             if plugin.plugin_project_folder.parent == CONSORTIUM_PLUGINS_DIRECTORY_PATH:
#                 unload_plugin_tasks.append(
#                     asyncio.create_task(
#                         self.unload_plugin_by_plugin_id(
#                             plugin_id=str(plugin.plugin_id),
#                             force_unload=force_unload,
#                             timeout=timeout,
#                         ),
#                     ),
#                 )
#         unload_plugin_tasks_results = await asyncio.gather(
#             *unload_plugin_tasks,
#             return_exceptions=True,
#         )
#         for result in unload_plugin_tasks_results:
#             # A successful plugin unload will log the plugin load message. We only want
#             # to log errors here.
#             if isinstance(result, PluginUnloadingError):
#                 self.plugins_service_logger.error(result)
#             else:
#                 number_of_unloaded_plugins += 1
#
#         self.plugins_service_logger.info(
#             f"Unloaded framework plugins ({number_of_unloaded_plugins} plugin(s) "
#             f"unloaded).",
#         )
#
#     async def start_plugin_by_plugin_id(
#         self,
#         plugin_id: str,
#         blocking: bool = False,
#     ) -> None:
#         """
#         Starts a plugin by its plugin id. The plugin must be registered to the
#         service.
#
#         Args:
#             plugin_id (str): The plugin id to start.
#             blocking (bool): If True, the method will block and wait until the plugin is
#                 stopped. If False, the method will return immediately after starting
#                 the plugin.
#
#         Returns:
#             None
#
#         Raises:
#             PluginNotFoundError: If the plugin id is not found in the service.
#             IncompatibleThirdPartyDependencyVersionError: If the plugin requires a
#                 third party dependency that has a version not compatible with the one
#                 installed in the framework.
#             ThirdPartyDependencyNotFoundError: If the plugin requires a third party
#                 dependency that is not installed in the framework.
#             IncompatiblePluginDependencyVersionError: If the plugin requires another
#                 plugin to be installed that has a version not compatible with the one
#                 installed in the framework.
#             PluginDependencyNotFoundError: If the plugin requires another plugin that
#                 is not installed in the framework.
#             PluginDependencyNotRunningError: If the plugin requires another plugin that
#                 is installed and of the appropriate version but is not currently
#                 running.
#             PluginAlreadyRunningError: If the plugin is already running.
#             PluginStartError: If the plugin failed to start for any reason.
#         """
#         plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
#         await plugin.start_plugin()
#
#         if not blocking:
#             return
#         while plugin.status.state in (PluginState.INITIALIZED, PluginState.STARTED):
#             await asyncio.sleep(0.1)
#
#     async def stop_plugin_by_plugin_id(
#         self,
#         plugin_id: str,
#         blocking: bool = False,
#     ) -> None:
#         """
#         Stops a plugin by its plugin id. The plugin must be registered to the
#         service.
#
#         Args:
#             plugin_id (str): The plugin id to stop.
#             blocking (bool): If True, the method will block and wait until the plugin is
#                 stopped. If False, the method will return immediately after stopping
#                 the plugin.
#
#         Returns:
#             None
#
#         Raises:
#             PluginNotFoundError: If the plugin id is not found in the service.
#             PluginStopError: If the plugin failed to stop for any reason.
#             PluginNotRunningError: If the plugin is not running.
#         """
#         plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
#         await plugin.stop_plugin()
#
#         if not blocking:
#             return
#         while plugin.status.state == PluginState.RUNNING:
#             await asyncio.sleep(0.1)
#
#     async def restart_plugin_by_plugin_id(
#         self,
#         plugin_id: str,
#         blocking: bool = False,
#     ) -> None:
#         """
#         Convenience method to restart a plugin by its plugin id. The plugin must be
#         registered to the service. This method will first stop the plugin and then
#         start it again.
#
#         Args:
#             plugin_id (str): The plugin id to restart.
#             blocking (bool): If True, the method will block and wait until the plugin is
#                 stopped and then started again. If False, the method will return
#                 immediately after attempting to restart the plugin.
#
#         Returns:
#             None
#
#         Raises:
#             PluginNotFoundError: If the plugin id is not found in the service.
#             IncompatibleThirdPartyDependencyVersionError: If the plugin requires a
#                 third party dependency that has a version not compatible with the one
#                 installed in the framework.
#             ThirdPartyDependencyNotFoundError: If the plugin requires a third party
#                 dependency that is not installed in the framework.
#             IncompatiblePluginDependencyVersionError: If the plugin requires another
#                 plugin to be installed that has a version not compatible with the one
#                 installed in the framework.
#             PluginDependencyNotFoundError: If the plugin requires another plugin that
#                 is not installed in the framework.
#             PluginDependencyNotRunningError: If the plugin requires another plugin that
#                 is installed and of the appropriate version but is not currently
#                 running.
#             PluginAlreadyRunningError: If the plugin is already running.
#             PluginStartError: If the plugin failed to start for any reason.
#             PluginStopError: If the plugin failed to stop for any reason.
#             PluginNotRunningError: If the plugin is not running.
#         """
#
#         async def _restart_plugin_task():
#             # Block and wait for the plugin to stop before immediately starting again.
#             await self.stop_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)
#             await self.start_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)
#
#         if blocking:
#             await _restart_plugin_task()
#         else:
#             task = asyncio.create_task(_restart_plugin_task())
#             self._restart_plugin_tasks.add(task)
#             task.add_done_callback(
#                 lambda finished_task: self._restart_plugin_tasks.remove(finished_task),
#             )
#
#     def get_plugin_by_plugin_id(self, plugin_id: str) -> BasePlugin:
#         """
#         Returns a plugin object by its plugin id. The plugin must be registered to the
#         service.
#
#         Args:
#             plugin_id (str): The plugin id to search for.
#
#         Returns:
#             BasePlugin: The plugin object if found.
#
#         Raises:
#             PluginNotFoundError: If the plugin id is not found in the service.
#         """
#         try:
#             plugin = self._plugins[plugin_id]
#         except KeyError:
#             raise PluginNotFoundError(plugin_id=plugin_id)
#
#         self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
#         return plugin
#
#     def get_plugins_by_label(self, label: str) -> list[BasePlugin]:
#         """
#         Returns all plugins that have the provided label. Multiple plugins can have
#         the same label. The plugins must be registered to the service.
#
#         Args:
#             label (str): The label to search for.
#
#         Returns:
#             BasePlugin: The plugin object if found.
#
#         Raises:
#             PluginLabelNotFoundError: If the plugin label is not found in the service.
#         """
#         for plugin in self._plugins.values():
#             if plugin.label == label:
#                 self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
#                 return plugin
#
#         raise PluginLabelNotFoundError(plugin_id=label)
#
#     def get_all_plugins(self) -> list[BasePlugin]:
#         """
#         Returns a list of all plugins registered to the service.
#
#         Returns:
#             list[BasePlugin]: A list of all plugins registered to the service.
#         """
#         self.plugins_service_logger.debug(
#             f"Retrieved all plugins ({len(self._plugins)} plugin(s) retrieved).",
#         )
#         return list(self._plugins.values())
