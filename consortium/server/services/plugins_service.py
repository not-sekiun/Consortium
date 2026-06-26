import asyncio
import graphlib
import pathlib
import uuid

from loguru import logger

from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.consortium_exceptions.plugins_consortium_exceptions import (
    PluginLoadingError,
    PluginsError,
    PluginUnloadingError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.component_loader_services.plugin_loader_service import (
    PluginLoaderService,
)
from consortium.server.services.component_registry_services.plugin_registry_service import (
    PluginRegistryService,
)
from consortium.server.services.release_service import ReleaseService
from consortium.server.utils import log_and_propagate_error_on_service_method


class PluginsService:
    def __init__(
        self,
        release_service: ReleaseService,
        plugins_directory: pathlib.Path,
        consortium_root: pathlib.Path,
    ):
        self._plugins_directory = plugins_directory
        self._plugins = {}
        self._plugin_loader_service = PluginLoaderService(
            consortium_root=consortium_root, release_service=release_service
        )
        self._plugin_registry_service = PluginRegistryService(
            component_loader_service=self._plugin_loader_service,
            component_framework_directory=self._plugins_directory,
        )
        self._restart_plugin_tasks = set()
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started Plugins Service")

    def __str__(self):
        return "Plugins Service"

    def __repr__(self):
        return "PluginsService()"

    @log_and_propagate_error_on_service_method
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
                enabled status check in the plugin project manifest.

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
        plugin = (
            self._plugin_registry_service.get_component_from_component_project_folder(
                component_project_folder=plugin_project_folder,
                ignore_enabled_component_flag=ignore_enabled_plugin_flag,
            )
        )
        if plugin is None:
            self._logger.debug(
                "Skipped loading plugin from '{}' because it was disabled",
                str(plugin_project_folder),
            )
        else:
            self._logger.debug(
                "Retrieved plugin {} from plugin project folder: {}",
                repr(plugin),
                str(plugin_project_folder),
            )
        return plugin

    @log_and_propagate_error_on_service_method
    def get_plugins_from_plugin_project_folder_directories(
        self,
        directory: pathlib.Path,
        ignore_enabled_plugin_flag: bool = False,
    ) -> tuple[
        list[BasePlugin],
        list[pathlib.Path],
        list[tuple[pathlib.Path, PluginLoadingError]],
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
                enabled status check in the plugin project manifests.

        Returns:
            tuple[list[BasePlugin], list[pathlib.Path], list[tuple[pathlib.Path, PluginLoadingError]]: A tuple containing three elements.

                1. A list of successfully retrieved plugin instances.

                2. A list of `pathlib.Path` objects representing the plugin project
                folders that were skipped because the plugins were disabled.

                3. A list of tuples, each containing a `pathlib.Path` object representing
                the plugin project folder that failed to load and the corresponding
                `PluginsError`

        Raises:
            PluginsError: See [get_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.get_plugin_from_plugin_project_folder]
                for possible exceptions raised during plugin retrieval.
        """
        retrieved, skipped, errored = (
            self._plugin_registry_service.get_components_from_component_project_folder_directories(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_plugin_flag,
            )
        )
        self._logger.debug(
            "Retrieved plugins from '{}' ({} plugin(s) retrieved, {} plugin(s) "
            "skipped, {} plugin(s) failed to load)",
            directory,
            len(retrieved),
            len(skipped),
            len(errored),
        )
        return (
            retrieved,
            skipped,
            errored,
        )

    @log_and_propagate_error_on_service_method
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
        self._plugin_registry_service.register_component(component=plugin)
        self._logger.debug("Registered plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
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
            `PluginsError`: See [get_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.get_plugin_from_plugin_project_folder]
                and [register_plugin][consortium.server.services.plugins_service.PluginsService.register_plugin]
                for possible exceptions raised during plugin registration.
        """
        plugin = self._plugin_registry_service.register_component_from_component_project_folder(
            component_project_folder=plugin_project_folder,
            ignore_enabled_component_flag=ignore_enabled_plugin_flag,
        )
        self._logger.debug("Registered plugin: {!r}", plugin)
        return plugin

    @log_and_propagate_error_on_service_method
    async def load_plugin_from_plugin_project_folder(
        self,
        plugin_project_folder: pathlib.Path,
        ignore_enabled_plugin_flag: bool = False,
        timeout: int | None = 5,
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
            timeout (int): The maximum time in seconds to wait for the plugin to start.

        Returns:
            BasePlugin | None: Returns the loaded plugin instance if successful, or
            None if the plugin is disabled or cannot be loaded.

        Raises:
            `PluginsError`: See [get_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.get_plugin_from_plugin_project_folder]
                and [register_plugin][consortium.server.services.plugins_service.PluginsService.register_plugin]
                for possible exceptions raised during plugin loading.
            `PluginStartError`: If the plugin fails to start.
        """
        plugin = await self._plugin_registry_service.load_component_from_component_project_folder(
            component_project_folder=plugin_project_folder,
            ignore_enabled_component_flag=ignore_enabled_plugin_flag,
            context={"timeout": timeout},
        )
        self._logger.success("Loaded plugin: {}", plugin)
        self._logger.debug("Loaded plugin: {!r}", plugin)
        return plugin

    @log_and_propagate_error_on_service_method
    async def unload_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
        timeout: int | None = 5,
        force_unload: bool = False,
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
        plugin = await self._plugin_registry_service.unload_component_by_component_id(
            component_id=plugin_id,
            context={
                "timeout": timeout,
                "force_unload": force_unload,
                "logger": self._logger,
            },
        )
        self._logger.info("Unloaded plugin: {}", plugin)
        self._logger.debug("Unloaded plugin: {!r}", plugin)

        # # This call will implicitly do a check to see if the plugin id is valid or not
        # # so we do not need to check it again.
        # plugin = self.get_plugin_by_plugin_id(plugin_id)
        #
        # if plugin.status.status == State.RUNNING:
        #     try:
        #         await plugin.stop()
        #     except BaseFrameworkException as exc:
        #         if not force_unload:
        #             raise exc
        #     except Exception as exc:
        #         if not force_unload:
        #             raise exc
        #
        #     # Ensure that the stop plugin event has been set before proceeding to wait
        #     # on the timeout.
        #     await plugin.stop_event.wait()
        #     if timeout is None:
        #         while plugin.status.status == State.RUNNING:
        #             await asyncio.sleep(1)
        #     else:
        #         # Every second check if the plugin has stopped and break early if it
        #         # has.
        #         for _ in range(timeout):
        #             if plugin.status.status != State.RUNNING:
        #                 break
        #             await asyncio.sleep(1)
        #
        #     # Check the status after the timeout and determine if we forcefully need to
        #     # cancel the plugin.
        #     if plugin.status.status != State.STOPPED:
        #         if not force_unload:
        #             raise PluginStopTimeoutError(plugin_str=str(plugin))
        #         else:
        #             self.logger.warning(
        #                 f"Forcing plugin cancellation for plugin {plugin} because its "
        #                 f"timeout exceeded the specified duration: {timeout} second(s)",
        #             )
        #             await plugin.cancel()
        #
        # del self._plugins[plugin_id]
        # self.logger.info("Unloaded plugin: {}", plugin)
        # self.logger.debug("Unloaded plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    async def reload_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
        ignore_enabled_plugin_flag: bool = False,
        load_timeout: int | None = 5,
        unload_timeout: int | None = 5,
        force_unload: bool = False,
    ) -> BasePlugin | None:
        """
        Reloads a plugin by its plugin ID. This operation consists of unloading the
        plugin currently loaded and reloading it from the plugin project folder.

        Args:
            plugin_id: The unique identifier of the plugin to be reloaded.
            ignore_enabled_plugin_flag: A flag indicating whether to ignore the
                enabled plugin status during the reloading process. Defaults to False.
            load_timeout: The maximum duration in seconds to wait for the plugin to
            unload_timeout: The maximum duration in seconds to wait for the plugin to
                unload. If set to None, it will wait indefinitely.
            force_unload: Whether to forcibly unload the plugin if it fails to stop
                within the timeout period.

        Returns:
            BasePlugin: The reloaded plugin instance if successful, or None if the
                plugin is disabled and the enabled check is not overridden.

        Raises:
            See [get_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.get_plugin_by_plugin_id],
            [unload_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.unload_plugin_by_plugin_id]
            and [load_plugin_from_plugin_project_folder][consortium.server.services.plugins_service.PluginsService.load_plugin_from_plugin_project_folder]
            for possible exceptions raised during the unload and load processes.
        """
        plugin = await self._plugin_registry_service.reload_component_by_component_id(
            component_id=plugin_id,
            ignore_enabled_component_flag=ignore_enabled_plugin_flag,
            load_context={
                "timeout": load_timeout,
            },
            unload_context={
                "timeout": unload_timeout,
                "force_unload": force_unload,
                "logger": self._logger,
            },
        )
        self._logger.info("Reloaded plugin: {}", plugin)
        self._logger.debug("Reloaded plugin: {!r}", plugin)
        return plugin

        # plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        # plugin_project_folder = plugin.plugin_project_folder
        # await self.unload_plugin_by_plugin_id(
        #     plugin_id=plugin_id,
        #     timeout=unload_timeout,
        #     force_unload=force_unload,
        # )
        # plugin = await self.load_plugin_from_plugin_project_folder(
        #     plugin_project_folder=plugin_project_folder,
        #     ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
        #     timeout=load_timeout,
        # )
        # self.logger.info("Reloaded plugin: {}", plugin)
        # self.logger.debug("Reloaded plugin: {!r}", plugin)
        # return plugin

    @log_and_propagate_error_on_service_method
    async def load_framework_plugins(
        self,
        ignore_enabled_plugin_flag: bool = False,
    ) -> None:
        self._logger.info("Loading framework plugins...")
        retrieved, skipped, errored = (
            self.get_plugins_from_plugin_project_folder_directories(
                directory=self._plugins_directory,
                ignore_enabled_plugin_flag=ignore_enabled_plugin_flag,
            )
        )
        for path in skipped:
            self._logger.info(
                "- Skipped loading plugin from '{}' because it was disabled",
                str(path),
            )
        if errored:
            for _, error in errored:
                self._logger.error(
                    "- {}",
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
            self._logger.error(
                "Unable to load framework plugins. Detected circular "
                "dependencies in the plugin dependency graph: {}. Either remove "
                "the circularly dependent plugin(s) or fix their dependencies to "
                "resolve the issue.",
                circular_dependency_path,
            )
            return
        for plugin in unresolved_plugins:
            self._logger.error("- {}", plugin[1])

        # Register and start each plugin according to the topological sort order
        # determined.
        failed_to_load = 0
        for plugin in resolved_ordered_plugins:
            try:
                self.register_plugin(plugin)
                if plugin.autostart:
                    await plugin.start()
                self._logger.success("- Loaded plugin: {}", plugin)
                self._logger.debug("- Loaded plugin: {!r}", plugin)
            except PluginsError as exc:
                failed_to_load += 1
                self._logger.error("- {}", str(exc))
            except Exception as exc:
                failed_to_load += 1
                self._logger.error(
                    "- Failed to load the plugin {}. An unhandled exception "
                    "occurred while starting the plugin: {}",
                    plugin,
                    str(exc),
                )

        self._logger.info(
            "Loaded plugins from '{}' ({} plugin(s) loaded, {} plugin(s) "
            "skipped, {} plugin(s) failed to load)",
            str(self._plugins_directory),
            len(resolved_ordered_plugins) - failed_to_load,
            len(skipped),
            len(errored) + len(unresolved_plugins) + failed_to_load,
        )

    @log_and_propagate_error_on_service_method
    async def unload_framework_plugins(
        self,
        force_unload: bool = False,
        timeout: None | int = 5,
    ) -> None:
        self._logger.info("Unloading framework plugins...")

        number_of_unloaded_plugins = 0
        unload_plugin_tasks = []
        for plugin in self.get_all_plugins():
            if plugin.plugin_project_folder.resolve().relative_to(
                self._plugins_directory.resolve()
            ):
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
                self._logger.error(result)
            else:
                number_of_unloaded_plugins += 1

        self._logger.info(
            "Unloaded framework plugins ({} plugin(s) unloaded)",
            number_of_unloaded_plugins,
        )

    @log_and_propagate_error_on_service_method
    async def reload_framework_plugins(
        self,
        force_reload: bool = False,
        timeout: None | int = 5,
        ignore_enabled_plugin_flag: bool = False,
    ) -> None:
        self._logger.info("Reloading framework plugins...")

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
                self._logger.error(result)

        # Recursively search through the framework's plugin project folders directory
        # to find all plugin project folders. If a plugin project folder is found that
        # is not already loaded (it failed to unload), load it.
        for plugin_project_folder in self._plugins_directory.rglob("*"):
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
                self._logger.error(result)

        self._logger.info("Reloaded framework plugins")

    @log_and_propagate_error_on_service_method
    async def start_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
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

        if blocking:
            await plugin.wait_until_started()

        self._logger.debug("Started plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    async def stop_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
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

        Raises:
            PluginNotFoundError: If the plugin id is not found in the service.
            PluginStopError: If the plugin failed to stop for any reason.
            PluginNotRunningError: If the plugin is not running.
        """
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        await plugin.stop()

        if blocking:
            await plugin.wait_until_stopped()

        self._logger.debug("Stopped plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    async def restart_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
        blocking: bool = False,
    ) -> None:
        """
        Restart a plugin by its plugin id.

        Args:
            plugin_id (str): The plugin with the plugin id to restart.
            blocking (bool): Whether the method should block and wait until the plugin
                is stopped and then started again or return immediately after
                attempting to restart the plugin.

        Raises:
            See [stop_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.stop_plugin_by_plugin_id]
            and [start_plugin_by_plugin_id][consortium.server.services.plugins_service.PluginsService.start_plugin_by_plugin_id]
            for possible exceptions raised during stopping and starting the plugin.
        """

        async def _restart_plugin():
            # Block and wait for the plugin to stop before immediately starting again.
            await self.stop_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)
            await self.start_plugin_by_plugin_id(plugin_id=plugin_id, blocking=True)

        if blocking:
            await _restart_plugin()
        else:
            task = asyncio.create_task(_restart_plugin())
            self._restart_plugin_tasks.add(task)
            task.add_done_callback(
                lambda finished_task: self._restart_plugin_tasks.remove(finished_task),
            )

        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        self._logger.debug("Restarted plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    async def cancel_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
        blocking: bool = False,
    ) -> None:
        """
        Cancels a plugin by its plugin id. The plugin must be registered to the
        service.

        Args:
            plugin_id (str): The plugin id to cancel.
            blocking (bool): If True, the method will block and wait until the plugin is
                cancelled. If False, the method will return immediately after
                cancelling the plugin.

        Raises:
            PluginNotFoundError: If the plugin id is not found in the service.
            PluginNotRunningError: If the plugin is not running.
        """
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        await plugin.cancel()

        if blocking:
            await plugin.wait_until_stopped()

        self._logger.debug("Cancelled plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    def get_plugin_by_plugin_id(self, plugin_id: str | uuid.UUID) -> BasePlugin:
        """
        Returns a plugin object by its plugin id. The plugin must be registered to the
        service.

        Args:
            plugin_id (str | uuid.UUID): The plugin id to search for.

        Returns:
            BasePlugin: The plugin object if found.

        Raises:
            PluginNotFoundError: If the plugin id is not found in the service.
        """
        plugin = self._plugin_registry_service.get_component_by_component_id(
            component_id=plugin_id,
        )
        self._logger.debug("Retrieved plugin: {!r}", plugin)
        return plugin

    @log_and_propagate_error_on_service_method
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
        return self._plugin_registry_service.get_components_by_label(label=label)

    @log_and_propagate_error_on_service_method
    def get_all_plugins(self) -> list[BasePlugin]:
        """
        Returns a list of all plugins loaded in the service.

        Returns:
            list[BasePlugin]: A list of all plugins loaded in the service.
        """
        plugins = self._plugin_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all plugins ({} plugin(s) retrieved)",
            len(plugins),
        )
        return plugins
