# Server Overview

The Consortium server is the core of the framework. It hosts the services that operate on
the framework primitives and exposes them to clients over a REST API and an Events
WebSockets API. Operators drive the server through the [client](../client/client-overview.md).

## Launching the server

Start the server from the project root:

```shell
uv run consortium.py server
```

By default the server binds to the socket address `0.0.0.0:9999`, and any client with a
valid user account can then connect. Make sure the server is running before starting a
client.

## Configuration files

The server reads all of its configuration from JSON files under `data/server`. Each file
governs a different aspect of the server and has its own page in this section:

| File                    | Purpose                                                       | Reference                                                     |
|-------------------------|---------------------------------------------------------------|---------------------------------------------------------------|
| `server_config.json`    | Socket address, host allow/deny lists, and the server header. | [Server Configuration](server-configuration.md)               |
| `user_accounts.json`    | The user accounts allowed to authenticate against the server. | [User Accounts](user-accounts.md)                             |
| `role_permissions.json` | The roles and the permissions each role grants.               | [Roles and Permissions](roles-and-permissions.md)             |
| `logging_config.json`   | Log level, destination, rotation, and retention.              | [Logging](logging.md)                                         |

The server configuration and logging configuration files can be overridden at startup
with command line flags:

| Flag                        | Description                                              |
|-----------------------------|----------------------------------------------------------|
| `-s`, `--server-config`     | Path to a custom server configuration file.              |
| `-l`, `--logging-config`    | Path to a custom logging configuration file.             |
| `--debug`                   | Raise the log level to `DEBUG` for this run.             |
| `--reload`                  | Restart the server automatically when files in the framework component directories change.|

```shell
uv run consortium.py server -s path/to/server_config.json -l path/to/logging_config.json
```
