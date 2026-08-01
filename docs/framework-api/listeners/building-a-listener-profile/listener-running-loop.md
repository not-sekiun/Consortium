# Listener Running Loop

`on_running()` is the listener's main loop. The framework wraps it in an asyncio Task
immediately after `on_started()` returns, so it runs concurrently with all other server
activity.

!!! warning
    **`on_running()` must never block the event loop.** Calling `time.sleep()`, performing
    synchronous network I/O, or running any CPU-heavy loop without an `await` will stall the
    entire server for the duration of that call. Every wait must yield control back to the
    event loop with `await`.

## The server skeleton

The canonical pattern is three steps: start the server, store it on `self.environment` so
the shutdown hooks can reach it, then `await self.stop_event.wait()` to hold the hook open
until `stop()` is called.

```python
import asyncio

from consortium.framework.listeners import BaseListener


class Listener(BaseListener):

    async def on_running(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]

        async def handle_client(reader, writer):
            remote = writer.get_extra_info("peername", ("?", "?"))
            remote_addr = f"{remote[0]}:{remote[1]}"
            try:
                await self._handle_session(reader, writer, remote_addr)
            except Exception as exc:
                self.logger.warning("Session from {} aborted: {}", remote_addr, exc)
            finally:
                writer.close()

        server = await asyncio.start_server(handle_client, local_host, local_port)
        self.environment.server = server  # store for on_stopped / on_cancelled

        self.logger.info("Listening on {}:{}.", local_host, local_port)
        async with server:
            await self.stop_event.wait()  # block until stop() is called externally
```

`self.stop_event` is an `asyncio.Event` the framework sets when `stop()` is called;
awaiting it keeps `on_running()` alive without a busy loop. Store the server on
`self.environment`, never as a direct instance attribute, so the shutdown hooks can find
it without risking an `AttributeError`.

## Dispatching to the protocol handlers

The `handle_client` callback runs concurrently for each connection. Inside it, a
per-session loop reads messages and dispatches each one, by type, to a handler that
fulfils one of the three [protocol obligations](listener-protocol.md):

```python
    async def _handle_session(self, reader, writer, remote_addr):
        while True:
            line = await reader.readline()
            if not line:
                break
            message = json.loads(line)

            msg_type = message.get("type")
            if msg_type == "register":
                await self._handle_registration(message, writer, remote_addr)
            elif msg_type == "check_in":
                await self._handle_check_in(message, writer)
            elif msg_type == "result":
                await self._handle_result(message, writer)
```

Each `_handle_*` method wraps a single `self.connected_agents_service` call from
[The Agent-Listener Protocol](listener-protocol.md) and translates framework exceptions
into wire responses. Their full bodies, including error handling and JSON encoding, are in
the [Complete Listener Profile](complete-listener-profile.md).

## Per-session state

Keep all per-connection state local to the `handle_client` callback and its handlers. Do
not store session state as instance attributes. Use `self.environment` only for
listener-wide runtime state, like the server object above.

Continue to [Listener Shutdown](listener-shutdown.md) to tear the server down cleanly.
