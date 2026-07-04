# Quick Start

## Consortium Server Quick Start

Start the server by running the following command:

```shell
uv run consortium.py server
```

This will start the server on the default socket address of `0.0.0.0:9999`. Anyone can
now attempt to connect to the server through
the [client](#consortium-client-quick-start).

### Configuring the Consortium Server

By default, the server loads its configuration information from
`data/server/server_config.json`.

You can change the `local_host` and `local_port` fields from here to specify the socket
address that you want the server to bind to.

!!! warning
    When modifying the `local_port` field in the server configuration file, ensure that
    the value being passed is an **integer**. Passing a **string** (e.g. `"9999"`) will
    result in an error.

```json hl_lines="2 3" title="server_config.json"
{
    "local_host": "0.0.0.0",
    "local_port": 9999,
    "remote_host_whitelist": [],
    "remote_host_blacklist": [],
    "server_banner": null
}
```

| Field                   | Description                                                                                           | Default Value |
|-------------------------|-------------------------------------------------------------------------------------------------------|---------------|
| `local_host`            | The local host IP address that the server will bind to.                                               | `"0.0.0.0"`   |
| `local_port`            | The local host port that the server will bind to.                                                     | `9999`        |
| `remote_host_whitelist` | A list of remote IP addresses that are allowed to connect to the server.                              | `[]`          |
| `remote_host_blacklist` | A list of remote IP addresses that are not allowed to connect to the server.                          | `[]`          |
| `server_banner`         | The server banner that is sent in the HTTP header `Server` whenever the server responds to a request. | `null`        |

To pass a custom server configuration file from another file location, use the
`-s/--server-config` flag when starting the server.

```shell
uv run consortium.py server -s path/to/custom_server_config.json
```

### Configuring the Consortium Server's User Accounts

By default, the server loads user account information from
`data/server/user_accounts.json`.

This file describes the credentials of all the user accounts that are allowed to
connect to the server over its REST API and their respective permissions.

!!! warning
    It is **highly recommended** to change the default user accounts in the user accounts
    file before deploying the server to prevent unauthorized access to the server.

These are the default user accounts that are present.

```json title="user_accounts.json"
[
    {
        "username": "admin",
        "password": "admin",
        "role": "ADMIN"
    },
    {
        "username": "operator",
        "password": "operator",
        "role": "OPERATOR"
    },
    {
        "username": "spectator",
        "password": "spectator",
        "role": "SPECTATOR"
    }
]
```

| Field      | Description                                                                                     | Restrictions                                                                                                                                                                             |
|------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `username` | The username of the user.                                                                       | - Cannot contain leading or trailing whitespace characters.<br>- Cannot be an empty string.<br>- Can only contain printable ASCII characters.<br> - Must be unique across user accounts. |
| `password` | The password of the user.                                                                       | - Cannot be an empty string.<br>- Can only contain printable ASCII characters.                                                                                                           |
| `role`     | The role of the user controlling its access to the server's REST API and Events WebSockets API. | - Can only be one of the following: `ADMIN`, `OPERATOR`, or `SPECTATOR` (in **all caps**).                                                                                               |

The `role` field determines the permissions that the user has when connecting to the
server. In general the roles have the following permissions:

| Role        | Permissions                                                                                                   |
|-------------|---------------------------------------------------------------------------------------------------------------|
| `ADMIN`     | Can perform all actions on the server.                                                                        |
| `OPERATOR`  | Can perform most actions on the server except actions that **involve managing other user accounts or users**. |
| `SPECTATOR` | Can only perform actions that **read** information from the server.                                           |

### Configuring the Consortium Server's Logging

By default, the server loads logging configuration information from
`data/server/logging_config.json`.

This file describes how the server logs its events and messages and to where. You can
modify this file to change the logging level, format, and destination of the server's
logs.

```json title="logging_config.json"
{
    "level": "INFO",
    "log_file": "data/server/logs/{time}.log",
    "rotation": null,
    "retention": 1,
    "colorize": true
}
```

| Field       | Description                                                                                                                                                                    | Default Value                   |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|
| `level`     | The minimum logging level for messages to be logged. Can be one of: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, or `SUCCESS`.                                    | `"INFO"`                        |
| `log_file`  | The file path where log files will be written. Supports dynamic placeholders like `{time}` for timestamps.                                                                     | `"data/server/logs/{time}.log"` |
| `rotation`  | The condition for rotating log files. Can be a file size (e.g., `"10 MB"`), a time period (e.g., `"1 day"`), a specific time (e.g., `"00:00"`), or `null` to disable rotation. | `null`                          |
| `retention` | The number of log files to retain before deletion, or a time period (e.g., `"1 week"`). Can be an integer or string, or `null` to keep all logs indefinitely.                  | `1`                             |
| `colorize`  | Whether to enable colorized output in the terminal/console. Set to `true` to enable colored log messages in stdout, or `false` to disable.                                     | `true`                          |

To pass a custom logging configuration file from another file location, use the
`-l/--logging-config` flag when starting the server.

```shell
uv run consortium.py server -l path/to/custom_logging_config.json
```

??? note "More on logging configuration"
Internally Consortium uses the `Loguru` logging library. For more information about
the logging configuration options, refer to the
[Loguru documentation](https://loguru.readthedocs.io/en/stable/api/logger.html#configuration).

## Consortium Client Quick Start

Start the client by running the following command **after the server** has already been
started:

```shell
uv run consortium.py client
```

This will start the client and attempt to connect to the server at the default socket
address of `127.0.0.1:9999`. Make sure the [server](#consortium-server-quick-start)
is already running before starting the client.

### Configuring the Consortium Client

By default, the client loads its configuration information from
`data/client/client_config.json`.

You can change the `remote_host` and `remote_port` fields to point towards where the
server is hosted if you are running the client and server on different machines.

!!! important
    Make sure that the `username` and `password` fields correspond to an existing user
    account in the server's `user_accounts.json` file.

```json hl_lines="4 5" title="client_config.json"
{
    "username": "admin",
    "password": "admin",
    "remote_host": "127.0.0.1",
    "remote_port": 9999
}
```

| Field         | Description                                                                        | Default Value |
|---------------|------------------------------------------------------------------------------------|---------------|
| `username`    | The username of the user that the client will use to authenticate with the server. | `"admin"`     |
| `password`    | The password of the user that the client will use to authenticate with the server. | `"admin"`     |
| `remote_host` | The remote host IP address that the client will connect to.                        | `"127.0.0.1"` |
| `remote_port` | The remote host port that the client will connect to.                              | `9999`        |

To pass a custom client configuration file from another file location, use the
`-c/--config` flag when starting the client.

```shell
uv run consortium.py client -c path/to/custom_client_config.json
```

### Starting the Consortium Client in Disconnected Mode.

If the client fails to connect to the server at startup, it will start in the
_disconnected_ mode.

To attempt to connect to a server, use the `connect` command. This command
allows you to attempt to connect using the default client configuration file or a
custom client configuration file.

```shell
Consortium > connect -c path/to/custom_client_config.json
Consortium > connect -c  # Connect using the default client configuration file at `data/client/client_config.json`.
```

Here we can just attempt to connect to a server using the default client configuration
file (assuming the server has already been started).

```plaintext
Consortium > connect -c
[+] Successfully logged into server 127.0.0.1:9999 as 'admin'.
```

Alternatively you can manually provide the fields required to connect to the server.

```plaintext
Consortium > connect -u admin -p admin -rh 127.0.0.1 -rp 9999
[+] Successfully logged into server 127.0.0.1:9999 as 'admin'.
```

!!! tip
    You can use the `connect -h/--help` command to get more information about the
    arguments that the `connect` command takes. In general, all commands in the client
    support the `-h/--help` flag to display help information.

After you have successfully connected to the server a new client session will be
present representing a connection to a particular server. List all available client
sessions with the `list_client_sessions` command.

!!! info
    A _client session_ represents a particular connection to a valid instance of a
    Consortium server. The client supports connecting multiple client sessions at once
    as well as switching to different ones on the fly.

```plaintext
Consortium > list_client_sessions
                              Client Sessions
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Client Session ID                    ┃ Name ┃ Remote Host ┃ Remote Port ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 43fdb768-486c-4159-aaf4-366d41829222 │      │ 127.0.0.1   │ 9999        │
└──────────────────────────────────────┴──────┴─────────────┴─────────────┘
```

To interact with the newly created client session use the `interact_client_session`
command with the client session ID being passed in as an argument.

!!! tip
    You can press `tab` to autocomplete _commands_ and _certain arguments_ that those
    commands take. Pressing `tab` without any input to the interpreter prompt will cycle
    through all available commands for the current interpreter context.

```shell
Consortium (Home) > interact_client_session 43fdb768-486c-4159-aaf4-366d41829222
[+] Interacting with client session '' (43fdb768-486c-4159-aaf4-366d41829222)
```

All in all, the process of starting the client in disconnected mode and connecting to a
server is demonstrated below.

<div id="disconnected-interpreter-demo"></div>
<script>
  document$.subscribe(function(){
    var el = document.getElementById("disconnected-interpreter-demo");
    if (el && !el.hasChildNodes()) {
      AsciinemaPlayer.create(
        "/asciinema/disconnected_interpreter_demo.cast",
        el,
        {theme: 'gruvbox-dark', autoPlay: true, loop: false},
      );
    }
  });
</script>

For more information about using the client, refer to the [Client section of the
Manual](../client/client-overview.md).
