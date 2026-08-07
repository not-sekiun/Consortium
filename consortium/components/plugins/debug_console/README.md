# Debug Console Plugin

An interactive Python REPL attached to the running server, with every framework service
already in scope.

- Label: `consortium.plugins.debug_console_plugin`
- Autostart: yes
- Enabled by default: no

## What it does

The plugin opens a `prompt_toolkit` session on the server's terminal:

```
Consortium (Debug) >
```

Input is executed inside the server's own event loop, so both sync and async
expressions work directly without wrapping them in `asyncio.run`:

```
Consortium (Debug) > listeners_service.get_all_listeners()
Consortium (Debug) > await agents_service.get_agent_by_agent_id(agent_id)
```

Behaviour worth knowing:

- The globals dict is `vars(self.services)`, so every service is available by its
  attribute name (`listeners_service`, `agents_service`, `logging_service`, ...).
- Tab completion covers service names, then their public attributes and methods, tagged
  ` meth ` or ` attr ` in the completion menu.
- Non-`None` results are pretty printed with `rich`.
- Assignments persist between lines: the code runs inside a generated temporary async
  function that copies its locals back into the globals on exit.
- Starting a block statement (anything ending in `:`) drops into a multiline prompt.
  Accept it with `Meta+Enter` or `Esc` then `Enter`; cancel with `Ctrl+C`.
- Exceptions are printed as a trimmed traceback showing only the innermost frame.
- Exit with `exit` or `exit()`. This leaves the REPL only; the server keeps running and
  is still stopped with CTRL-C.

On `on_started` the plugin also swaps the server's default `stdout` log sink for a
`StdoutProxy` so that log output does not corrupt the prompt line.

## Usage

Enable it in `manifest.json`:

```json
{
    "entry_point": "plugin:Plugin",
    "enabled": true
}
```

The plugin requires both `stdin` and `stdout` to be TTYs. If either is missing,
redirected or closed, `on_started` raises `PluginStartError` naming the offending
streams rather than failing later inside the prompt loop.

## Notes

- This is a full `exec`/`eval` console over live server state with no sandboxing. It is
  a debugging tool: anyone with access to the server terminal has complete control of
  the framework. Keep it disabled outside of development.
