# Plugin Shutdown

`on_stopped()` is called when `stop()` is invoked from outside the plugin. The
stop_event
is set before `on_stopped()` is called, so any `await self.stop_event.wait()` in the
running loop will have already unblocked. Use `on_stopped()` for final cleanup: flushing
buffers, closing connections, writing final state to disk.

```python
async def on_stopped(self) -> None:
    self.logger.info(
        "Agent Report Plugin stopped after {} report(s) emitted.",
        self.environment.total_reports_emitted,
    )
```

Raise `PluginStopError` if the stop cannot complete cleanly:

```python
async def on_stopped(self) -> None:
    try:
        self._flush_pending_data()
    except IOError as exc:
        raise PluginStopError(
            message=f"Failed to flush data on stop: {exc}",
        ) from exc
```

## on_completed

`on_completed()` fires when `on_running()` returns normally without `stop()` having been
called. This is the "ran to completion" path, as opposed to the "was stopped externally"
path. Most persistent background plugins never hit `on_completed()` because their loop
runs until `stop()` is called. A plugin like `auto_updater`, which performs a single
check and exits, uses `on_completed()` to handle the post-run cleanup.

For a plugin whose loop is guarded by `stop_event`, leave `on_completed()` as a no-op:

```python
async def on_completed(self) -> None:
    pass
```

Continue to [Plugin Error Handling](plugin-error-handling.md) to handle runtime and
fatal
errors.
