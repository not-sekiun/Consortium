# # import asyncio
# #
# # from consortium.framework.plugins import BasePlugin
# #
# #
# # class MyAwesomePlugin(BasePlugin):
# #     label = "My Awesome Plugin"
# #     name = "My Awesome Plugin"
# #     description = "This is my awesome plugin."
# #     version = "1.0.0"
# #     compatible_framework_version = ">=1.0.0"
# #     authors = {"John Doe", "Jane Smith"}
# #     autostart = True
# #     plugin_dependencies = {("DependencyPlugin", ">=1.0.0")}
# #
# #     async def on_started(self) -> None:
# #         print(f"{self.name} has started.")
# #
# #     async def on_running(self) -> None:
# #         while not self.stop_event.is_set():
# #             print(self.server_services)
# #             await asyncio.sleep(1)
# #
# #     async def on_completed(self) -> None:
# #         print(f"{self.name} has completed its task.")
# #
# #     async def on_stopped(self) -> None:
# #         print(f"{self.name} has been stopped.")
# #
# #     async def on_cancelled(self) -> None:
# #         print(f"{self.name} has been cancelled.")
# #
# #     async def on_errored(self, exc: Exception) -> None:
# #         print(f"{self.name} encountered an error: {exc}")
# #
# #
# # async def main():
# #     plugin = MyAwesomePlugin()
# #     try:
# #         await plugin.start()
# #         await asyncio.sleep(3)  # Simulate some running time
# #         print(plugin.to_json())
# #         await plugin.stop()
# #         await asyncio.sleep(1)
# #         print(plugin.to_json())
# #     except Exception as exc:
# #         print(f"Exception occurred: {exc}")
# #         print(plugin.to_json())
# #
# #
# # if __name__ == "__main__":
# #     asyncio.run(main())
#
#
# import asyncio
# import graphlib
# import importlib.metadata
# import json
# import pathlib
# import tomllib
#
# import jsonschema
# from loguru import logger
# from packaging import requirements, version
#
# from consortium.framework.plugins._plugin_status import PluginState
# from consortium.framework.plugins.base_plugin import BasePlugin
# from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
#     BaseFrameworkException,
# )
# from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
#     PluginsFrameworkError,
# )
# from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
#     DuplicatePluginLabelError,
#     IncompatiblePluginFrameworkVersionError,
#     IncompatibleThirdPartyDependencyVersionError,
#     InternalPluginProjectError,
#     InternalPluginStartError,
#     InternalPluginStopError,
#     InvalidPluginProjectManifestFileJSONError,
#     InvalidPluginProjectManifestFileSchemaError,
#     InvalidPluginProjectPyProjectFileDependencyError,
#     InvalidPluginProjectPyProjectFileTOMLError,
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
#     ThirdPartyDependencyNotFoundError,
# )
# from consortium.server.server_config import (
#     CONSORTIUM_HOME_DIRECTORY_PATH,
#     CONSORTIUM_PLUGINS_DIRECTORY_PATH,
#     SERVER_RELEASE,
# )
#
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
#         manifest_file_path = plugin_project_folder / "manifest.json"
#         manifest_json_schema = {
#             "type": "object",
#             "properties": {
#                 "entry_point": {"type": "string"},
#                 "enabled": {"type": "boolean"},
#             },
#             "required": ["entry_point", "enabled"],
#             "additionalProperties": False,
#         }
#
#         # Check if the manifest file exists and follows the correct JSON schema.
#         try:
#             with manifest_file_path.open(
#                 "r",
#             ) as plugin_project_manifest_file:
#                 manifest_json = json.load(plugin_project_manifest_file)
#                 jsonschema.validate(
#                     manifest_json,
#                     manifest_json_schema,
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
#         if not manifest_json["enabled"] and not ignore_enabled_plugin_flag:
#             self.plugins_service_logger.info(
#                 "Skipped loading plugin from '{}' because it was disabled.",
#                 str(plugin_project_folder),
#             )
#             return None
#
#         # Check for a valid plugin project folder structure as specified by the
#         # manifest file.
#         plugin_module, plugin_symbol = manifest_json["entry_point"].split(":", 1)
#         plugin_file = pathlib.Path(plugin_project_folder, *plugin_module.split("."))
#         # Append .py suffix
#         plugin_file = plugin_file.parent / (plugin_file.name + ".py")
#
#         # Check if the file exists first, don't try-catch for `ImportError` because
#         # these can be raised by missing third party dependencies instead of a missing
#         # plugin file.
#         if not plugin_file.exists():
#             raise PluginProjectPluginFileNotFoundError(
#                 plugin_file=str(plugin_file),
#                 plugin_project_folder=str(plugin_project_folder),
#             )
#
#         # Check for any third party dependencies declared by the plugin. If they exist
#         # check that they are importable and of the correct version before finally
#         # loading the entire plugin in.
#         pyproject_toml = plugin_project_folder / "pyproject.toml"
#         if pyproject_toml.exists():
#             try:
#                 with pyproject_toml.open("r") as pyproject_toml_file:
#                     pyproject_data = tomllib.loads(pyproject_toml_file.read())
#             except tomllib.TOMLDecodeError:
#                 raise InvalidPluginProjectPyProjectFileTOMLError(
#                     plugin_project_folder=str(plugin_project_folder),
#                 )
#             dependency_entries = pyproject_data.get("project", {}).get(
#                 "dependencies",
#                 [],
#             )
#         else:
#             dependency_entries = []
#
#         dependencies = set()
#         for entry in dependency_entries:
#             try:
#                 # Check dependency entry is valid
#                 dependency = requirements.Requirement(entry)
#                 # Check dependency exists and is a compatible version without importing
#                 # the module.
#                 dependency_version = importlib.metadata.version(dependency.name)
#                 if dependency_version not in dependency.specifier:
#                     raise IncompatibleThirdPartyDependencyVersionError(
#                         plugin_project_folder=str(plugin_project_folder),
#                         third_party_dependency_name=dependency.name,
#                         required_version=str(dependency.specifier),
#                         installed_version=dependency_version,
#                     )
#                 dependencies.add(dependency)
#             except importlib.metadata.PackageNotFoundError:
#                 raise ThirdPartyDependencyNotFoundError(
#                     plugin_project_folder=str(plugin_project_folder),
#                     third_party_dependency_name=dependency.name,
#                 )
#             except requirements.InvalidRequirement:
#                 raise InvalidPluginProjectPyProjectFileDependencyError(
#                     plugin_project_folder=str(plugin_project_folder),
#                     invalid_dependency_entry=entry,
#                 )
#
#         # Check for valid symbol names in the required plugin project file.
#         plugin_module_path = ".".join(
#             plugin_file.relative_to(
#                 CONSORTIUM_HOME_DIRECTORY_PATH,
#             ).parts,
#         )[: -len(".py")]
#
#         try:
#             # Any import errors that arise should not be from third-party dependencies
#             # because we checked for that earlier
#             plugin_module = importlib.import_module(plugin_module_path)
#             plugin_class = getattr(
#                 plugin_module,
#                 plugin_symbol,
#             )
#             plugin_class.third_party_dependencies = dependencies
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
#         # Check the plugin's framework version compatibility if not specified, assume
#         # it is compatible.
#         if (
#             plugin_object.compatible_framework_version
#             and version.Version(SERVER_RELEASE.version)
#             not in plugin_object.compatible_framework_version
#         ):
#             raise IncompatiblePluginFrameworkVersionError(
#                 plugin_str=str(plugin_object),
#                 required_version=str(
#                     plugin_object.compatible_framework_version,
#                 ),
#                 current_version=SERVER_RELEASE.version,
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
#         if str(plugin.plugin_id) in self._plugins:
#             raise PluginAlreadyRegisteredError(
#                 plugin_str=str(plugin),
#                 plugin_id=str(plugin.plugin_id),
#             )
#
#         if plugin.label and plugin.label in [
#             plugin.label for plugin in self._plugins.values() if plugin.label
#         ]:
#             raise DuplicatePluginLabelError(
#                 plugin_str=str(plugin),
#                 label=plugin.label,
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
#                 await plugin.start()
#             except BaseFrameworkException:
#                 raise
#             except Exception as exc:
#                 raise InternalPluginStartError(
#                     plugin_str=str(plugin),
#                     internal_error_message=str(exc),
#                 ) from exc
#
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
#         # This call will implicitly do a check to see if the plugin id is valid or not
#         # so we do not need to check it again.
#         plugin = self.get_plugin_by_plugin_id(plugin_id)
#
#         if plugin.status.state == PluginState.RUNNING:
#             try:
#                 await plugin.stop()
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
#             await plugin.stop_event.wait()
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
#                     await plugin.cancel()
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
#             if path.name != "manifest.json":
#                 continue
#             plugin_project_folder_paths.append(path.parent)
#         plugins_to_load = {}
#         for plugin_project_folder_path in plugin_project_folder_paths:
#             try:
#                 plugin_id = self.get_plugin_from_plugin_project_folder(
#                     plugin_project_folder=plugin_project_folder_path,
#                     ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
#                 )
#                 if plugin_id:
#                     plugins_to_load[plugin_id.label] = plugin_id
#             except PluginsFrameworkError as exc:
#                 self.plugins_service_logger.error(
#                     f"Failed to load plugin from plugin project folder "
#                     f"'{plugin_project_folder_path}': {exc}",
#                 )
#
#         # Construct DAG to resolve start order. While constructing, check plugin
#         # dependency versions to make sure all plugins are of compatible versions. The
#         # nodes of the DAG are the labels of the plugins being loaded.
#         dependency_graph = {}
#         for label, plugin in plugins_to_load.items():
#             # Check if all plugin dependencies are available and of compatible
#             # versions. If not skip loading that plugin entirely. But continue to try
#             # loading other plugins
#             load_plugin = True
#             for dependency in plugin.plugin_dependencies:
#                 if dependency.name not in plugins_to_load:
#                     self.plugins_service_logger.error(
#                         f"Plugin '{plugin}' requires plugin "
#                         f"'{dependency.name}' to be installed, but it was not found. "
#                         f"Skipping loading of plugin '{plugin}'.",
#                     )
#                     load_plugin = False
#                     break
#                 if plugins_to_load[dependency.name].version not in dependency.specifier:
#                     self.plugins_service_logger.error(
#                         f"Plugin '{plugin}' requires plugin "
#                         f"'{dependency.name}' to be of version "
#                         f"'{dependency.specifier}', but found version "
#                         f"'{plugins_to_load[dependency.name].version}'. Skipping "
#                         f"loading of plugin '{plugin}'.",
#                     )
#                     load_plugin = False
#                     break
#             if not load_plugin:
#                 continue
#
#             # Plugin has all dependencies available and of compatible versions, add to
#             # the dependency graph.
#             dependency_graph[label] = set()
#             for dependency in plugin.plugin_dependencies:
#                 dependency_graph[label].add(dependency.name)
#
#         # Check for cyclic dependencies in the dependency graph before proceeding to
#         # load plugins. Cyclic dependencies abort the entire load process.
#         topological_sorter = graphlib.TopologicalSorter(dependency_graph)
#         try:
#             order = topological_sorter.static_order()
#         except graphlib.CycleError as exc:
#             circular_dependency_path = " -> ".join(
#                 [f"'{str(plugins_to_load[plugin_id])}'" for plugin_id in exc.args[1]],
#             )
#             self.plugins_service_logger.error(
#                 (
#                     f"Unable to load framework plugins. Detected circular dependencies "
#                     f"in the plugin dependency graph: {circular_dependency_path}. "
#                     f"Either remove the circularly dependent plugins or fix their "
#                     f"dependencies to resolve the issue."
#                 ),
#             )
#             return
#
#         # Register and start each plugin according to the topological sort order
#         # determined.
#         number_of_loaded_plugins = 0
#         for label in order:
#             try:
#                 plugin = plugins_to_load[label]
#                 self.register_plugin(plugin)
#                 if plugin.autostart:
#                     try:
#                         await plugin.start()
#                     except BaseFrameworkException:
#                         raise
#                     except Exception as exc:
#                         raise InternalPluginStartError(
#                             plugin_str=str(plugin),
#                             internal_error_message=str(exc),
#                         ) from exc
#                 number_of_loaded_plugins += 1
#             except PluginsFrameworkError as exc:
#                 self.plugins_service_logger.error(
#                     f"Failed to load plugin '{plugins_to_load[label]}': {exc}",
#                 )
#
#         self.plugins_service_logger.info(
#             f"Loaded framework plugins ({number_of_loaded_plugins} plugin(s) "
#             f"loaded).",
#         )
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
#         plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
#         await plugin.start()
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
#         plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
#         await plugin.stop()
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
#         try:
#             plugin = self._plugins[plugin_id]
#         except KeyError:
#             raise PluginNotFoundError(plugin_id=plugin_id)
#
#         self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
#         return plugin
#
#     def get_plugins_by_label(self, label: str) -> list[BasePlugin]:
#         for plugin in self._plugins.values():
#             if plugin.label == label:
#                 self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
#                 return plugin
#
#         raise PluginLabelNotFoundError(label=label)
#
#     def get_all_plugins(self) -> list[BasePlugin]:
#         self.plugins_service_logger.debug(
#             f"Retrieved all plugins ({len(self._plugins)} plugin(s) retrieved).",
#         )
#         return list(self._plugins.values())
