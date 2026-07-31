# Managing Artifacts

**Artifacts** are files produced by agents during operations and stored on the server,
for example files an agent collects from a target or output it generates while running a
capability. Unlike [assets](managing-assets.md), artifacts are not uploaded from the
client: they are created by agents, so there is no upload sub-command, only sub-commands
to list, inspect, download, rename, describe, and remove them.

Artifacts are one of the three repository resources managed by the `asset`, `artifact`,
and `payload` commands, which are available in every connected interpreter under the
**Resource Management Commands** group in `help`.

## Artifact commands

Every artifact operation is a sub-command of `artifact`:

| Command                                         | Description                             |
|-------------------------------------------------|-----------------------------------------|
| `artifact list`                                 | List all artifacts                      |
| `artifact info <resource_id>`                   | Show details of an artifact             |
| `artifact download <resource_id>`               | Download an artifact by its resource ID |
| `artifact rename <resource_id> <name>`          | Rename an artifact                      |
| `artifact describe <resource_id> <description>` | Set an artifact's description           |
| `artifact remove <resource_id>`                 | Remove an artifact                      |

Sub-command names and artifact resource IDs tab complete. Each sub-command carries its
own help:

```text
artifact --help            # list the available sub-commands
artifact download --help   # show the arguments and examples for one sub-command
```

## Inspecting an artifact

`artifact info <resource_id>` shows an artifact's details, including the agent that
produced it. Pass `-v` (or `--verbose`) to additionally display detailed information
about that agent:

```text
artifact info 123e4567-e89b-12d3-a456-42661417400       # show artifact details
artifact info 123e4567-e89b-12d3-a456-42661417400 -v    # also show producing agent details
```

The producing agent recorded on an artifact is a point-in-time reference. If that agent
has since been deleted the artifact and its details remain available, but the verbose
agent view can no longer be shown.

## Downloading an artifact

`artifact download <resource_id>` downloads an artifact from the server to the client
machine. Use `artifact list` to find the resource ID and `artifact info <resource_id>`
to inspect an artifact before downloading it:

```text
artifact download 123e4567-e89b-12d3-a456-42661417400                    # download to the current directory
artifact download 123e4567-e89b-12d3-a456-42661417400 -o ./loot/out.bin  # download to a specific path
artifact download 123e4567-e89b-12d3-a456-42661417400 -w                 # overwrite an existing file
artifact download 123e4567-e89b-12d3-a456-42661417400 -d                 # decompress a downloaded artifact directory
```

By default an artifact directory is downloaded as a `.zip` archive. Pass `-d` (or
`--decompress`) to automatically extract artifact directories after downloading.

## Renaming, describing, and removing an artifact

```text
artifact rename 123e4567-e89b-12d3-a456-42661417400 "target_hosts.txt"
artifact describe 123e4567-e89b-12d3-a456-42661417400 "collected from the file server"
artifact remove 123e4567-e89b-12d3-a456-42661417400
```

Artifacts are the counterpart to assets in the agent workflow: task an agent with a
capability, then use these sub-commands to retrieve and manage the files it produces.
See [Tasking Agents](../agents/tasking-agents.md).
