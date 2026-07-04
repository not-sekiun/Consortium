# Managing Assets

**Assets** are files exchanged with the server as part of operating against agents, for
example files uploaded to be delivered to a target or files retrieved from one. Asset
commands are available in both the [Agents interpreter](tasking-agents.md) and the
Interact
Agent interpreter.

## Asset commands

| Command                 | Description                                   |
|-------------------------|-----------------------------------------------|
| `as-list`               | List all assets                               |
| `as-info <resource_id>` | Show details of an asset                      |
| `up <path>`             | Upload an asset from a file or directory path |
| `as-dl <resource_id>`   | Download an asset by its resource ID          |
| `as-rm <resource_id>`   | Remove an asset                               |

Asset resource IDs tab complete. The `up` command completes against local file paths to
make selecting a file to upload straightforward.

## Uploading an asset

`up <path>` uploads a file or an entire directory to the server as an asset. You can
attach
a description at upload time:

```text
up ./tools/mimikatz.exe                      # upload a single file
up ./tools/mimikatz.exe -d "credential tool" # upload with a description
up ./collection_directory                    # upload an entire directory
```

## Downloading an asset

`as-dl <resource_id>` downloads an asset from the server to the client machine. Use
`as-list` to find the resource ID and `as-info <resource_id>` to inspect an asset before
downloading it.

Assets are typically used alongside agent capabilities: upload a tool as an asset, then
task an agent with a capability that references it, and download any files the agent
returns. See [Tasking Agents](tasking-agents.md).
