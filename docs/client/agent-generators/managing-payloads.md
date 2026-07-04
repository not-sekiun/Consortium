# Managing Payloads

A **payload** is the concrete artifact an agent generator produces: the thing you
deliver
to a target so that it runs and checks in as an agent. Payloads are managed from the
[Generators interpreter](setting-up-agent-generators.md).

## Payload commands

| Command                | Description                           |
|------------------------|---------------------------------------|
| `pl-list`              | List all payloads                     |
| `pl-info <payload_id>` | Show details of a payload             |
| `pl-dl <payload_id>`   | Download a payload by its resource ID |
| `pl-rm <payload_id>`   | Remove a payload                      |

Payload IDs tab complete, and the list stays current as generators produce or remove
payloads (the interpreter subscribes to `PAYLOAD_CREATED` and `PAYLOAD_DELETED` events).

## Downloading a payload

`pl-dl <payload_id>` downloads a payload to the client machine. Some payloads are
produced
as a directory rather than a single file. For those, pass `--decompress` to
automatically
decompress the downloaded payload directory:

```text
pl-dl a1b2c3d4-...               # download the payload
pl-dl a1b2c3d4-... --decompress  # download and decompress a payload directory
```

## Where payloads come from

Payloads are produced when an agent generator runs. To create one:

1. Configure an agent template and create a generator, as described in
   [Using Agent Templates](using-agent-templates.md).
2. Start the generator (this happens automatically unless you passed `--no-start` to
   `create`).
3. Find the resulting payload with `pl-list` and download it with `pl-dl`.

Once delivered and executed on a target, the payload connects back through its
compatible
listener and the agent appears in the [Agents interpreter](../agents/tasking-agents.md),
ready to be tasked.
