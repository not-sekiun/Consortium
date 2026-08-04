import asyncio
import graphlib
import pathlib
import uuid

from loguru import logger

from consortium.framework._core.framework_exceptions.plugins_framework_exceptions import (
    PluginsFrameworkError,
)
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.exceptions.service_exceptions.plugins_service_exceptions import (
    PluginLoadingError,
    PluginsServiceError,
    PluginUnloadingError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.services.component_loader_services.plugin_loader_service import (
    PluginLoaderService,
)
from consortium.server.services.component_registry_services.plugin_registry_service import (
    PluginRegistryService,
)
from consortium.server.services.paths_service import PathsService
from consortium.server.services.release_service import ReleaseService
from consortium.server.utils import log_and_propagate_error_on_service_method


class PluginsService:
    def __init__(
        self,
        release_service: ReleaseService,
        paths_service: PathsService,
    ):
        self._plugins_directory = paths_service.plugins_directory
        self._plugins = {}
        self._plugin_loader_service = PluginLoaderService(
            paths_service=paths_service, release_service=release_service
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
    def get_plugin_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> BasePlugin | None:
        """Instantiates a plugin from a root directory without registering it.

        Disabled plugins (as indicated by `enabled: false` in their `manifest.json`)
        are not instantiated unless `ignore_enabled_flag` is `True`.

        Args:
            directory: Path to the directory containing the plugin
                project files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the `enabled` check in
                the manifest. Defaults to `False`.

        Returns:
            The instantiated plugin, or `None` if the plugin is disabled and the
            enabled check is not overridden.

        Raises:
            PluginManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidPluginManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidPluginManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            PluginEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            PluginSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            PluginInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatiblePluginFrameworkVersionError: If the plugin is incompatible
                with the current framework version.
            InternalPluginError: If an unhandled exception occurs while
                loading the plugin.
        """
        plugin = self._plugin_registry_service.get_component_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_flag,
        )
        if plugin is None:
            self._logger.debug(
                "Skipped loading plugin from '{}' because it was disabled",
                str(directory),
            )
        else:
            self._logger.debug(
                "Retrieved plugin {} from plugin root directory: {}",
                repr(plugin),
                str(directory),
            )
        return plugin

    @log_and_propagate_error_on_service_method
    def get_all_plugins_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> tuple[
        list[BasePlugin],
        list[pathlib.Path],
        list[tuple[pathlib.Path, PluginLoadingError]],
    ]:
        """Recursively scans a directory for plugin root directories and instantiates them.

        Disabled plugins (as indicated by `enabled: false` in their `manifest.json`)
        are skipped unless `ignore_enabled_flag` is `True`. Plugins that fail to
        load are collected in the returned error list rather than aborting the scan.

        Args:
            directory: The directory to scan for plugin root directories.
            ignore_enabled_flag: When `True`, bypasses the `enabled` check in
                each plugin's manifest. Defaults to `False`.

        Returns:
            A three-element tuple: (1) a list of successfully instantiated plugins, (2)
            a list of paths skipped because the plugin was disabled, and (3) a list of
            `(path, error)` tuples for plugins that failed to load.
        """
        retrieved, skipped, errored = (
            self._plugin_registry_service.get_all_components_from_directory(
                directory=directory,
                ignore_enabled_component_flag=ignore_enabled_flag,
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
        """Registers an already-instantiated plugin with the service.

        Each plugin is uniquely identified by its `plugin_id`. Registration validates
        that the plugin's ID and label are unique and that all of its declared component
        dependencies are satisfied. Registering a plugin does not start it.

        Args:
            plugin: The plugin instance to register.

        Raises:
            PluginAlreadyRegisteredError: If a plugin with the same ID is already
                registered.
            DuplicatePluginLabelError: If a plugin with the same label is already
                registered.
            ComponentDependencyNotFoundError: If the plugin declares a dependency on
                another component that is not registered.
            IncompatibleComponentDependencyVersionError: If the plugin declares a
                dependency on a registered component whose version does not satisfy the
                required specifier.
        """
        self._plugin_registry_service.register_component(component=plugin)
        self._logger.debug("Registered plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    def register_plugin_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
    ) -> BasePlugin | None:
        """Instantiates and registers a plugin from a root directory.

        Disabled plugins are skipped unless `ignore_enabled_flag` is `True`.
        This method registers the plugin but does not start it.

        Args:
            directory: Path to the directory containing the plugin project
                files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the `enabled` check in
                the manifest. Defaults to `False`.

        Returns:
            The registered plugin, or `None` if the plugin is disabled and the enabled
            check is not overridden.

        Raises:
            PluginManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidPluginManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidPluginManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            PluginEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            PluginSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            PluginInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatiblePluginFrameworkVersionError: If the plugin is incompatible
                with the current framework version.
            InternalPluginError: If an unhandled exception occurs while
                loading the plugin.
            PluginAlreadyRegisteredError: If a plugin with the same ID is already
                registered.
            DuplicatePluginLabelError: If a plugin with the same label is already
                registered.
            ComponentDependencyNotFoundError: If the plugin declares a dependency on
                another component that is not registered.
            IncompatibleComponentDependencyVersionError: If the plugin declares a
                dependency on a registered component whose version does not satisfy the
                required specifier.
        """
        plugin = self._plugin_registry_service.register_component_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_flag,
        )
        self._logger.debug("Registered plugin: {!r}", plugin)
        return plugin

    @log_and_propagate_error_on_service_method
    async def load_plugin_from_directory(
        self,
        directory: pathlib.Path,
        ignore_enabled_flag: bool = False,
        timeout: int | None = 5,
    ) -> BasePlugin | None:
        """Loads a plugin from a root directory, registering it and starting it if it autostarts.

        Disabled plugins are skipped unless `ignore_enabled_flag` is `True`.
        After registration, the plugin is started when its `autostart` attribute is
        `True`.

        Args:
            directory: Path to the directory containing the plugin project
                files and `manifest.json`.
            ignore_enabled_flag: When `True`, bypasses the `enabled` check in
                the manifest. Defaults to `False`.
            timeout: The maximum number of seconds to wait for the plugin to start when
                it autostarts. When `None`, waits indefinitely. Defaults to 5.

        Returns:
            The loaded plugin, or `None` if the plugin is disabled and the enabled
            check is not overridden.

        Raises:
            PluginManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidPluginManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidPluginManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            PluginEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            PluginSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            PluginInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatiblePluginFrameworkVersionError: If the plugin is incompatible
                with the current framework version.
            InternalPluginError: If an unhandled exception occurs while
                loading the plugin.
            PluginStartError: If the plugin autostarts but fails to start.
        """
        plugin = await self._plugin_registry_service.load_component_from_directory(
            directory=directory,
            ignore_enabled_component_flag=ignore_enabled_flag,
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
        """Stops (if running) and deregisters a loaded plugin by its ID.

        A running plugin is stopped before it is removed from the registry. A plugin
        that does not stop within `timeout` is either forcibly cancelled (when
        `force_unload` is `True`) or causes the unload to fail (when `force_unload` is
        `False`).

        Args:
            plugin_id: The ID of the plugin to unload.
            timeout: The maximum number of seconds to wait for the plugin to stop. When
                `None`, waits indefinitely. Defaults to 5.
            force_unload: When `True`, a plugin that fails to stop cleanly within
                `timeout` is forcibly cancelled and still unloaded. When `False`
                (default), a failure to stop cleanly aborts the unload.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
            PluginStopError: If the plugin fails to stop and `force_unload` is `False`.
            PluginStopTimeoutError: If the plugin does not stop within `timeout` and
                `force_unload` is `False`.
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

    @log_and_propagate_error_on_service_method
    async def reload_plugin_by_plugin_id(
        self,
        plugin_id: str | uuid.UUID,
        ignore_enabled_flag: bool = False,
        load_timeout: int | None = 5,
        unload_timeout: int | None = 5,
        force_unload: bool = False,
    ) -> BasePlugin | None:
        """Unloads a plugin then reloads it from its original root directory.

        The plugin is stopped and deregistered, then loaded again from the root
        directory it was originally loaded from, starting it again if it autostarts. If the
        plugin is disabled after reload and `ignore_enabled_flag` is `False`, the
        plugin will only be unloaded, not reloaded.

        Args:
            plugin_id: The ID of the plugin to reload.
            ignore_enabled_flag: When `True`, bypasses the `enabled` check in
                the manifest during reload. Defaults to `False`.
            load_timeout: The maximum number of seconds to wait for the plugin to start
                when it autostarts on reload. When `None`, waits indefinitely. Defaults
                to 5.
            unload_timeout: The maximum number of seconds to wait for the plugin to stop
                during unload. When `None`, waits indefinitely. Defaults to 5.
            force_unload: When `True`, a plugin that fails to stop cleanly within
                `unload_timeout` is forcibly cancelled during the unload step. When
                `False` (default), a failure to stop cleanly aborts the reload.

        Returns:
            The reloaded plugin, or `None` if the plugin is disabled and the enabled
            check is not overridden.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
            PluginStopError: If the plugin fails to stop during unload and
                `force_unload` is `False`.
            PluginStopTimeoutError: If the plugin does not stop within `unload_timeout`
                and `force_unload` is `False`.
            PluginManifestFileNotFoundError: If `manifest.json` is missing.
            InvalidPluginManifestFileJSONError: If `manifest.json` contains
                invalid JSON.
            InvalidPluginManifestFileSchemaError: If `manifest.json` does not
                follow the expected schema.
            PluginEntryPointModuleNotFoundError: If the entry-point module
                cannot be found.
            PluginSymbolNotFoundError: If the symbol specified in the manifest
                is not found.
            PluginInterfaceError: If the class does not inherit from the
                expected base class.
            IncompatiblePluginFrameworkVersionError: If the plugin is incompatible
                with the current framework version.
            InternalPluginError: If an unhandled exception occurs while
                loading the plugin.
            PluginStartError: If the reloaded plugin autostarts but fails to start.
        """
        plugin = await self._plugin_registry_service.reload_component_by_component_id(
            component_id=plugin_id,
            ignore_enabled_component_flag=ignore_enabled_flag,
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

    @log_and_propagate_error_on_service_method
    async def load_framework_plugins(
        self,
        ignore_enabled_flag: bool = False,
    ) -> None:
        """Discovers and loads all plugins from the framework's plugins directory.

        Every plugin root directory under the framework plugins directory is discovered,
        resolved into a dependency-respecting load order, then registered and (when the
        plugin has `autostart` set) started. Disabled plugins are skipped unless
        `ignore_enabled_flag` is set. Discovery errors, unresolved dependencies,
        circular dependencies, and per-plugin load failures are logged rather than
        raised so that a single bad plugin does not abort loading the rest.

        Args:
            ignore_enabled_flag: When `True`, plugins are loaded even if they are
                marked as disabled. When `False` (default), disabled plugins are skipped.
        """
        self._logger.info("Loading framework plugins...")
        retrieved, skipped, errored = self.get_all_plugins_from_directory(
            directory=self._plugins_directory,
            ignore_enabled_flag=ignore_enabled_flag,
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
            except (PluginsServiceError, PluginsFrameworkError) as exc:
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
        """Unloads every loaded plugin that lives under the framework plugins directory.

        Each matching plugin is unloaded concurrently. Failures to unload individual
        plugins are logged rather than raised so that one failing plugin does not prevent
        the others from being unloaded.

        Args:
            force_unload: When `True`, plugins are unloaded even if they do not stop
                cleanly within `timeout`. When `False` (default), an unclean stop causes
                that plugin's unload to fail.
            timeout: The number of seconds to wait for each plugin to stop before its
                unload is considered to have timed out. When `None`, waits indefinitely.
        """
        self._logger.info("Unloading framework plugins...")

        number_of_unloaded_plugins = 0
        unload_plugin_tasks = []
        for plugin in self.get_all_plugins():
            if plugin.root_directory.resolve().is_relative_to(
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
        ignore_enabled_flag: bool = False,
    ) -> None:
        """Unloads all currently loaded plugins and reloads them from disk.

        Every currently loaded plugin is unloaded concurrently, then the framework
        plugins directory is rescanned and any plugin that is not already
        loaded (for example one that failed to unload) is loaded again. Per-plugin unload
        and load failures are logged rather than raised so that one failing plugin does
        not prevent the others from being reloaded.

        Args:
            force_reload: When `True`, plugins are unloaded even if they do not stop
                cleanly within `timeout` before being loaded again. When `False`
                (default), an unclean stop causes that plugin's unload to fail.
            timeout: The number of seconds to wait for each plugin to stop before its
                unload is considered to have timed out. When `None`, waits indefinitely.
            ignore_enabled_flag: When `True`, plugins are loaded even if they are
                marked as disabled. When `False` (default), disabled plugins are skipped
                when reloading.
        """
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

        # Recursively search through the framework's plugins directory to find all
        # plugins. If a plugin is found that is not already loaded (it failed to
        # unload), load it.
        for path in self._plugins_directory.rglob("*"):
            if path.name != "manifest.json":
                continue
            plugin_loaded = False
            for plugin in self.get_all_plugins():
                if plugin.root_directory.parent == path.parent:
                    plugin_loaded = True
                    break
            if not plugin_loaded:
                load_plugin_tasks.append(
                    asyncio.create_task(
                        self.load_plugin_from_directory(
                            directory=path.parent,
                            ignore_enabled_flag=ignore_enabled_flag,
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
        """Starts a loaded plugin by its ID.

        Args:
            plugin_id: The ID of the plugin to start.
            blocking: When `True`, blocks until the plugin has finished starting. When
                `False` (default), returns immediately after starting the plugin.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
            PluginAlreadyRunningError: If the plugin is already running.
            PluginStartError: If the plugin fails to start.
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
        """Stops a loaded plugin by its ID.

        Args:
            plugin_id: The ID of the plugin to stop.
            blocking: When `True`, blocks until the plugin has finished stopping. When
                `False` (default), returns immediately after stopping the plugin.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
            PluginNotRunningError: If the plugin is not running.
            PluginStopError: If the plugin fails to stop.
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
        """Restarts a loaded plugin by its ID, stopping it and then starting it again.

        When `blocking` is `False`, the stop-then-start sequence runs in a background
        task, so any error raised while stopping or starting the plugin is not
        propagated to the caller.

        Args:
            plugin_id: The ID of the plugin to restart.
            blocking: When `True`, blocks until the plugin has stopped and started
                again. When `False` (default), schedules the restart in the background
                and returns immediately.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
            PluginNotRunningError: If `blocking` is `True` and the plugin is not running
                when the restart attempts to stop it.
            PluginStopError: If `blocking` is `True` and the plugin fails to stop.
            PluginAlreadyRunningError: If `blocking` is `True` and the plugin is already
                running when the restart attempts to start it.
            PluginStartError: If `blocking` is `True` and the plugin fails to start.
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
        """Cancels a loaded plugin by its ID.

        Args:
            plugin_id: The ID of the plugin to cancel.
            blocking: When `True`, blocks until the plugin has been cancelled. When
                `False` (default), returns immediately after cancelling the plugin.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
            PluginNotRunningError: If the plugin is not running.
        """
        plugin = self.get_plugin_by_plugin_id(plugin_id=plugin_id)
        await plugin.cancel()

        if blocking:
            await plugin.wait_until_stopped()

        self._logger.debug("Cancelled plugin: {!r}", plugin)

    @log_and_propagate_error_on_service_method
    def get_plugin_by_plugin_id(self, plugin_id: str | uuid.UUID) -> BasePlugin:
        """Returns a loaded plugin by its ID.

        Args:
            plugin_id: The ID of the plugin to retrieve.

        Returns:
            The requested plugin.

        Raises:
            PluginNotFoundError: If no plugin with the given ID is registered.
        """
        plugin = self._plugin_registry_service.get_component_by_component_id(
            component_id=plugin_id,
        )
        self._logger.debug("Retrieved plugin: {!r}", plugin)
        return plugin

    @log_and_propagate_error_on_service_method
    def get_plugins_by_label(self, label: str) -> list[BasePlugin]:
        """Returns all loaded plugins with the given label.

        Args:
            label: The label to filter by.

        Returns:
            All loaded plugins whose label matches. Empty if none match.
        """
        return self._plugin_registry_service.get_components_by_label(label=label)

    @log_and_propagate_error_on_service_method
    def get_all_plugins(self) -> list[BasePlugin]:
        """Returns a list of all plugins loaded in the service.

        Returns:
            A list of all plugins loaded in the service.
        """
        plugins = self._plugin_registry_service.get_all_components()
        self._logger.debug(
            "Retrieved all plugins ({} plugin(s) retrieved)",
            len(plugins),
        )
        return plugins
