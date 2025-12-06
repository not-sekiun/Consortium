import asyncio
import graphlib
import pathlib

from loguru import logger

from consortium.framework.plugins._plugin_status import PluginState
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.framework.utils.exception_utils import remap_exception
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
    PluginsFrameworkError,
)
from consortium.server.exceptions.service_exceptions import (
    component_loader_service_exceptions as comp_ldr_svc_excs,
)
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    ComponentDependencyNotFoundError,
    ComponentDependencyNotRunningError,
    DuplicatePluginLabelError,
    IncompatibleComponentDependencyVersionError,
    IncompatiblePluginFrameworkVersionError,
    IncompatibleThirdPartyDependencyVersionError,
    InternalPluginProjectError,
    InternalPluginStartError,
    InternalPluginStopError,
    InvalidPluginProjectManifestFileJSONError,
    InvalidPluginProjectManifestFileSchemaError,
    InvalidPluginProjectPyProjectFileDependencyError,
    InvalidPluginProjectPyProjectFileError,
    PluginAlreadyRegisteredError,
    PluginDependsOnInvalidComponentDependencyError,
    PluginLabelNotFoundError,
    PluginLoadingError,
    PluginNotFoundError,
    PluginProjectInterfaceError,
    PluginProjectManifestFileNotFoundError,
    PluginProjectPluginFileNotFoundError,
    PluginProjectSymbolNotFoundError,
    PluginsServiceError,
    PluginStopTimeoutError,
    PluginUnloadingError,
    ThirdPartyDependencyNotFoundError,
)
from consortium.server.server_config import CONSORTIUM_PLUGINS_DIRECTORY_PATH
from consortium.server.services.component_loader_services.plugin_loader_service import (
    PluginLoaderService,
)


