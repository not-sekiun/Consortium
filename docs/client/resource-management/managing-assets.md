# Managing Assets

**Assets** are files uploaded to the server by an operator, for example files to be
delivered to a target through an agent capability. Assets are one of the three
repository resources managed by the `asset`, `artifact`, and `payload` commands, which
are available in every connected interpreter under the **Resource Management Commands**
group in `help`.

## Asset commands

Every asset operation is a sub-command of `asset`:

| Command                                      | Description                                   |
|----------------------------------------------|-----------------------------------------------|
| `asset list`                                 | List all assets                               |
| `asset info <resource_id>`                   | Show details of an asset                      |
| `asset upload <path>`                        | Upload an asset from a file or directory path |
| `asset download <resource_id>`               | Download an asset by its resource ID          |
| `asset rename <resource_id> <name>`          | Rename an asset                               |
| `asset describe <resource_id> <description>` | Set an asset's description                    |
| `asset remove <resource_id>`                 | Remove an asset                               |

Sub-command names and asset resource IDs tab complete, and `asset upload` completes
against local file paths to make selecting a file to upload straightforward. Each
sub-command carries its own help:

```text
asset --help           # list the available sub-commands
asset upload --help    # show the arguments and examples for one sub-command
```

## Uploading an asset

`asset upload <path>` uploads a file or an entire directory to the server as an asset.
You can attach a name and a description at upload time:

```text
asset upload ./tools/mimikatz.exe                      # upload a single file
asset upload ./tools/mimikatz.exe -d "credential tool" # upload with a description
asset upload ./tools/mimikatz.exe -n creds.exe         # upload under a different name
asset upload ./collection_directory                    # upload an entire directory
```

An asset directory is uploaded as a `.zip` archive and recorded on the server as a
directory resource.

## Downloading an asset

`asset download <resource_id>` downloads an asset from the server to the client machine.
Use `asset list` to find the resource ID and `asset info <resource_id>` to inspect an
asset before downloading it:

```text
asset download 123e4567-e89b-12d3-a456-426614174000                   # download to the current directory
asset download 123e4567-e89b-12d3-a456-426614174000 -o ./tools/x.exe  # download to a specific path
asset download 123e4567-e89b-12d3-a456-426614174000 -w                # overwrite an existing file
asset download 123e4567-e89b-12d3-a456-426614174000 -d                # decompress a downloaded asset directory
```

By default an asset directory is downloaded as a `.zip` archive. Pass `-d` (or
`--decompress`) to automatically extract asset directories after downloading.

## Renaming, describing, and removing an asset

```text
asset rename 123e4567-e89b-12d3-a456-426614174000 "new_name.exe"
asset describe 123e4567-e89b-12d3-a456-426614174000 "staged for the file server host"
asset remove 123e4567-e89b-12d3-a456-426614174000
```

An asset records the user account that uploaded it as a point-in-time reference. If that
account has since been deleted the asset remains available, and `asset info` reports the
uploading username along with the fact that the account no longer exists.

Assets are typically used alongside agent capabilities: upload a tool as an asset, then
task an agent with a capability that references it, and download any files the agent
returns as [artifacts](managing-artifacts.md). See
[Tasking Agents](../agents/tasking-agents.md).
