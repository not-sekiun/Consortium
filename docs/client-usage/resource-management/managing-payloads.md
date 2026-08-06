# Managing Payloads

A **payload** is the concrete artifact an agent generator produces: the thing you
deliver to a target so that it runs and checks in as an agent. Payloads are one of the
three repository resources managed by the `asset`, `artifact`, and `payload` commands,
which are available in every connected interpreter under the **Resource Management
Commands** group in `help`.

## Payload commands

Every payload operation is a sub-command of `payload`:

| Command                                       | Description                           |
|-----------------------------------------------|---------------------------------------|
| `payload list`                                | List all payloads                     |
| `payload info <payload_id>`                   | Show details of a payload             |
| `payload download <payload_id>`               | Download a payload by its resource ID |
| `payload rename <payload_id> <name>`          | Rename a payload                      |
| `payload describe <payload_id> <description>` | Set a payload's description           |
| `payload remove <payload_id>`                 | Remove a payload                      |

Sub-command names and payload IDs tab complete, and the completions stay current as
generators produce or remove payloads (every connected interpreter subscribes to the
`PAYLOAD_CREATED` and `PAYLOAD_DELETED` events, along with the equivalent asset and
artifact events). Each sub-command carries its own help:

```text
payload --help            # list the available sub-commands
payload download --help   # show the arguments and examples for one sub-command
```

## Inspecting a payload

`payload info <payload_id>` shows the payload's resource details along with the build
parameters it was produced with and a summary of the agent template that produced it.
Pass `-v` (or `--verbose`) to display the full agent template including all of its
options:

```text
payload info a1b2c3d4-...       # show payload details and a template summary
payload info a1b2c3d4-... -v    # also show the full agent template and its options
```

The agent template recorded on a payload is a point-in-time reference. If the template
has since been removed the payload remains available and its details still list the
template's label and name.

## Downloading a payload

`payload download <payload_id>` downloads a payload to the client machine. Some payloads
are produced as a directory rather than a single file. For those, pass `--decompress` to
automatically decompress the downloaded payload directory:

```text
payload download a1b2c3d4-...               # download the payload
payload download a1b2c3d4-... --decompress  # download and decompress a payload directory
payload download a1b2c3d4-... -o ./out.exe  # download to a specific path
payload download a1b2c3d4-... -w             # overwrite an existing file
```

A payload's name is whatever it was built or renamed as, extension included, and it is the
name the download is saved under when `-o` is not given (with `.zip` appended for a payload
directory). The server stores the file itself under the payload's resource ID, so the name
is free to be anything: it never has to match what is on disk.

## Where payloads come from

Payloads are produced when an agent generator runs. To create one:

1. Configure an agent template and create a generator, as described in
   [Using Agent Templates](../agent-generators/using-agent-templates.md).
2. Start the generator (this happens automatically unless you passed `--no-start` to
   `create`).
3. Find the resulting payload with `payload list` and download it with
   `payload download`.

Once delivered and executed on a target, the payload connects back through its
compatible listener and the agent appears in the
[Agents interpreter](../agents/tasking-agents.md), ready to be tasked.