class PluginsService:
    _EXCEPTION_MAP = {
        comp_ldr_svc_excs.ComponentProjectManifestFileNotFoundError: PluginProjectManifestFileNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileJSONError: InvalidPluginProjectManifestFileJSONError,
        comp_ldr_svc_excs.InvalidComponentProjectManifestFileSchemaError: InvalidPluginProjectManifestFileSchemaError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileError: InvalidPluginProjectPyProjectFileError,
        comp_ldr_svc_excs.IncompatibleThirdPartyDependencyVersionError: IncompatibleThirdPartyDependencyVersionError,
        comp_ldr_svc_excs.ThirdPartyDependencyNotFoundError: ThirdPartyDependencyNotFoundError,
        comp_ldr_svc_excs.InvalidComponentProjectPyProjectFileDependencyError: InvalidPluginProjectPyProjectFileDependencyError,
        comp_ldr_svc_excs.ComponentProjectComponentFileNotFoundError: PluginProjectPluginFileNotFoundError,
        comp_ldr_svc_excs.ComponentProjectSymbolNotFoundError: PluginProjectSymbolNotFoundError,
        comp_ldr_svc_excs.ComponentProjectInterfaceError: PluginProjectInterfaceError,
        comp_ldr_svc_excs.IncompatibleComponentFrameworkVersionError: IncompatiblePluginFrameworkVersionError,
        comp_ldr_svc_excs.InternalComponentProjectError: InternalPluginProjectError,
        comp_ldr_svc_excs.ComponentDependencyNotFoundError: ComponentDependencyNotFoundError,
        comp_ldr_svc_excs.IncompatibleComponentDependencyVersionError: IncompatibleComponentDependencyVersionError,
        comp_ldr_svc_excs.ComponentDependencyNotRunningError: ComponentDependencyNotRunningError,
        comp_ldr_svc_excs.ComponentDependsOnInvalidComponentDependencyError: PluginDependsOnInvalidComponentDependencyError,
    }
    _EXCEPTION_KWARGS_MAP = {
        "component_project_folder": "plugin_project_folder",
        "component_file": "plugin_file",
        "component_symbol": "plugin_symbol",
        "component_str": "plugin_str",
        "component_id": "plugin_id",
    }

    def __init__(self):
        self._plugins = {}
        self._restart_plugin_tasks = set()
        self._plugin_loader_service = PluginLoaderService()
        self.logger = logger.bind(
            logger_name=str(self),
        )
        self.logger.debug("Started Plugins Service")

    def __str__(self):
        return "Plugins Service"

    def __repr__(self):
        return "PluginsService()"

    def get_plugin_from_plugin_project_folder(
        self,
        plugin_project_folder: pathlib.Path,
        ignore_enabled_plugin_flag: bool = False,
    ) -> BasePlugin | None:
        """
        Retrieves a plugin instance from a specified plugin project folder.

        Plugins that are specified to be disabled in their `manifest.json` will not be
        loaded unless `ignore_enabled_plugin_flag` is set to `True`. Valid plugins are
        instantiated and returned.

        Args:
            plugin_project_folder (pathlib.Path): The path of the folder containing the
                plugin project.
            ignore_enabled_plugin_flag (bool): If `True`, the method bypasses the
                enabled state check in the plugin project manifest.

        Returns:
            BasePlugin | None: An instance of the plugin if successfully retrieved, or
                `None` if the plugin is disabled and the enabled check is not
                overridden.

        Raises:
            PluginProjectManifestFileNotFoundError: If the plugin project manifest
                file, `plugin_project_manifest.json`, is missing.
            InvalidPluginProjectManifestFileJSONError: If the manifest file,
                `plugin_project_manifest.json`, contains invalid JSON.
            InvalidPluginProjectManifestFileSchemaError: If the manifest file
                `plugin_project_manifest.json` doesn't follow the expected schema.
            PluginProjectPluginFileNotFoundError: If the file specified in the plugin
                manifest, `plugin_project_manifest.json`, cannot be found.
            PluginProjectSymbolNotFoundError: If the symbol specified in the plugin
                manifest, `plugin_project_manifest.json`, is not found in the specified
                file.
            PluginProjectInterfaceError: If the plugin class does not correctly inherit
                from the [`BasePlugin`][consortium.framework.plugins.base_plugin.BasePlugin]
                class.
            IncompatiblePluginFrameworkVersionError: If the plugin is incompatible with
                the current framework version.
            InternalPluginProjectError: If an unhandled exception is raised within the
                plugin while initializing the plugin.
        """
        try:
            plugin = (
                self._plugin_loader_service.get_component_from_component_project_folder(
                    component_project_folder=plugin_project_folder,
                    ignore_enabled_component_flag=ignore_enabled_plugin_flag,
                )
            )
        except (
            comp_ldr_svc_excs.ComponentLoadingError,
            comp_ldr_svc_excs.ComponentDependencyError,
        ) as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=self._EXCEPTION_MAP,
                exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
            ) from None
        if plugin is None:
            self.logger.debug(
                "Skipped loading plugin from '{}' because it was disabled.",
                str(plugin_project_folder),
            )
        else:
            self.logger.debug(
                "Retrieved plugin {} from plugin project folder: {}",
                repr(plugin),
                str(plugin_project_folder),
            )
        return plugin

    def get_plugins_from_plugin_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_plugin_flag: bool = False,
    ) -> tuple[
        list[BasePlugin],
        list[pathlib.Path],
        list[tuple[pathlib.Path, PluginLoadingError]] | None,
    ]:
        """
        Retrieves all plugins from the specified directory containing plugin project folders.

        Plugins that are specified to be disabled in their `manifest.json` will not be
        loaded unless `ignore_enabled_plugin_flag` is set to `True`. Valid plugins are
        instantiated and returned.

        Args:
            directory (pathlib.Path): The path of the directory containing plugin
                project folders.
            ignore_enabled_plugin_flag (bool): If `True`, the method bypasses the
                enabled state check in the plugin project manifests.

        Returns:
            tuple[list[BasePlugin], list[pathlib.Path], list[tuple[pathlib.Path, PluginLoadingError]] | None]:
                A tuple containing three elements:
                1. A list of successfully retrieved plugin instances.
                2. A list of pathlib.Path objects representing the plugin project
                    folders that were skipped because the plugins were disabled.
                3. A list of tuples, each containing a pathlib.Path object representing
                    the plugin project folder that failed to load and the corresponding
                    `PluginLoadingError` exception.

        Raises:
            See [get_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.get_plugin_from_plugin_project_folder]
            for possible exceptions raised during plugin retrieval.
        """
        retrieved, skipped, errored = (
            self._plugin_loader_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_plugin_flag,
            )
        )
        remapped_errored = []
        for error_tuple in errored:
            error = error_tuple[1]
            # A configuration error will raise a PluginConfigurationError which is not
            # a ComponentLoadingError, so we only remap ComponentLoadingErrors here.
            if isinstance(
                error,
                (
                    comp_ldr_svc_excs.ComponentsLoaderServiceError,
                    comp_ldr_svc_excs.ComponentDependencyError,
                ),
            ):
                remapped_errored.append(
                    (
                        error_tuple[0],
                        remap_exception(
                            original_exception=error,
                            original_kwargs=error.kwargs,
                            exception_map=self._EXCEPTION_MAP,
                            exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
                        ),
                    ),
                )
            else:
                remapped_errored.append(error_tuple)
        self.logger.debug(
            "Retrieved plugins from '{}' ({} plugin(s) retrieved, {} plugin(s) "
            "skipped, {} plugin(s) failed to load)",
            directory,
            len(retrieved),
            len(skipped),
            len(remapped_errored),
        )
        return (
            retrieved,
            skipped,
            remapped_errored,
        )

    def register_plugin(
        self,
        plugin: BasePlugin,
    ) -> None:
        """
        Registers a plugin instance with the framework.

        Each plugin instance is uniquely identified and referred to by its `plugin_id`.
        Registering a plugin will not start it. Plugins that are registered must have
        unique labels.

        Args:
            plugin (BasePlugin): The plugin instance to register. It must have a unique
            `plugin_id` and conform to the `BasePlugin` interface. The plugin's `label`
            must be unique across all registered plugins.

        Returns:
            None

        Raises:
            PluginAlreadyRegisteredError: If a plugin with the same `plugin_id` is
                already registered.
            DuplicatePluginLabelError: If a plugin with the same `label` attribute is
                already registered.
            PluginDependencyNotFoundError: If the plugin depends on another plugin that
                is not registered.
            IncompatiblePluginDependencyVersionError: If the plugin depends on another
                plugin that is registered but has an incompatible version.
        """
        if str(plugin.plugin_id) in self._plugins:
            raise PluginAlreadyRegisteredError(
                plugin_str=str(plugin),
                plugin_id=str(plugin.plugin_id),
            )
        if plugin.label and plugin.label in [
            plugin.label for plugin in self._plugins.values() if plugin.label
        ]:
            raise DuplicatePluginLabelError(
                plugin_str=str(plugin),
                label=plugin.label,
            )
        try:
            self._plugin_loader_service.validate_component_component_dependencies(
                component=plugin,
                registered_components=self.get_all_plugins(),
            )
        except comp_ldr_svc_excs.ComponentDependencyError as exc:
            raise remap_exception(
                original_exception=exc,
                original_kwargs=exc.kwargs,
                exception_map=self._EXCEPTION_MAP,
                exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
            ) from None

        self._plugins[str(plugin.plugin_id)] = plugin
        self.logger.debug(f"Registered plugin: {plugin!r}")

    def register_plugin_from_plugin_project_folder(
        self,
        plugin_project_folder: pathlib.Path,
        ignore_enabled_plugin_flag: bool = False,
    ) -> BasePlugin | None:
        """
        Registers a plugin from the provided plugin project folder with the framework.

        If the plugin is disabled and the `ignore_enabled_plugin_project_flag` is set to False, the plugin will not be
        registered. On successful registration, the plugin is added to the internal
        plugin registry. Note that this method does not start the plugin; it only
        registers it.

        Args:
            plugin_project_folder (pathlib.Path): The path to the folder containing the
                plugin project from which the plugin is to be registered.
            ignore_enabled_plugin_flag (bool): Specifies whether to ignore the
                flag indicating whether the plugin is enabled in the provided project.
                Defaults to False.

        Returns:
            BasePlugin | None: Returns the registered plugin instance if the plugin is
            successfully registered; otherwise, returns None.

        Raises:
            See [get_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.get_plugin_from_plugin_project_folder]
            and [register_plugin][consortium.server.services.plugins_service.PluginsService.register_plugin]
            for possible exceptions raised during plugin retrieval.
        """
        plugin = self.get_plugin_from_plugin_project_folder(
            plugin_project_folder=plugin_project_folder,
            ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
        )
        # If `plugin` is `None`, it implies a disabled plugin was attempted to be
        # registered.
        if plugin is None:
            return None

        self.register_plugin(plugin=plugin)
        return plugin

    async def load_plugin_from_plugin_project_folder(
        self,
        plugin_project_folder: pathlib.Path,
        ignore_enabled_plugin_flag: bool = False,
    ) -> BasePlugin | None:
        """
        Loads a plugin from its project folder. The plugin is registered to the plugin
        service and additionally started if its `autostart` attribute is set to True.

        This function integrates with the plugin registration mechanism and ensures
        that any plugin meeting the specified requirements is properly initialized
        and prepared for further usage.

        Args:
            plugin_project_folder (pathlib.Path): The directory path where the plugin's
                project files are stored.
            ignore_enabled_plugin_flag (bool): Optional flag indicating whether the
                'enabled' status of the plugin should be ignored. Defaults to False.

        Returns:
            BasePlugin | None: Returns the loaded plugin instance if successful, or
            None if the plugin is disabled or cannot be loaded.

        Raises:
        """
        plugin = self.register_plugin_from_plugin_project_folder(
            plugin_project_folder=plugin_project_folder,
            ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
        )
        # `plugin` being `None` implies a disabled plugin was attempted to be loaded.
        if plugin is None:
            return None

        if plugin.autostart:
            try:
                await plugin.start()
            except BaseFrameworkException:
                raise
            except Exception as exc:
                raise InternalPluginStartError(
                    plugin_str=str(plugin),
                    internal_error_message=str(exc),
                ) from exc

        self.logger.success("Loaded plugin: {}", plugin)
        self.logger.debug("Loaded plugin: {!r}", plugin)
        return plugin

    async def unload_plugin_by_plugin_id(
        self,
        plugin_id: str,
        force_unload: bool = False,
        timeout: None | int = 5,
    ) -> None:
        """
        Unloads a plugin identified by its `plugin_id`, stopping its execution if
        necessary, and removing it from the internal plugin registry. The function
        ensures that the plugin is stopped either gracefully or forcibly based on the
        provided arguments. A timeout is used to wait for the plugin to stop, after
        which it will be forcibly stopped if specified before being unloaded.

        Args:
            plugin_id: The unique identifier of the plugin to be unloaded.
            force_unload: Whether to forcibly unload the plugin if it fails to stop
                within the timeout period. Default is False.
            timeout: The maximum duration in seconds to wait for the plugin to stop
                gracefully. If set to None, it will wait indefinitely. Default is 5
                seconds.

        Returns:
            None

        Raises:
            InternalPluginStopError: If the plugin fails to stop and force_unload is set
                to False due to internal errors.
            PluginStopTimeoutError: If the plugin fails to stop within the specified
                timeout, and force_unload is set to False.
        """
        # This call will implicitly do a check to see if the plugin id is valid or not
        # so we do not need to check it again.
        plugin = self.get_plugin_by_plugin_id(plugin_id)

        if plugin.status.state == PluginState.RUNNING:
            try:
                await plugin.stop()
            except BaseFrameworkException:
                if not force_unload:
                    raise
            except Exception as exc:
                if not force_unload:
                    raise InternalPluginStopError(
                        plugin_str=str(plugin),
                        internal_error_message=str(exc),
                    ) from exc

            # Ensure that the stop plugin event has been set before proceeding to wait
            # on the timeout.
            await plugin.stop_event.wait()
            if timeout is None:
                while plugin.status.state == PluginState.RUNNING:
                    await asyncio.sleep(1)
            else:
                # Every second check if the plugin has stopped and break early if it
                # has.
                for _ in range(timeout):
                    if plugin.status.state != PluginState.RUNNING:
                        break
                    await asyncio.sleep(1)

            # Check the state after the timeout and determine if we forcefully need to
            # cancel the plugin.
            if plugin.status.state != PluginState.STOPPED:
                if not force_unload:
                    raise PluginStopTimeoutError(plugin_str=str(plugin))
                else:
                    self.logger.warning(
                        f"Forcing plugin cancellation for plugin {plugin} because its "
                        f"timeout exceeded the specified duration: {timeout} second(s).",
                    )
                    await plugin.cancel()

        del self._plugins[plugin_id]
        self.logger.info(f"Unloaded plugin: {plugin}")
        self.logger.debug(f"Unloaded plugin: {plugin!r}")

    async def reload_plugin_by_plugin_id(
        self,
        plugin_id: str,
        ignore_enabled_plugin_flag: bool = False,
    ) -> BasePlugin | None:
        """
        Reloads a plugin by its plugin ID. This operation consists of unloading the
        plugin currently loaded and reloading it from the plugin project folder.

        Args:
            plugin_id: The unique identifier of the plugin to be reloaded.
            ignore_enabled_plugin_flag: A flag indicating whether to ignore the
                enabled plugin status during the reloading process. Defaults to False.

        Returns:
            BasePlugin: The reloaded plugin instance if successful, or None if the
                plugin is disabled and the enabled check is not overridden.

        Raises:
            See [get_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.get_plugin_by_plugin_id],
            [unload_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.unload_plugin_by_plugin_id]
            and [load_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.load_plugin_from_plugin_project_folder]
            for possible exceptions raised during the unload and load processes.
        """
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        plugin_project_folder = plugin.plugin_project_folder
        await self.unload_plugin_by_plugin_id(plugin_id=plugin_id)
        plugin = await self.load_plugin_from_plugin_project_folder(
            plugin_project_folder=plugin_project_folder,
            ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
        )
        self.logger.info(f"Reloaded plugin: {plugin}")
        self.logger.debug(f"Reloaded plugin: {plugin!r}")
        return plugin

    async def load_framework_plugins(
        self,
        ignore_enabled_plugin_flag: bool = False,
    ) -> None:
        self.logger.info(f"Loading framework plugins...")
        retrieved, skipped, errored = (
            self.get_plugins_from_plugin_project_folder_directories(
                directory=CONSORTIUM_PLUGINS_DIRECTORY_PATH,
                ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
            )
        )
        for path in skipped:
            self.logger.info(
                "├─ Skipped loading plugin from '{}' because it was disabled.",
                str(path),
            )
        if errored:
            for _, error in errored:
                self.logger.error(
                    "├─ {}",
                    str(error),
                )

        try:
            resolved_ordered_plugins, unresolved_plugins = (
                self._plugin_loader_service.resolve_component_load_order(
                    components=retrieved,
                    already_loaded_components=self.get_all_plugins(),
                )
            )
        except graphlib.CycleError as exc:
            circular_dependency_path = " -> ".join(exc.args[1])
            self.logger.error(
                "└─ Unable to load framework plugins. Detected circular dependencies "
                "in the plugin dependency graph: {}. Either remove the circularly "
                "dependent plugin(s) or fix their dependencies to resolve the issue.",
                circular_dependency_path,
            )
            return
        for plugin in unresolved_plugins:
            self.logger.error(
                "├─ {}",
                str(
                    remap_exception(
                        original_exception=plugin[1],
                        original_kwargs=plugin[1].kwargs,
                        exception_map=self._EXCEPTION_MAP,
                        exception_kwargs_map=self._EXCEPTION_KWARGS_MAP,
                    ),
                ),
            )

        # Register and start each plugin according to the topological sort order
        # determined.
        failed_to_load = 0
        for plugin in resolved_ordered_plugins:
            try:
                self.register_plugin(plugin)
                if plugin.autostart:
                    try:
                        await plugin.start()
                    except BaseFrameworkException:
                        raise
                    except Exception as exc:
                        raise InternalPluginStartError(
                            plugin_str=str(plugin),
                            internal_error_message=str(exc),
                        ) from exc
                self.logger.success("├─ Loaded plugin: {}", plugin)
                self.logger.debug("├─ Loaded plugin: {!r}", plugin)
            except (PluginsFrameworkError, PluginsServiceError) as exc:
                failed_to_load += 1
                self.logger.error("├─ {}", str(exc))

        self.logger.info(
            "└─ Loaded plugins from '{}' ({} plugin(s) loaded, {} plugin(s) "
            "skipped, {} plugin(s) failed to load).",
            str(CONSORTIUM_PLUGINS_DIRECTORY_PATH),
            len(resolved_ordered_plugins) - failed_to_load,
            len(skipped),
            len(errored) + len(unresolved_plugins) + failed_to_load,
        )

    async def unload_framework_plugins(
        self,
        force_unload: bool = False,
        timeout: None | int = 5,
    ) -> None:
        self.logger.info(f"Unloading framework plugins...")

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
            if isinstance(result, PluginUnloadingError):
                self.logger.error(result)
            else:
                number_of_unloaded_plugins += 1

        self.logger.info(
            "Unloaded framework plugins ({} plugin(s) unloaded).",
            number_of_unloaded_plugins,
        )

    async def reload_framework_plugins(
        self,
        force_reload: bool = False,
        timeout: None | int = 5,
        ignore_enabled_plugin_flag: bool = False,
    ) -> None:
        self.logger.info(f"Reloading framework plugins...")

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
            if isinstance(result, PluginUnloadingError):
                self.logger.error(result)

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
                self.logger.error(result)

        self.logger.info(f"Reloaded framework plugins.")

    async def start_plugin_by_plugin_id(
        self,
        plugin_id: str,
        blocking: bool = False,
    ) -> None:
        """
        Starts a plugin by its plugin id. The plugin must be registered to the
        service.

        Args:
            plugin_id (str): The plugin id to start.
            blocking (bool): If True, the method will block and wait until the plugin is
                stopped. If False, the method will return immediately after starting
                the plugin.

        Returns:
            None

        Raises:
            PluginNotFoundError: If the plugin id is not found in the service.
            IncompatibleThirdPartyDependencyVersionError: If the plugin requires a
                third party dependency that has a version not compatible with the one
                installed in the framework.
            ThirdPartyDependencyNotFoundError: If the plugin requires a third party
                dependency that is not installed in the framework.
            IncompatiblePluginDependencyVersionError: If the plugin requires another
                plugin to be installed that has a version not compatible with the one
                installed in the framework.
            PluginDependencyNotFoundError: If the plugin requires another plugin that
                is not installed in the framework.
            PluginDependencyNotRunningError: If the plugin requires another plugin that
                is installed and of the appropriate version but is not currently
                running.
            PluginAlreadyRunningError: If the plugin is already running.
            PluginStartError: If the plugin failed to start for any reason.
        """
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        await plugin.start()

        if not blocking:
            return
        while plugin.status.state in (PluginState.INITIALIZED, PluginState.STARTED):
            await asyncio.sleep(0.1)

    async def stop_plugin_by_plugin_id(
        self,
        plugin_id: str,
        blocking: bool = False,
    ) -> None:
        """
        Stops a plugin by its plugin id. The plugin must be registered to the
        service.

        Args:
            plugin_id (str): The plugin id to stop.
            blocking (bool): If True, the method will block and wait until the plugin is
                stopped. If False, the method will return immediately after stopping
                the plugin.

        Returns:
            None

        Raises:
            PluginNotFoundError: If the plugin id is not found in the service.
            PluginStopError: If the plugin failed to stop for any reason.
            PluginNotRunningError: If the plugin is not running.
        """
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        await plugin.stop()

        if not blocking:
            return
        while plugin.status.state == PluginState.RUNNING:
            await asyncio.sleep(0.1)

    async def restart_plugin_by_plugin_id(
        self,
        plugin_id: str,
        blocking: bool = False,
    ) -> None:
        """
        Restart a plugin by its plugin id.

        Args:
            plugin_id (str): The plugin with the plugin id to restart.
            blocking (bool): Whether the method should block and wait until the plugin
                is stopped and then started again or return immediately after
                attempting to restart the plugin.

        Returns:
            None

        Raises:
            See [stop_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.stop_plugin_by_plugin_id]
            and [start_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.start_plugin_by_plugin_id]
            for possible exceptions raised during stopping and starting the plugin.
        """

        async def _restart_plugin_task():
            # Block and wait for the plugin to stop before immediately starting again.
            await self.stop_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)
            await self.start_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)

        if blocking:
            await _restart_plugin_task()
        else:
            task = asyncio.create_task(_restart_plugin_task())
            self._restart_plugin_tasks.add(task)
            task.add_done_callback(
                lambda finished_task: self._restart_plugin_tasks.remove(finished_task),
            )

    def get_plugin_by_plugin_id(self, plugin_id: str) -> BasePlugin:
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

        self.logger.debug("Retrieved plugin: {!r}", plugin)
        return plugin

    def get_plugins_by_label(self, label: str) -> list[BasePlugin]:
        """
        Returns all plugins loaded in the service that have the provided label.

        Args:
            label (str): The label to search for.

        Returns:
            list[BasePlugin]: The list of plugins, if found.

        Raises:
            PluginLabelNotFoundError: If the plugin label is not found in the service.
        """
        plugins = []
        for plugin in self.get_all_plugins():
            if plugin.label == label:
                self.logger.debug("Retrieved plugin: {!r}", plugin)
                plugins.append(plugin)

        if plugins:
            return plugins
        else:
            raise PluginLabelNotFoundError(label=label)

    def get_all_plugins(self) -> list[BasePlugin]:
        """
        Returns a list of all plugins loaded in the service.

        Returns:
            list[BasePlugin]: A list of all plugins loaded in the service.
        """
        self.logger.debug(
            "Retrieved all plugins ({} plugin(s) retrieved).",
            len(self._plugins),
        )
        return list(self._plugins.values())
