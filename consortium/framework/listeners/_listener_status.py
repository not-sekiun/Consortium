# from enum import StrEnum
#
# from consortium.server.exceptions.framework_exceptions.listeners_framework_exceptions import (
#     ListenerRuntimeError,
# )
#
#
# class ListenerState(StrEnum):
#     """
#     An `enum.StrEnum` object that represents the state of a listener as a string in all
#     capital letters. This object is accessed as part of the [`ListenerStatus`][consortium.server.objects.listener_objects.ListenerStatus] object
#     that is in turn part of the [`BaseListener`][consortium.framework.listeners.BaseListener] object as its
#     [`status`][consortium.framework.listeners.BaseListener.status] instance
#     attribute.
#
#     Attributes:
#         INITIALIZED: The listener has been initialized and created from its constructor
#             method either through its corresponding listener template or by manually
#             creating the listener.
#         STARTED: The listener has been started through calling its [`start_listener()`][consortium.framework.listeners.base_listener.BaseListener.start_listener]
#             method. Whether the listener successfully starts or not is still not yet
#             known because a [`ListenerStartError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerStartError]
#             may be thrown at this point.
#         RUNNING: The listener is running after its [`start_listener()`][consortium.framework.listeners.BaseListener.start_listener]
#             method has run to completion without raising any exceptions.
#         STOPPED: The listener has been stopped gracefully after a call was made to its
#             [`stop_listener()`][consortium.framework.listeners.base_listener.BaseListener.stop_listener]
#             method. The [`on_listener_stop()'][consortium.framework.listeners.base_listener.BaseListener.on_listener_stop]
#             method has also been run to completion without raising any exceptions. The
#             listener's main runtime method
#             [`on_listener_running()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_running]
#             has also been run to completion without raising any exceptions.
#         CANCELLED: The listener has been stopped forcefully through a call to its
#             [`cancel_listener()`][consortium.framework.listeners.base_listener.BaseListener.cancel_listener]
#             method. The listener's main runtime method has exited prematurely by
#             throwing an `asyncio.CancelledError` into its main runtime loop.
#         ERRORED: The listener has errored at some point through its main runtime loop
#             [`on_listener_running()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_running]
#             method. The listener's main runtime method has exited prematurely by
#             having a [`ListenerRuntimeError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerRuntimeError]
#             be raised.
#         FATAL: The listener has fatally errored at some point through its main runtime
#             loop [`on_listener_running()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_running]
#             method. The difference between this state and the `ERRORED` state is that
#             the particular error that caused the listener to fatally error was not
#             caught and handled by the listener's main runtime loop.
#     """
#
#     INITIALIZED = "INITIALIZED"
#     """
#     The listener has been initialized and created from its constructor method either
#     through its corresponding listener template or by manually creating the listener.
#     """
#     STARTED = "STARTED"
#     """
#     The listener has been started through calling its
#     [`start_listener()`][consortium.framework.listeners.base_listener.BaseListener.start_listener]
#     method. Whether the listener successfully starts or not is still not yet known
#     because a [`ListenerStartError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerStartError]
#     may be thrown at this point.
#     """
#     RUNNING = "RUNNING"
#     """
#     The listener is running after its [`start_listener()`][consortium.framework.listeners.base_listener.BaseListener.start_listener]
#     method has run to completion without raising any exceptions.
#     """
#     STOPPED = "STOPPED"
#     """
#     The listener has been stopped gracefully after a call was made to its
#     [`stop_listener()`][consortium.framework.listeners.base_listener.BaseListener.stop_listener]
#     method. The [`on_listener_stopped()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_stopped]
#     method has also been run to completion without raising any exceptions. The
#     listener's main runtime method [`on_listener_running()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_running]
#     has also been run to completion without raising any exceptions.
#     """
#     CANCELLED = "CANCELLED"
#     """
#     The listener has been stopped forcefully through a call to its [`cancel_listener()`][consortium.framework.listeners.base_listener.BaseListener.cancel_listener]
#     method. The listener's main runtime method has exited prematurely by throwing an
#     [asyncio.CancelledError] into its main runtime loop.
#     """
#     ERRORED = "ERRORED"
#     """
#     The listener has errored at some point through its main runtime
#     [`on_listener_running()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_running]
#     method. The listener's main runtime method has exited prematurely by having a
#     [`ListenerRuntimeError`][consortium.framework.exceptions.listeners_framework_exceptions.ListenerRuntimeError]
#     be raised.
#     """
#     FATAL = "FATAL"
#     """
#     The listener has fatally errored at some point through its main runtime
#     [`on_listener_running()`][consortium.framework.listeners.base_listener.BaseListener.on_listener_running]
#     method. The difference between this state and the `ERRORED` state is that the
#     particular error that caused the listener to fatally error was not caught and
#     handled by the listener's main runtime loop.
#     """
#
#
# class ListenerStatus:
#     """
#     An object that represents the status of a listener. This object encapsulates both
#     the [`state`][consortium.framework.listeners._listener_status.ListenerState] of the
#     listener as well as any other additional error information that may be present when
#     the [`state`][consortium.framework.listeners._listener_status.ListenerState] object is
#     in the `ERRORED` or `FATAL` states. This object is accessed as part of the
#     [BaseListener][consortium.framework.listeners.base_listener.BaseListener] object.
#     """
#
#     def __init__(self):
#         self.state = ListenerState.INITIALIZED
#         self.exception = None
#
#     def __str__(self) -> str:
#         if self.exception is None:
#             return f"{self.state}"
#         else:
#             return f"{self.state}: {self.exception}"
#
#     def __repr__(self) -> str:
#         if self.exception is None:
#             return f"!r{self.state}"
#         else:
#             return f"!r{self.state}: {self.exception}"
#
#     def to_json(self) -> dict[str, str | None]:
#         """
#         Convert the listener status object to a dictionary representation that can be
#         serialized to JSON.
#
#         Returns:
#             dict[str, str | None]: A dictionary representation of the listener status
#                 object that can be serialized to JSON.
#         """
#         # Internally the identifier "exception" is more representative of what is stored
#         # here. In the API we want to expose this as "error" instead to align the naming
#         # convention with other parts of the api that use "error" instead of "exception"
#         return {
#             "state": str(self.state),
#             "error": self.exception.to_json() if self.exception else None,
#         }
#
#     def _transition_to_initialized(self) -> None:
#         self.state = ListenerState.INITIALIZED
#         self.exception = None
#
#     def _transition_to_started(self) -> None:
#         self.state = ListenerState.STARTED
#         self.exception = None
#
#     def _transition_to_running(self) -> None:
#         self.state = ListenerState.RUNNING
#         self.exception = None
#
#     def _transition_to_stopped(self) -> None:
#         self.state = ListenerState.STOPPED
#         self.exception = None
#
#     def _transition_to_cancelled(self) -> None:
#         self.state = ListenerState.CANCELLED
#         self.exception = None
#
#     def _transition_to_errored(self, exception: ListenerRuntimeError) -> None:
#         self.state = ListenerState.ERRORED
#         self.exception = exception
#
#     def _transition_to_fatal(self, listener: str, exception: Exception) -> None:
#         self.state = ListenerState.FATAL
#         self.exception = ListenerRuntimeError(
#             listener_str=listener,
#             error_message=f"{type(exception).__name__}: {exception}",
#             detail={
#                 "type": type(exception).__name__,
#                 "message": str(exception),
#             },
#         )
