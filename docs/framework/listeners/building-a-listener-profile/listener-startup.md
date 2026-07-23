# Listener Startup

`BaseListener` is where the network server lives. It inherits from `ComponentLifeCycle`
and runs through the same lifecycle hooks as a plugin. The first of those is
`on_started()`.

`on_started()` runs once, before `on_running()` is scheduled. Use it for one-time setup
and, above all, for failing fast: check that the port is free, that required files exist,
that credentials are present, before the server tries to accept connections.

```python
import socket

from consortium.framework.signal_exceptions import ListenerStartError
from consortium.framework.listeners import BaseListener


class Listener(BaseListener):

    async def on_started(self) -> None:
        local_host = self.parameters["local_host"]
        local_port = self.parameters["local_port"]
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            probe.bind((local_host, local_port))
            probe.close()
        except OSError as exc:
            raise ListenerStartError(
                f"Cannot bind to {local_host}:{local_port}: {exc}",
            ) from None
        self.logger.info("TCP JSON Listener ready on {}:{}.", local_host,
                         local_port)
```

## self.parameters

The option values an operator supplied through the template are resolved into
`self.parameters`, a name-keyed dict. Read `local_host`, `local_port`, and any other
options you declared from here. This is the same dict passed to the template's
`resolve_*` methods.

## Signalling errors: ListenerStartError

Raising `ListenerStartError` from `on_started()` aborts the start sequence cleanly: the
listener's status reverts to `INITIALIZED` and the error is surfaced to whoever called
`start()`. This is the correct way to signal that a listener cannot start.

```python
# Correct: tells the lifecycle engine to abort startup cleanly
raise ListenerStartError("Cannot bind to 0.0.0.0:4444: address already in use.")

# Incorrect: an unhandled exception transitions the listener to FATAL
raise OSError("address already in use")
```

Do not raise bare exceptions from a hook; an unhandled exception in any hook goes
straight to `FATAL`.

Continue to [Listener Running Loop](listener-running-loop.md) to start the server.
