# Running the Client in Docker

On a [Docker install](../getting-started/installation.md#docker-install) the client runs
in a container of its own, started on demand from the same image as the server.

Everything in the rest of the [Client Usage](client-usage-overview.md) section applies unchanged: the
same interpreters, the same commands, the same configuration file. What differs is that
the client's **filesystem**, its **shell**, and its **network** belong to the container
rather than to your host. Every nuance on this page follows from that.

## Starting the client

```shell
docker compose run --rm client
```

The client is declared under a Compose profile, so `docker compose up` never starts it.
It needs an interactive terminal, which only `docker compose run` provides.

`--rm` removes the container when the client exits. Anything written inside the container
that is not in a mounted directory goes with it, which is the single most important thing
to know before transferring files.

## The file transfer boundary

A container only sees the directories mounted into it. Two are mounted for the client:

| Host path     | Container path          | Contents                                                                          |
|---------------|-------------------------|-----------------------------------------------------------------------------------|
| `./workspace` | `/consortium/workspace` | The client's working directory. Files you upload from and download to.            |
| `./data`      | `/consortium/data`      | Shared configuration and state: `client_config.json`, `aliases.json`, client logs |

Everything else in the container is discarded when the client exits.

### Downloading

The client's working directory is `/consortium/workspace`, which is the `./workspace`
directory in the project root on your host. A download with no explicit output path lands
there and is immediately visible outside the container:

```text
asset download 123e4567-e89b-12d3-a456-426614174000
```

```plaintext
[*] Downloading asset file 'mimikatz.exe' (123e4567-e89b-12d3-a456-426614174000) to '/consortium/workspace/mimikatz.exe'...
[+] Finished downloading asset
```

That file is now at `./workspace/mimikatz.exe` on the host.

!!! warning
    Passing `-o` with a path outside a mounted directory writes the file **inside the
    container**, where it is lost as soon as the client exits. `-o /tmp/x.exe` or
    `-o ../x.exe` will report success and leave nothing behind on the host.

### Uploading

The same boundary applies in reverse: the client can only upload files the container can
see. Copy the file into `./workspace` on the host, then upload it by name from the client:

```text
asset upload payload.exe
asset upload ./collection_directory
```

A path that exists on your host but was never mounted is simply not there as far as the
container is concerned. The client detects this and says so rather than leaving you
hunting for a typo:

```plaintext
[-] Asset path not found: '/home/operator/tools/mimikatz.exe'
[!] '/home/operator/tools/mimikatz.exe' resolved to '/home/operator/tools/mimikatz.exe' inside the container, which can only see the directories mounted into it. If this is a path on the host, copy it into the directory mounted at '/consortium/workspace' (./workspace on the host under the bundled docker-compose.yml) and upload it from there.
```

!!! note
    Tab completion on `asset upload` completes paths **inside the container**. Under the
    bundled Compose file it starts in the mounted workspace, so completion lists the files
    you dropped in `./workspace` and nothing on the host outside it.

### The startup notice

A containerized client reports where relative paths resolve when it starts, so the
working directory is never a guess:

```plaintext
[*] Running in a container. Downloads without '-o' and relative upload paths use '/consortium/workspace', which is mounted from the host, so downloaded files are visible outside the container.
```

If the working directory is **not** mounted from the host, the same notice becomes a
warning that downloads written there will be lost. Seeing that warning under the bundled
Compose file means the `./workspace` mount was removed or the working directory was
overridden.

### Mounting another directory for a single run

To work against a host directory other than `./workspace` without editing
`docker-compose.yml`, mount it for that one invocation and make it the working directory:

=== "Linux and macOS"

    ```shell
    docker compose run --rm -v "$PWD:/work" -w /work client
    ```

=== "Windows (PowerShell)"

    ```shell
    docker compose run --rm -v "${PWD}:/work" -w /work client
    ```

Downloads without `-o` and relative upload paths then resolve against whatever directory
you launched from, which is the closest equivalent to how the client behaves on a manual
install.

## Paths in client output are container paths

The client reports absolute paths so that there is no ambiguity about where a file went,
but they are paths **inside the container**. Translate them through the mount table above:

| Client output                        | On the host                |
|--------------------------------------|----------------------------|
| `/consortium/workspace/mimikatz.exe` | `./workspace/mimikatz.exe` |
| `/consortium/data/client/logs/`      | `./data/client/logs/`      |
| `/consortium/anything_else`          | Nowhere. Discarded on exit |

## The `exec` command runs inside the container

`exec` runs its command in the client's shell, which is the **container's** shell, not
your host's. The image is a slim Debian base carrying Python, `uv`, and the Docker CLI,
so host tooling is not available and anything the command writes obeys the same mount
rules as everything else.

```text
exec ls /consortium/workspace   # lists ./workspace on the host
exec ls /home/operator          # not your host's home directory
```

## Resource files and aliases

`rc <file>` resolves its path the same way uploads do, so keep resource files in
`./workspace` (or under `./data`) to make them reachable:

```text
rc setup.rc
```

Aliases are stored in `data/client/aliases.json`, which is mounted, so aliases created in
a containerized client survive `--rm` and are shared with a client run on the host. See
[Aliases and Resource Files](aliases-and-resource-files.md).

## Networking

The client container shares the **server container's** network namespace. This is what
lets one `data/client/client_config.json` serve both installs: `remote_host` of
`127.0.0.1` reaches the server in both cases.

The consequence is that `127.0.0.1` inside the client always means the server container,
never your host. Connecting to a second server running directly on your host needs that
host's real address rather than loopback:

```text
session connect -rh 192.168.1.10 -rp 9999 -u admin -p admin
```

Reaching servers elsewhere on the network works normally. See
[Managing Client Sessions](client-sessions/managing-client-sessions.md).

!!! note
    `session connect -c <path>` and the client's own `-c/--client-config` flag read a
    configuration file through the container, so a config file kept outside `./data` or
    `./workspace` is not reachable by the path it has on the host.

## What is lost when the client exits

| Item                                | Persists |
|-------------------------------------|----------|
| Files in `/consortium/workspace`    | Yes, in `./workspace` |
| Files in `/consortium/data`         | Yes, in `./data` |
| Aliases (`data/client/aliases.json`)| Yes |
| Client logs (`data/client/logs/`)   | Yes |
| Files written anywhere else         | No |
| Command history                     | No, and it is per session on a manual install too |

## Where to go next

- [Managing Assets](resource-management/managing-assets.md),
  [Managing Artifacts](resource-management/managing-artifacts.md), and
  [Managing Payloads](resource-management/managing-payloads.md): the commands that move
  files between the client and the server.
- [Installation](../getting-started/installation.md#docker-install): the rest of the
  Docker install, including listener ports and containerized agent builds.
- [Client Overview](client-usage-overview.md): the interpreters and commands themselves, which
  are identical in both installs.
