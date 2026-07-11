# Listener Error Handling

## ListenerRuntimeError and on_errored

Raising `ListenerRuntimeError` from `on_running()` signals a recoverable runtime failure.
The framework transitions the listener to `ERRORED`, calls `on_errored()`, and ends the
main Task. The rest of the server keeps running.

```python
from consortium.framework.signal_exceptions import ListenerRuntimeError

raise ListenerRuntimeError("Failed to process agent request: connection reset.")
```

```python
async def on_errored(self, error) -> None:
    # The default implementation logs the error at the error level.
    # Override to add alerting, restart logic, or other custom handling.
    self.logger.error("Listener error: {}", error.message)
```

The distinction between `ListenerRuntimeError` and unhandled exceptions matters. A
`ListenerRuntimeError` is for failures you anticipate and want handled gracefully;
anything else transitions the listener straight to `FATAL` and calls `on_fatal()`
instead. Let genuinely unexpected exceptions bubble up as fatal so they stand out
clearly in the logs.

## on_fatal and ComponentLifeCycleFatalContext

Any unhandled exception that escapes `on_started()`, `on_running()`, `on_stopped()`, or
`on_cancelled()` calls `on_fatal()`. The `fatal_context` argument identifies which
lifecycle phase the exception came from:

```python
from consortium.framework._core.components import ComponentLifeCycleFatalContext


async def on_fatal(self, exc: Exception,
                   fatal_context: ComponentLifeCycleFatalContext) -> None:
    # The default logs the full traceback. Override to add a monitoring webhook
    # call, send an alert, or attempt some form of recovery.
    self.logger.error(
        "Fatal error during {}: {}: {}",
        fatal_context,
        type(exc).__name__,
        exc,
    )
```

The values of `ComponentLifeCycleFatalContext` are `START`, `RUNNING`, `STOP`, `CANCEL`,
and `ERROR` (fatal during `on_errored`). The default `on_fatal` from `BaseListener` logs
the full traceback; override it only when you need behaviour beyond logging.

Continue to [Listener Conventions](listener-conventions.md) for how to structure the
listener class.
