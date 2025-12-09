# from enum import StrEnum
#
# from consortium.server.exceptions.framework_exceptions.plugins_framework_exceptions import (
#     PluginRuntimeError,
# )
#
#
# class PluginState(StrEnum):
#     """
#     The current state of the plugin.
#
#     Attributes:
#         INITIALIZED:
#             The plugin has been initialized and created from its constructor.
#         STARTED:
#             The plugin has been started through calling its
#             [`start()`][consortium.framework.plugins.BasePlugin.start_plugin]
#             method. Whether the plugin successfully starts or not is still not yet
#             known because a
#             [`PluginStartError`][consortium.framework.exceptions.plugins_framework_exceptions.PluginStartError]
#             may be thrown at this point.
#         RUNNING: The plugin is running after its
#             [`start_plugin()`][consortium.framework.plugins.BasePlugin.start_plugin]
#             method has run to completion without raising any exceptions.
#         STOPPING: The plugin is in the process of stopping after a call was made to its
#             [`stop_plugin()`][consortium.framework.base_plugin.BasePlugin.stop_plugin]
#             method.
#         STOPPED: The plugin has been stopped gracefully after a call was made to its
#             [`stop_plugin()`][consortium.framework.base_plugin.BasePlugin.stop_plugin]
#             method. The
#             [`on_plugin_stop()'][consortium.framework.base_plugin.BasePlugin.on_plugin_stop]
#             method has also been run to completion without raising any exceptions. The
#             plugin's main runtime method
#             [`on_plugin_running()`][consortium.framework.base_plugin.BasePlugin.on_plugin_running]
#             has also been run to completion without raising any exceptions.
#         CANCELLED: The plugin has been stopped forcefully through a call to its
#             [`cancel_plugin()`][consortium.framework.base_plugin.BasePlugin.cancel_plugin]
#             method. The plugin's main runtime method has exited prematurely by
#             throwing an `asyncio.CancelledError` into its main runtime loop.
#         ERRORED: The plugin has errored at some point through its main runtime loop
#             [`on_plugin_running()`][consortium.framework.base_plugin.BasePlugin.on_plugin_running]
#             method. The plugin's main runtime method has exited prematurely by
#             having a
#             [`PluginRuntimeError`][consortium.framework.exceptions.plugin_framework_exceptions.PluginRuntimeError]
#             be raised.
#         FATAL: The plugin has fatally errored at some point through its main runtime
#             loop
#             [`on_plugin_running()`][consortium.framework.base_plugin.BasePlugin.on_plugin_running]
#             method. The difference between this state and the `ERRORED` state is that
#             the particular error that caused the plugin to fatally error was not
#             caught and handled by the plugin's main runtime loop.
#     """
#
#     INITIALIZED = "INITIALIZED"
#     STARTED = "STARTED"
#     RUNNING = "RUNNING"
#     STOPPING = "STOPPING"
#     STOPPED = "STOPPED"
#     CANCELLED = "CANCELLED"
#     ERRORED = "ERRORED"
#     FATAL = "FATAL"
#
#
# class PluginStatus:
#     """
#     The current status of the plugin.
#
#     Attributes:
#         state (PluginState):
#             The current state of the plugin
#         error (PluginRuntimeError | None):
#             The error that caused the plugin to transition to the `ERRORED` or
#             `FATAL` state. This is `None` if the plugin is not either of the
#             aforementioned states. The `error` will always be a PluginRuntimeError
#             object.
#     """
#
#     _VALID_PLUGIN_STATE_TRANSITIONS = {
#         PluginState.INITIALIZED: {PluginState.STARTED},
#         PluginState.STARTED: {
#             PluginState.RUNNING,
#             PluginState.ERRORED,
#         },
#         PluginState.RUNNING: {
#             PluginState.STOPPED,
#             PluginState.CANCELLED,
#             PluginState.ERRORED,
#             PluginState.FATAL,
#         },
#         PluginState.STOPPED: {
#             PluginState.STARTED,
#         },
#         PluginState.CANCELLED: {
#             PluginState.STARTED,
#         },
#         PluginState.ERRORED: {
#             PluginState.STARTED,
#         },
#         PluginState.FATAL: {
#             PluginState.STARTED,
#         },
#     }
#
#     def __init__(self):
#         self.state = PluginState.INITIALIZED
#         self.error = None
#
#     def to_json(self) -> dict[str, str | dict[str, str] | None]:
#         """
#         Returns the plugin status as a JSON-compatible dictionary.
#
#         Returns:
#             The plugin status as a JSON-compatible dictionary.
#         """
#         return {
#             "state": str(self.state),
#             "error": self.error.to_json()
#             if isinstance(self.error, PluginRuntimeError)
#             else None,
#         }
#
#     def _transition_to_state(
#         self,
#         plugin_state: PluginState,
#         error: PluginRuntimeError | None = None,
#     ) -> None:
#         if plugin_state not in self._VALID_PLUGIN_STATE_TRANSITIONS[self.state]:
#             raise AssertionError(
#                 f"Invalid state transition from current plugin state '{self.state}' to "
#                 f"new plugin state '{plugin_state}'"
#             )
#
#         self.state = plugin_state
#         self.error = (
#             error if plugin_state in {PluginState.ERRORED, PluginState.FATAL} else None
#         )
#
#     def _transition_to_initialized(self) -> None:
#         self._transition_to_state(plugin_state=PluginState.INITIALIZED)
#
#     def _transition_to_started(self) -> None:
#         self._transition_to_state(plugin_state=PluginState.STARTED)
#
#     def _transition_to_running(self) -> None:
#         self._transition_to_state(plugin_state=PluginState.RUNNING)
#
#     def _transition_to_stopped(self) -> None:
#         self._transition_to_state(plugin_state=PluginState.STOPPED)
#
#     def _transition_to_cancelled(self) -> None:
#         self._transition_to_state(plugin_state=PluginState.CANCELLED)
#
#     def _transition_to_errored(self, error: PluginRuntimeError) -> None:
#         self._transition_to_state(
#             plugin_state=PluginState.ERRORED,
#             error=error,
#         )
#
#     def _transition_to_fatal(self, plugin_str: str, exception: Exception) -> None:
#         self._transition_to_state(
#             plugin_state=PluginState.FATAL,
#             error=PluginRuntimeError(
#                 plugin_str=plugin_str,
#                 error_message=f"{type(exception).__name__}: {exception}",
#                 detail={
#                     "type": type(exception).__name__,
#                     "message": str(exception),
#                 },
#             ),
#         )
