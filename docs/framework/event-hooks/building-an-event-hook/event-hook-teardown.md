# Event Hook Teardown

`on_teardown()` is called once when the server shuts down and the hook is being
unregistered. Use it to flush state to disk, close open connections, or perform any
final cleanup:

```python
import json

async def on_teardown(self) -> None:
    summary_path = self.event_hook_project_folder / "last_session_summary.json"
    summary = {
        str(event_type): count
        for event_type, count in self.environment.counts.items()
    }
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)
    self.logger.info("Session summary written to '{}'.", summary_path)
```

`self.event_hook_project_folder` is a `pathlib.Path` pointing to the directory that
contains your event hook's source files. Use it exactly like
`self.plugin_project_folder`
in plugins.

## Signalling teardown failures

Raise `EventHookTeardownError` from `on_teardown()` to signal that cleanup failed. This
aborts unloading: the event hook's handlers are **not** deregistered from the events
service, and the registry surfaces the failure as an `EventHookTeardownError` (from
`consortium.server.exceptions.consortium_exceptions.event_hooks_consortium_exceptions`)
carrying your `message` and any structured `detail` you provide.

```python
from consortium.framework.signal_exceptions.event_hooks_signal_exceptions import (
    EventHookTeardownError,
)


async def on_teardown(self) -> None:
    try:
        summary_path = self.event_hook_project_folder / "last_session_summary.json"
        with summary_path.open("w") as f:
            json.dump(self.environment.counts, f, indent=2)
    except OSError as exc:
        raise EventHookTeardownError(
            message=f"Failed to write session summary: {exc}",
            detail={"exception_type": type(exc).__name__},
        ) from exc
```

As with `on_setup()` and `on_triggered()`, do not catch and log teardown failures
internally, and do not let a bare exception escape unremarked: raise
`EventHookTeardownError` so the failure is reported with the same structured
`code`/`message`/`detail` shape as every other framework error.

Continue to [Event Hook Conventions](event-hook-conventions.md) for guidance on
structuring event hook code.
