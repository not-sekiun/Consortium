# Listener Shutdown

`on_stopped()` is called when `stop()` is invoked from outside the listener. The
stop_event is set before `on_stopped()` runs, so the `await self.stop_event.wait()` in
the running loop will have already unblocked. Use `on_stopped()` to tear down what
`on_running()` started: close the server, drain connections, release the port.

```python
    async def on_stopped(self) -> None:


    if hasattr(self.environment, "server"):
        self.environment.server.close()
        await self.environment.server.wait_closed()
self.logger.info("TCP JSON Listener stopped.")
```

## on_cancelled

`on_cancelled()` runs when the listener is cancelled rather than stopped normally. It
should release the same resources as `on_stopped()`, but it may run before `on_running()`
finished initialising, so guard attribute access with `hasattr`:

```python
    async def on_cancelled(self) -> None:
        # stop() may have been called before on_running() stored the server
        if hasattr(self.environment, "server"):
            self.environment.server.close()
```

That guard is the practical reason runtime state lives on `self.environment` rather than
directly on `self`: a cancellation mid-startup can reach the shutdown hooks before the
server object exists, and the `hasattr` check keeps that case simple.

Continue to [Listener Error Handling](listener-error-handling.md) for runtime and fatal
errors.
