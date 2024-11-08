import asyncio
import importlib
import json
import traceback
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.framework.plugins.exceptions import PluginsFrameworkError
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    InternalPluginProjectError,
    InternalPluginStopError,
    InvalidPluginProjectManifestFileJSONError,
    InvalidPluginProjectManifestFileSchemaError,
    PluginLoadingError,
    PluginNotFoundError,
    PluginProjectInterfaceError,
    PluginProjectManifestFileNotFoundError,
    PluginProjectPluginFileNotFoundError,
    PluginProjectSymbolNotFoundError,
    PluginStopTimeoutError,
    PluginUnloadError,
)
from consortium.framework.plugins.plugin_status import PluginState
from consortium.server.server_config import (
    CONSORTIUM_HOME_DIRECTORY_PATH,
    CONSORTIUM_PLUGINS_DIRECTORY_PATH,
)


class PluginsService:
    def __init__(self):
        self._plugins = {}
        self.plugins_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.plugins_service_logger.debug("Started Plugins Service")

    def __str__(self):
        return "Plugins Service"

    def __repr__(self):
        return "PluginsService()"

    def get_plugin_from_plugin_project_folder(
        self,
        plugin_project_folder: Path,
        ignore_enabled_plugin_project_flag: bool = False,
    ) -> BasePlugin | None:
        plugin_project_manifest_file_path = (
            plugin_project_folder / "plugin_project_manifest.json"
        )
        plugin_project_manifest_json_schema = {
            "type": "object",
            "properties": {
                "plugin": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string"},
                        "symbol": {"type": "string"},
                    },
                    "required": ["filepath", "symbol"],
                    "additionalProperties": False,
                },
                "enabled": {
                    "type": "boolean",
                },
            },
            "required": ["plugin", "enabled"],
            "additionalProperties": False,
        }

        # Check if manifest file exists and follows the correct json schema.
        try:
            with plugin_project_manifest_file_path.open(
                "r",
            ) as plugin_project_manifest_file:
                plugin_project_manifest_json = json.load(plugin_project_manifest_file)
                jsonschema.validate(
                    plugin_project_manifest_json,
                    plugin_project_manifest_json_schema,
                )
        except FileNotFoundError:
            raise PluginProjectManifestFileNotFoundError
        except json.JSONDecodeError:
            raise InvalidPluginProjectManifestFileJSONError(
                plugin_project_folder=str(plugin_project_folder),
            )
        except jsonschema.ValidationError as exc:
            raise InvalidPluginProjectManifestFileSchemaError(
                plugin_project_folder=str(plugin_project_folder),
                json_schema_error_message=exc.message,
            )

        if (
            not plugin_project_manifest_json["enabled"]
            and not ignore_enabled_plugin_project_flag
        ):
            self.plugins_service_logger.info(
                "Skipped loading plugin from '{}' because it was disabled.",
                str(plugin_project_folder),
            )
            return None

        # Check for valid project folder structure as specified by the manifest file.
        plugin_file = plugin_project_folder / Path(
            plugin_project_manifest_json["plugin"]["filepath"],
        )
        plugin_symbol = plugin_project_manifest_json["plugin"]["symbol"]

        if not plugin_file.exists():
            raise PluginProjectPluginFileNotFoundError(
                plugin_file=str(plugin_file),
                plugin_project_folder=str(plugin_project_folder),
            )

        # Check for valid symbol names in the required plugin project file.
        plugin_module_path = ".".join(
            plugin_file.relative_to(
                CONSORTIUM_HOME_DIRECTORY_PATH,
            ).parts,
        )[: -len(".py")]

        try:
            plugin_module = importlib.import_module(plugin_module_path)
            plugin_class = getattr(
                plugin_module,
                plugin_symbol,
            )
        except AttributeError:
            raise PluginProjectSymbolNotFoundError(
                symbol_name=plugin_symbol,
                plugin_project_folder=str(plugin_project_folder),
                plugin_file=str(plugin_file),
            )
        except PluginsFrameworkError as exc:
            raise exc from None
        # This should only catch errors that are not related to the plugin project.
        except Exception as exc:
            raise InternalPluginProjectError(
                plugin_project_folder=str(plugin_project_folder),
                internal_error_message=str(exc),
            )

        # Check for correct inheritance and instantiation of classes.
        if not issubclass(plugin_class, BasePlugin):
            raise PluginProjectInterfaceError(
                plugin_project_folder=str(plugin_project_folder),
                plugin_symbol=plugin_symbol,
            )

        try:
            plugin_object = plugin_class()
        except PluginsFrameworkError as exc:
            raise exc from None
        except Exception as exc:
            raise InternalPluginProjectError(
                plugin_project_folder=str(plugin_project_folder),
                internal_error_message=str(exc),
            )

        self.plugins_service_logger.debug(
            f"Retrieved plugin {plugin_object!r} from plugin project folder: "
            f"{plugin_project_folder}",
        )
        return plugin_object

    async def load_framework_plugins(
        self,
        ignore_enabled_plugin_flag: bool = False,
    ) -> None:
        self.plugins_service_logger.info(f"Loading framework plugins...")

        plugin_project_folder_paths = []
        load_plugins_tasks = []

        # Recursively search through the plugins directory to find all plugin project
        # folders.
        for path in CONSORTIUM_PLUGINS_DIRECTORY_PATH.rglob("*"):
            if path.name != "plugin_project_manifest.json":
                continue
            plugin_project_folder_paths.append(path.parent)
        for plugin_project_folder_path in plugin_project_folder_paths:
            load_plugins_tasks.append(
                asyncio.create_task(
                    self.load_plugin_from_plugin_project_folder(
                        plugin_project_folder=plugin_project_folder_path,
                        ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
                    ),
                ),
            )

        number_of_loaded_plugins = 0
        load_plugins_tasks_results = await asyncio.gather(
            *load_plugins_tasks,
            return_exceptions=True,
        )
        for result in load_plugins_tasks_results:
            if isinstance(result, (PluginLoadingError, PluginsFrameworkError)):
                self.plugins_service_logger.error(result)
            elif isinstance(result, Exception):
                self.plugins_service_logger.error(
                    "Fatal error occurred while loading plugin.",
                )
                self.plugins_service_logger.opt(colors=True, raw=True).error(
                    "<bold><red>{}</></>",
                    "".join(traceback.format_exception(result)),
                )
            elif result is None:
                continue
            else:
                number_of_loaded_plugins += 1

        self.plugins_service_logger.info(
            f"Loaded framework plugins ({number_of_loaded_plugins} plugin(s) "
            f"loaded).",
        )

    async def reload_framework_plugins(
        self,
        force_reload: bool = False,
        timeout: None | int = 5,
        ignore_enabled_plugin_flag: bool = False,
    ) -> None:
        self.plugins_service_logger.info(f"Reloading framework plugins...")

        unload_plugin_tasks = []
        load_plugin_tasks = []

        for plugin_id in self._plugins:
            unload_plugin_tasks.append(
                asyncio.create_task(
                    self.unload_plugin_by_plugin_id(
                        plugin_id=plugin_id,
                        force_unload=force_reload,
                        timeout=timeout,
                    ),
                ),
            )

        unload_plugin_tasks_results = await asyncio.gather(
            *unload_plugin_tasks,
            return_exceptions=True,
        )
        for result in unload_plugin_tasks_results:
            # A successful plugin unload will log the plugin load message. We only want
            # to log errors here.
            if isinstance(result, PluginUnloadError):
                self.plugins_service_logger.error(result)

        # Recursively search through the framework's plugin project folders directory
        # to find all plugin project folders. If a plugin project folder is found that
        # is not already loaded (it failed to unload), load it.
        for plugin_project_folder in CONSORTIUM_PLUGINS_DIRECTORY_PATH.rglob("*"):
            if plugin_project_folder.name != "plugin_project_manifest.json":
                continue
            plugin_loaded = False
            for plugin in self.get_all_plugins():
                if plugin.plugin_project_folder.parent == plugin_project_folder.parent:
                    plugin_loaded = True
                    break
            if not plugin_loaded:
                load_plugin_tasks.append(
                    asyncio.create_task(
                        self.load_plugin_from_plugin_project_folder(
                            plugin_project_folder=plugin_project_folder.parent,
                            ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
                        ),
                    ),
                )
        load_plugin_tasks_results = await asyncio.gather(
            *load_plugin_tasks,
            return_exceptions=True,
        )
        for result in load_plugin_tasks_results:
            # A successful plugin load will log the plugin load message. We only want to
            # log errors here.
            if isinstance(result, PluginLoadingError):
                self.plugins_service_logger.error(result)

        self.plugins_service_logger.info(
            f"Reloaded framework plugins.",
        )

    async def unload_framework_plugins(
        self,
        force_unload: bool = False,
        timeout: None | int = 5,
    ) -> None:
        self.plugins_service_logger.info(f"Unloading framework plugins...")

        number_of_unloaded_plugins = 0
        unload_plugin_tasks = []
        for plugin in self.get_all_plugins():
            if plugin.plugin_project_folder.parent == CONSORTIUM_PLUGINS_DIRECTORY_PATH:
                unload_plugin_tasks.append(
                    asyncio.create_task(
                        self.unload_plugin_by_plugin_id(
                            plugin_id=str(plugin.plugin_id),
                            force_unload=force_unload,
                            timeout=timeout,
                        ),
                    ),
                )
        unload_plugin_tasks_results = await asyncio.gather(
            *unload_plugin_tasks,
            return_exceptions=True,
        )
        for result in unload_plugin_tasks_results:
            # A successful plugin unload will log the plugin load message. We only want
            # to log errors here.
            if isinstance(result, PluginUnloadError):
                self.plugins_service_logger.error(result)
            else:
                number_of_unloaded_plugins += 1

        self.plugins_service_logger.info(
            f"Unloaded framework plugins ({number_of_unloaded_plugins} plugin(s) "
            f"unloaded).",
        )

    async def load_plugin_from_plugin_project_folder(
        self,
        plugin_project_folder: Path,
        ignore_enabled_plugin_flag: bool = False,
    ) -> BasePlugin | None:
        plugin = self.get_plugin_from_plugin_project_folder(
            plugin_project_folder=plugin_project_folder,
            ignore_enabled_plugin_project_flag=ignore_enabled_plugin_flag,
        )

        # `plugin` being `None` implies a disabled plugin was attempted to be loaded.
        if plugin is None:
            return None
        if plugin.autostart:
            try:
                await plugin.start_plugin()
            except Exception as exc:
                raise PluginLoadingError(
                    f"Failed to load plugin {plugin} because it failed to autostart "
                    f"due to an error: {exc}",
                )

        self._plugins[str(plugin.plugin_id)] = plugin
        self.plugins_service_logger.success(f"Loaded plugin: {plugin}")
        self.plugins_service_logger.debug(f"Loaded plugin: {plugin!r}")
        return plugin

    async def unload_plugin_by_plugin_id(
        self,
        plugin_id: str,
        force_unload: bool = False,
        timeout: None | int = 5,
    ) -> None:
        # This call will implicitly do a check to see if the plugin id is valid or not
        # so we do not need to check it again.
        plugin = self.get_plugin_by_plugin_id(plugin_id)

        try:
            await plugin.stop_plugin()
        except Exception as exc:
            if not force_unload:
                raise InternalPluginStopError(
                    plugin=str(plugin),
                    internal_error_message=str(exc),
                )

        if plugin.stop_plugin_event.is_set():
            if timeout is None:
                while plugin.status.state == PluginState.RUNNING:
                    await asyncio.sleep(1)
            else:
                for _ in range(timeout):
                    if plugin.status.state == PluginState.RUNNING:
                        await asyncio.sleep(1)
                    break

        if plugin.status.state != PluginState.STOPPED:
            if not force_unload:
                raise PluginStopTimeoutError(plugin=str(plugin))
            else:
                self.plugins_service_logger.warning(
                    f"Forcing plugin cancellation for plugin {plugin} because its "
                    f"timeout exceeded the specified duration: {timeout} seconds. ",
                )
                await plugin.cancel_plugin()

        del self._plugins[plugin_id]
        self.plugins_service_logger.info(f"Unloaded plugin: {plugin}")
        self.plugins_service_logger.debug(f"Unloaded plugin: {plugin!r}")

    async def reload_plugin_by_plugin_id(
        self,
        plugin_id: str,
        ignore_enabled_plugin_flag: bool = False,
    ) -> BasePlugin:
        plugin = self.get_plugin_by_plugin_id(plugin_id)
        plugin_project_folder = plugin.plugin_project_folder
        await self.unload_plugin_by_plugin_id(plugin_id)
        plugin = await self.load_plugin_from_plugin_project_folder(
            plugin_project_folder=plugin_project_folder,
            ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
        )
        self.plugins_service_logger.info(f"Reloaded plugin: {plugin}")
        self.plugins_service_logger.debug(f"Reloaded plugin: {plugin!r}")
        return plugin

    async def start_plugin_by_plugin_id(self, plugin_id: str, blocking: bool = False):
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        if not blocking:
            await plugin.start_plugin()
            return

        await plugin.start_plugin()
        while plugin.status.state in (PluginState.INITIALIZED, PluginState.STARTED):
            await asyncio.sleep(0.1)

    async def stop_plugin_by_plugin_id(self, plugin_id: str, blocking: bool = False):
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)

        if not blocking:
            await plugin.stop_plugin()
            return

        await plugin.stop_plugin()
        while plugin.status.state == PluginState.RUNNING:
            await asyncio.sleep(0.1)

    async def restart_plugin_by_plugin_id(self, plugin_id: str):
        await self.start_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)
        await self.stop_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)

    def get_plugin_by_plugin_id(self, plugin_id: str) -> BasePlugin:
        try:
            plugin = self._plugins[plugin_id]
        except KeyError:
            raise PluginNotFoundError(plugin_id=plugin_id)

        self.plugins_service_logger.debug(f"Retrieved plugin: {plugin!r}")
        return plugin

    def get_all_plugins(self) -> list[BasePlugin]:
        self.plugins_service_logger.debug(
            f"Retrieved all plugins ({len(self._plugins)} plugin(s) retrieved).",
        )
        return list(self._plugins.values())
