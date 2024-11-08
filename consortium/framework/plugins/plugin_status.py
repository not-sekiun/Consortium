from enum import StrEnum

from consortium.framework.plugins.exceptions import PluginRuntimeError


class PluginState(StrEnum):
    """
    The current state of the plugin.

    Attributes:
        INITIALIZED:
            The plugin has been initialized and created from its constructor.
        STARTED:
            The plugin has been started through calling its [`start()`][consortium.framework.plugins.BaseListener.start_listener]
            method. Whether the listener successfully starts or not is still not yet
            known because a [`ListenerStartError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerStartError]
            may be thrown at this point.
        RUNNING: The listener is running after its [`start_listener()`][consortium.framework.listeners.BaseListener.start_listener]
            method has run to completion without raising any exceptions.
        STOPPED: The listener has been stopped gracefully after a call was made to its
            [`stop_listener()`][consortium.framework.base_listener.BaseListener.stop_listener]
            method. The [`on_listener_stop()'][consortium.framework.base_listener.BaseListener.on_listener_stop]
            method has also been run to completion without raising any exceptions. The
            listener's main runtime method
            [`on_listener_running()`][consortium.framework.base_listener.BaseListener.on_listener_running]
            has also been run to completion without raising any exceptions.
        CANCELLED: The listener has been stopped forcefully through a call to its
            [`cancel_listener()`][consortium.framework.base_listener.BaseListener.cancel_listener]
            method. The listener's main runtime method has exited prematurely by
            throwing an `asyncio.CancelledError` into its main runtime loop.
        ERRORED: The listener has errored at some point through its main runtime loop
            [`on_listener_running()`][consortium.framework.base_listener.BaseListener.on_listener_running]
            method. The listener's main runtime method has exited prematurely by
            having a [`ListenerRuntimeError`][consortium.framework.exceptions.listener_framework_exceptions.ListenerRuntimeError]
            be raised.
        FATAL: The listener has fatally errored at some point through its main runtime
            loop [`on_listener_running()`][consortium.framework.base_listener.BaseListener.on_listener_running]
            method. The difference between this state and the `ERRORED` state is that
            the particular error that caused the listener to fatally error was not
            caught and handled by the listener's main runtime loop.
    """
    INITIALIZED = "INITIALIZED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    ERRORED = "ERRORED"
    FATAL = "FATAL"


class PluginStatus:
    """
    The current status of the plugin.

    Attributes:
        state (PluginState):
            The current state of the plugin
        exception (Exception | None):
            The exception that caused the plugin to transition to the `ERRORED` or
            `FATAL` state. This is `None` if the plugin is not either of the
            aforementioned states. The `exception` can only be a PluginRuntimeError
            when the state is `ERRORED` indicating an intentionally thrown plugin
            runtime error. If it is the `FATAL` state, the exception can be any
            exception type indicating an unhanded exception that caused the plugin
            to fail.
    """

    _VALID_PLUGIN_STATE_TRANSITIONS = {
        PluginState.INITIALIZED: {PluginState.STARTED},
        PluginState.STARTED: {
            PluginState.RUNNING,
            PluginState.ERRORED,
        },
        PluginState.RUNNING: {
            PluginState.STOPPED,
            PluginState.CANCELLED,
            PluginState.ERRORED,
            PluginState.FATAL,
        },
        PluginState.STOPPED: {
            PluginState.STARTED,
        },
        PluginState.CANCELLED: {
            PluginState.STARTED,
        },
        PluginState.ERRORED: {
            PluginState.STARTED,
        },
        PluginState.FATAL: {
            PluginState.STARTED,
        },
    }

    def __init__(self):
        self.state = PluginState.INITIALIZED
        self.exception = None

    def to_json(self) -> dict[str, str | dict[str, str] | None]:
        """
        Returns the plugin status as a JSON-compatible dictionary.

        Returns:
            The plugin status as a JSON-compatible dictionary.
        """
        if isinstance(self.exception, PluginRuntimeError):
            error_json_object = self.exception.to_json()
        elif isinstance(self.exception, Exception):
            error_json_object = {
                "type": type(self.exception).__name__,
                "message": str(self.exception),
            }
        else:
            error_json_object = None
        # Internally the identifier "exception" is more representative of what is stored
        # here. In the API we want to expose this as "error" instead to align the naming
        # convention with other parts of the api that use "error" instead of "exception"
        return {
            "state": str(self.state),
            "error": error_json_object,
        }


    def _transition_to_state(
        self,
        plugin_state: PluginState,
        exception: Exception | None = None,
    ) -> None:
        if plugin_state not in self._VALID_PLUGIN_STATE_TRANSITIONS[self.state]:
            assert False, (
                f"Invalid state transition from current plugin state '{self.state}' to "
                f"new plugin state '{plugin_state}'"
            )

        self.state = plugin_state
        self.exception = exception

    def _transition_to_initialized(self) -> None:
        self._transition_to_state(
            plugin_state=PluginState.INITIALIZED
        )

    def _transition_to_started(self) -> None:
        self._transition_to_state(
            plugin_state=PluginState.STARTED
        )

    def _transition_to_running(self) -> None:
        self._transition_to_state(
            plugin_state=PluginState.RUNNING
        )

    def _transition_to_stopped(self) -> None:
        self._transition_to_state(
            plugin_state=PluginState.STOPPED
        )

    def _transition_to_cancelled(self) -> None:
        self._transition_to_state(
            plugin_state=PluginState.CANCELLED
        )

    def _transition_to_errored(self, exception: PluginRuntimeError) -> None:
        self._transition_to_state(
            plugin_state=PluginState.ERRORED,
            exception=exception,
        )

    def _transition_to_fatal(self, exception: Exception) -> None:
        self._transition_to_state(
            plugin_state=PluginState.FATAL,
            exception=exception,
        )
