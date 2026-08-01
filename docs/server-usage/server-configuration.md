# Server Configuration

By default, the server loads its configuration from `data/server/server_config.json`. This
file controls the socket address the server binds to, which remote hosts are allowed or
denied, and the value sent in the `Server` HTTP header.

Change the `local_host` and `local_port` fields to specify the socket address the server
should bind to.

!!! warning
    The `local_port` field must be an **integer**. Passing a **string** (e.g. `"9999"`)
    will result in an error.

```json hl_lines="2 3" title="server_config.json"
{
    "local_host": "0.0.0.0",
    "local_port": 9999,
    "remote_host_whitelist": [],
    "remote_host_blacklist": [],
    "server_header": null
}
```

| Field                   | Description                                                                           | Default Value |
|-------------------------|---------------------------------------------------------------------------------------|---------------|
| `local_host`            | The local host IP address that the server will bind to.                               | `"0.0.0.0"`   |
| `local_port`            | The local host port that the server will bind to.                                     | `9999`        |
| `remote_host_whitelist` | A list of remote IP addresses that are allowed to connect to the server.              | `[]`          |
| `remote_host_blacklist` | A list of remote IP addresses that are not allowed to connect to the server.          | `[]`          |
| `server_header`         | The value sent in the HTTP header `Server` whenever the server responds to a request. | `null`        |

To load a server configuration file from a different location, use the `-s/--server-config`
flag when starting the server.

```shell
uv run consortium.py server -s path/to/custom_server_config.json
```
