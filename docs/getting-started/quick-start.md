# Quick Start

This guide gets a Consortium server and client running with their default configuration.
For anything beyond the defaults, follow the links to the relevant sections.

## Start the server

From the project root, start the server:

=== "Manual install"

    ```shell
    uv run consortium.py server
    ```

=== "Docker install"

    ```shell
    docker compose up -d
    ```

    The server runs in the background. Check that it is ready with `docker compose ps`
    and follow its output with `docker compose logs -f server`.

This binds the server to the default socket address `0.0.0.0:9999`. The server ships with
three default user accounts (`admin`, `operator`, and `spectator`), each using its own name
as the password.

!!! warning
    Change the default user accounts before deploying the server to prevent unauthorized
    access. See [User Accounts](../server/user-accounts.md).

To change the bind address, user accounts, roles, or logging, see the
[Server](../server/server-overview.md) section.

## Start the client

With the server running, start the client from the project root in a separate terminal:

=== "Manual install"

    ```shell
    uv run consortium.py client
    ```

=== "Docker install"

    ```shell
    docker compose run --rm client
    ```

    `docker compose up` never starts the client: it needs an interactive terminal, which
    only `docker compose run` provides.

The client reads `data/client/client_config.json` and connects to `127.0.0.1:9999` as
`admin` by default. Once connected, you land in the **Home** interpreter and can begin
operating against the server.

```plaintext
[+] Successfully logged into server 127.0.0.1:9999 as 'admin'.
```

If the client cannot reach the server at startup, it opens in **disconnected mode**, where
you can connect manually with the `connect` command. See
[Managing Client Sessions](../client/client-sessions/managing-client-sessions.md).

To point the client at a different server or user account, see the
[Client](../client/client-overview.md) section.

## Where to go next

- [Server](../server/server-overview.md): configure the server's address, accounts, roles,
  and logging.
- [Client](../client/client-overview.md): learn the interpreters, commands, and workflow
  for operating against a server.
