# Quick Start

## Consortium Server Quick Start

Start the server by running the following command:

```shell
poetry run python consortium.py server
```

This will start the server on the default socket address of `0.0.0.0:9999`.
### Configuring the Consortium Server

You can change the default socket address by modifying the server's default
configuration file at `data/server/server_config.json`. Change the `local_host` and
`local_port` fields to specify the socket address that you want the server to bind to.

!!! important
    When modifying the `local_port` field in the server configuration file, ensure that
    the value being passed is an **integer**. Passing a **string** (e.g. `"9999"`) will
    result in an error.

```json hl_lines="2 3" title="server_config.json"
{
    "local_host": "0.0.0.0",
    "local_port": 9999,
    "remote_host_whitelist": [],
    "remote_host_blacklist": [],
    "server_banner": "Apache",
    "log_level": "INFO"
}
```

All of the server's configuration options are meant to be set from here. The following
table describes each field in the server configuration file:

| Field                   | Description                                                                                                                                                                                                               | Default Value |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| `local_host`            | The local host IP address that the server will bind to.                                                                                                                                                                   | `"0.0.0.0"`   |
| `local_port`            | The local host port that the server will bind to.                                                                                                                                                                         | `9999`        |
| `remote_host_whitelist` | A list of remote IP addresses that are allowed to connect to the server.                                                                                                                                                  | `[]`          |
| `remote_host_blacklist` | A list of remote IP addresses that are not allowed to connect to the server.                                                                                                                                              | `[]`          |
| `server_banner`         | The server banner that is sent in the HTTP header `Server` whenever the server responds to a request.                                                                                                                     | `"Apache"`    |
| `log_level`             | The logging level that the server will use when outputting to the console. Note that this value can be overriden by passing in the `-d/--debug` flag when starting the server which will set its logging level to `DEBUG` | `"INFO"`      |

It is possible to create your own configuration file and pass it to the server using the
`-c/--config` flag when starting the server. The configuration file must be a JSON file
that follows the same structure as the default configuration file.

```shell
poetry run python consortium.py server -c path/to/custom_server_config.json
```

### Configuring the Consortium Server's User Accounts

The server's user accounts are stored in the `data/server/user_accounts.json` file. This
file describes all the users that are allowed to connect to the server over its REST API
and those users respective permissions. These are the default user accounts that are
present:

!!! warning
    It is highly recommended to change the default user accounts in the user accounts
    file before deploying the server to prevent unauthorized access to the server.

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

The following table describes each field in the user accounts file:

| Field      | Description                                                                                     | Restrictions                                                                                                                                                                             |
|------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `username` | The username of the user.                                                                       | - Cannot contain leading or trailing whitespace characters.<br>- Cannot be an empty string.<br>- Can only contain printable ASCII characters.<br> - Must be unique across user accounts. |
| `password` | The password of the user.                                                                       | - Cannot be an empty string.<br>- Can only contain printable ASCII characters.                                                                                                           |
| `role`     | The role of the user controlling its access to the server's REST API and Events WebSockets API. | - Can only be one of the following: `ADMIN`, `OPERATOR`, or `SPECTATOR` (in **all caps**).                                                                                                   |

The `role` field determines the permissions that the user has when connecting to the
server. In general the roles have the following permissions:

| Role        | Permissions                                                                                               |
|-------------|-----------------------------------------------------------------------------------------------------------|
| `ADMIN`     | Can perform all actions on the server.                                                                    |
| `OPERATOR`  | Can perform most actions on the server except actions that involve managing other user accounts or users. |
| `SPECTATOR` | Can only perform actions that read information from the server.                                           |

## Consortium Client Quick Start

Start the client by running the following command after the server has already been
started:

```shell
poetry run python consortium.py server
```

This will start the client and attempt to connect to the server at the default socket
address of `127.0.0.1:9999`.

### Configuring the Consortium Client
You can change the default socket address that the client attemtps to connect to by
modifying the client's default configuration file at `data/client/client_config.json`.
Change the `remote_host` and `remote_port` fields to point towards where the server is
hosted.

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

Similar to the server, all of the client's configuration options are meant to be set
from here. The following table describes each field in the client configuration file:

| Field         | Description                                                                        | Default Value  |
|---------------|------------------------------------------------------------------------------------|----------------|
| `username`    | The username of the user that the client will use to authenticate with the server. | `"admin"`      |
| `password`    | The password of the user that the client will use to authenticate with the server. | `"admin"`      |
| `remote_host` | The remote host IP address that the client will connect to.                        | `"127.0.0.1"`  |
| `remote_port` | The remote host port that the client will connect to.                              | `9999`         |

The client can also be started with a custom configuration file by passing it to the
client using the `-c/--config` flag when starting the client. The configuration file
must be a JSON file that follows the same structure as the default configuration file.

```shell
poetry run python consortium.py client -c path/to/custom_client_config.json
```

### Starting the Consortium Client in Disconnected Mode.

If you start the client without having started the server, or if the client for
whatever reason fails to connect to the server, it will start in a disconnected mode in
the disconnected interpreter.

To attempt to connect to a server you can use the `connect` command. This command
allows you to attempt to connect using the default client configuration file or a
custom client configuration file.

```shell
connect -c path/to/custom_client_config.json
connect -c  # Connect using the default client configuration file at `data/client/client_config.json`.
```

Here we can just attempt to connect to a server using the default client configuration
file (_after_ the server has been started).

```plaintext
Consortium > connect -c
[+] Successfully logged into server 127.0.0.1:9999 as 'admin'.
```

Alternatively you can manually provide the fields required to connect to the server.
This makes it easy to connect to multiple servers without having to modify the client
configuration file or create new configuration files while in the client itself.

```plaintext
Consortium > connect -u admin -p admin -rh 127.0.0.1 -rp 9999
[+] Successfully logged into server 127.0.0.1:9999 as 'admin'.
```

After you have successfully connected to the server a new client session will be
present representing a connection to a particular server. List all available client
sessions with the `list_client_sessions` command.

!!! info
    A _client session_ represents a particular connection to a valid instance of a
    Consortium server. The client supports connecting multiple client sessions at once
    as well as switching to different ones on the fly.

    Client sessions do not need to be unique to a server host address. This means you
    can have multiple client sessions connected to the same server on different
    accounts.


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
    through all available completion options.

```shell
Consortium (Home) > interact_client_session 43fdb768-486c-4159-aaf4-366d41829222
[+] Interacting with client session '' (43fdb768-486c-4159-aaf4-366d41829222)
```

All in all, the process of starting the client in disconnected mode and connecting to a
server is demonstrated below.

<div id="disconnected-interpreter-reconnect-demo"></div>
<script>
  window.onload = function(){
    AsciinemaPlayer.create(
      "/asciinema/disconnected_interpreter_reconnect_demo.cast",
      document.getElementById("disconnected-interpreter-reconnect-demo"),
      {theme: 'gruvbox-dark', autoPlay: true, loop: true},
    );
  }
</script>

For more information about using the client, refer to the [Client section of the
Manual](../manual/client/introduction.md).
