# Plugin Error Handling

## PluginRuntimeError and on_errored

Raising `PluginRuntimeError` from `on_running()` signals a recoverable runtime failure.
The framework transitions the plugin to `ERRORED`, calls `on_errored()`, and ends the
main Task. The server keeps running.

```python
from consortium.framework.signal_exceptions.plugins_signal_exceptions import (
    PluginRuntimeError,
)


async def on_running(self) -> None:
    while True:
        try:
            agents = self.services.agents_service.get_all_agents()
        except Exception as exc:
            raise PluginRuntimeError(
                message=f"Failed to query agents service: {exc}",
                detail={"exception_type": type(exc).__name__},
            ) from exc

        self.logger.info(self._build_report(agents))
        ...


async def on_errored(self, error) -> None:
    # The default implementation logs the error at the error level.
    # Override to add alerting, restart logic, or other custom handling.
    self.logger.error("Plugin error: {}", error.message)
```

`detail` is an optional dict that can carry structured diagnostic data. It is attached
to the error object and surfaced by the framework's logging.

The distinction between `PluginRuntimeError` and unhandled exceptions is important.
Unhandled exceptions (anything that is not a `PluginRuntimeError`) transition the plugin
directly to `FATAL` and call `on_fatal()` instead. Use `PluginRuntimeError` for errors
you anticipate and want handled gracefully; let truly unexpected exceptions bubble up as
fatal so they are clearly distinguished in logs.

## on_fatal and ComponentLifeCycleFatalContext

Any unhandled exception that escapes `on_running()`, `on_started()`, `on_stopped()`, or
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

The values of `ComponentLifeCycleFatalContext` are `START`, `RUNNING`, `STOP`,
`CANCEL`, and `ERROR` (fatal during `on_errored`). The `persistent_listeners` plugin
delegates entirely to the default `on_fatal` implementation from `BasePlugin`, which
logs the full traceback. Override it only when you need behaviour beyond logging.

Continue to [Plugin Conventions](plugin-conventions.md) for guidance on structuring
plugin code.
