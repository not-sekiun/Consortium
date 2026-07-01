# Plugin Running Loop

`on_running()` is the plugin's main loop. The framework wraps it in an asyncio Task
immediately after `on_started()` returns. This Task runs concurrently with all other
server activity.

!!! warning
    **`on_running()` must never block the event loop.** Calling `time.sleep()`, performing
    synchronous network I/O, or any CPU-heavy loop without an `await` will stall the entire
    server for the duration of that call. Every wait must yield control back to the event
    loop with `await`.

## The stop_event pattern

`self.stop_event` is an `asyncio.Event` that the framework sets when `stop()` is called.
For a periodic loop, wait on the stop event with a timeout rather than using
`asyncio.sleep()`. This allows the plugin to respond immediately to a stop request
instead of sleeping through a full interval:

```python
async def on_running(self) -> None:
    while True:
        agents = self.services.agents_service.get_all_agents()
        self.logger.info(self._build_report(agents))
        self.environment.total_reports_emitted += 1

        try:
            await asyncio.wait_for(
                self.stop_event.wait(),
                timeout=self.environment.interval,
            )
            # stop_event was set: a stop was requested, exit the loop cleanly
            break
        except asyncio.TimeoutError:
            # The interval elapsed normally, continue to the next iteration
            pass
```

Contrast this with `asyncio.sleep()`, which would keep the plugin unresponsive to stop
requests for the full interval duration. The `stop_event.wait()` with timeout pattern is
the idiomatic choice for any periodic plugin.

For plugins that do not need a timer and simply need to stay alive until stopped (such as
`persistent_listeners` or `persistent_agent_generators`), the minimal form is:

```python
async def on_running(self) -> None:
    await self.stop_event.wait()
```

## Accessing services

`self.services` is a namespace that exposes every framework service as an attribute.
All service method calls are synchronous and return immediately:

```python
agents = self.services.agents_service.get_all_agents()
listeners = self.services.listeners_service.get_all_listeners()
generators = self.services.agent_generators_service.get_all_agent_generators()
```

Browse the available services in `consortium/server/services/`. Each file corresponds
to one service on the namespace (e.g. `agents_service.py` becomes
`self.services.agents_service`). The debug console plugin
(`consortium/components/plugins/debug_console/`) gives you live tab-completed access to
every service at runtime.

Continue to [Plugin Shutdown](plugin-shutdown.md) to handle the end of the loop.
