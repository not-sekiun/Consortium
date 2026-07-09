# Managing Artifacts

**Artifacts** are files produced by agents during operations and stored on the server,
for example files an agent collects from a target or output it generates while running a
capability. Unlike [assets](managing-assets.md), artifacts are not uploaded from the
client: they are created by agents, so there is no upload command, only commands to list,
inspect, download, and remove them. Artifact commands are available in both the
[Agents interpreter](tasking-agents.md) and the Interact Agent interpreter.

## Artifact commands

| Command                 | Description                              |
|-------------------------|------------------------------------------|
| `ar-list`               | List all artifacts                       |
| `ar-info <resource_id>` | Show details of an artifact              |
| `ar-dl <resource_id>`   | Download an artifact by its resource ID  |
| `ar-rm <resource_id>`   | Remove an artifact                       |

Artifact resource IDs tab complete.

## Inspecting an artifact

`ar-info <resource_id>` shows an artifact's details, including the agent that produced
it. Pass `-v` (or `--verbose`) to additionally display detailed information about that
agent:

```text
ar-info 123e4567-e89b-12d3-a456-42661417400       # show artifact details
ar-info 123e4567-e89b-12d3-a456-42661417400 -v    # also show producing agent details
```

The producing agent recorded on an artifact is a point-in-time reference. If that agent
has since been deleted the artifact and its details remain available, but the verbose
agent view can no longer be shown.

## Downloading an artifact

`ar-dl <resource_id>` downloads an artifact from the server to the client machine. Use
`ar-list` to find the resource ID and `ar-info <resource_id>` to inspect an artifact
before downloading it:

```text
ar-dl 123e4567-e89b-12d3-a456-42661417400                    # download to the current directory
ar-dl 123e4567-e89b-12d3-a456-42661417400 -o ./loot/out.bin  # download to a specific path
ar-dl 123e4567-e89b-12d3-a456-42661417400 -d                 # decompress a downloaded artifact directory
```

By default an artifact directory is downloaded as a `.zip` archive. Pass `-d` (or
`--decompress`) to automatically extract artifact directories after downloading.

## Removing an artifact

`ar-rm <resource_id>` deletes an artifact from the server.

Artifacts are the counterpart to assets in the agent workflow: task an agent with a
capability, then use these commands to retrieve and manage the files it produces. See
[Tasking Agents](tasking-agents.md).
