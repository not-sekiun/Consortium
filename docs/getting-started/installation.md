# Installation

Consortium can be installed in one of two ways.

| | [Manual install](#manual-install) | [Docker install](#docker-install) |
|---|---|---|
| Runs | Directly on the host | Server in a container, client on demand |
| Requires | Python 3.14+, uv, Git, Docker | Docker, Git |
| Component dependencies | Installed into the local environment | Built into the image |
| Framework reloading (`-r`) | Supported | Not supported |
| Listener ports | Bound directly on the host | Published from the container |

The manual install is the better fit for developing the framework or writing components,
because source changes take effect immediately and framework reloading works. The Docker
install is the better fit for running a server without provisioning Python on the host.

Both installs read their configuration from the same `data/` directory, so a server can
be moved between them without reconfiguration.

## Manual install

### Prerequisites

!!! important
    Consortium requires **Python 3.14 or newer**. If you are using an older version of
    Python, you will need to upgrade to a newer version before you can install
    Consortium.

??? important "Supported Python versioning"
    Consortium aims to only support Python versions **from 3.14 onwards** that have not
    reached end-of-life status yet (
    See [here](https://devguide.python.org/versions/#versions)).

Before you can install Consortium, you need to install a few prerequisite dependencies
and tools.

- [Python (3.14 or newer)](https://www.python.org/downloads/): The programming language
  that the Consortium server and client are written in.
- [Git](https://git-scm.com/downloads): The version control system that Consortium
  uses to manage its source code.
- [uv](https://docs.astral.sh/uv/getting-started/installation/): The package manager
  that Consortium uses to manage its Python dependencies.
- [Docker](https://docs.docker.com/get-started/get-docker/): The container runtime used
  by bundled agent generators that compile their payloads inside a container. Docker
  Engine on Linux, or Docker Desktop on Windows and macOS.

??? question "Why does a manual install need Docker?"
    Agents written in a compiled language need that language's toolchain to produce a
    payload. Rather than requiring you to install a toolchain for every language the
    bundled agents are written in, those agent generators compile inside a container that
    already carries one, using whichever Docker engine is available locally.

    Docker is only needed for those generators. Every other part of the framework, the
    server, the client, listeners, plugins, event hooks, and agents that do not compile
    in a container, runs without it. A generator that needs Docker refuses to start with
    an explanatory error when the engine is missing, and leaves the rest of the framework
    unaffected.

### Installing Consortium

!!! important
    Make sure that all the installed tools are visible on your system's PATH, and that
    the Docker engine is running before starting an agent generator that needs it.

1. Clone the repository and install base dependencies along with component dependencies
   using `uv`.
    ```shell
    git clone https://github.com/not-sekiun/Consortium
    cd Consortium
    uv sync --all-packages
    ```
2. Start the server first
    ```shell
    uv run consortium.py server
    ```
3. Connect to the server locally using the CLI client.
    ```shell
    uv run consortium.py client
    ```

For more information about component dependencies and how to install them, see the
[Installing Component Dependencies](#installing-component-dependencies) section.

For more information on how to configure the server and client, see the
[Server](../server/server-overview.md) and [Client](../client/client-overview.md)
sections.

## Docker install

### Prerequisites

- [Docker](https://docs.docker.com/get-started/get-docker/): Docker Engine on Linux, or
  Docker Desktop on Windows and macOS. Docker Compose v2 is included with both.
- [Git](https://git-scm.com/downloads): The version control system that Consortium
  uses to manage its source code.

Python and uv are **not** required on the host. Both are provided inside the image.

### Installing Consortium

1. Clone the repository.
    ```shell
    git clone https://github.com/not-sekiun/Consortium
    cd Consortium
    ```
2. Build the image and start the server.
    ```shell
    docker compose up -d --build
    ```
    Only the server starts. It is ready once its health check reports `healthy`, which
    you can watch with `docker compose ps`.
3. Connect to the server with the CLI client, which runs in a container of its own from
   the same image.
    ```shell
    docker compose run --rm client
    ```

The client is declared under a Compose profile, so `docker compose up` never starts it.
It needs an interactive terminal, which `docker compose run` provides and
`docker compose up` does not.

Useful follow-up commands:

```shell
docker compose logs -f server   # follow the server's log output
docker compose ps               # show container and health status
docker compose down             # stop the stack, leaving data/ intact
```

### What the Compose stack does

- **Configuration and state live on the host.** `data/` is bind mounted into the
  container, so the server and client read the same configuration files a manual install
  uses, and agents, payloads, assets, artifacts, and logs written by the server persist
  across `docker compose down`.
- **The API is published on port 9999.** The server binds `0.0.0.0:9999` inside the
  container and Compose publishes that port to the host, so the REST API and the
  websockets events API are reachable at `127.0.0.1:9999`.
- **The client shares the server's network.** This means `data/client/client_config.json`
  can point at `127.0.0.1` and work both in a container and on the host, so one
  configuration file serves both installs.

!!! important
    `local_host` in `data/server/server_config.json` must be `0.0.0.0` for the published
    port to work. Binding to `127.0.0.1` restricts the server to the container's own
    loopback interface, which is not reachable from the host.

### Listener ports

Published ports are fixed when a container starts, but listeners bind their ports later,
while the server is running. A listener on a port that was not published is only
reachable from inside the container.

To use listeners, publish the range of ports you intend to create them on by uncommenting
and adjusting the range in `docker-compose.yml`, then recreate the server.

```yaml title="docker-compose.yml"
    ports:
      - "9999:9999"
      - "8080-8090:8080-8090"
```

This constraint does not apply to a manual install, where listeners bind host ports
directly.

### Building agents that compile in containers

Some bundled agent generators compile their payloads inside a container. For these to
work from a containerized server, the server needs
access to a Docker engine. The Compose file mounts the host's Docker socket into the
server container for this purpose, and builds then run on the host's engine.

!!! warning
    Mounting the Docker socket grants the container control of the host's Docker engine,
    which is equivalent to root access on the host. Remove the `/var/run/docker.sock`
    mount and the `group_add` entry from `docker-compose.yml` if you do not intend to
    build these agents.

On Linux, the socket is owned by the `docker` group, so pass that group's id when
starting the stack:

```shell
DOCKER_GID=$(getent group docker | cut -d: -f3) docker compose up -d
```

On Docker Desktop the default is correct and no extra step is needed.

## Installing Component Dependencies

!!! note
    This section applies to the manual install. A Docker install already has every
    bundled component's dependencies built into the image.

Consortium ships with a set of default components that extend the framework. These are
the components bundled with the server out of the box and live in
`consortium/components`. Components come in four types: **listeners**, **agents**,
**plugins**, and **event-hooks**.

A component that needs its own third-party Python packages is a `uv` **workspace
package**: it has its own `pyproject.toml` next to its manifest that declares those
dependencies, and it is registered as a member of the workspace in the root
`pyproject.toml`.

```toml title="pyproject.toml"
[tool.uv.workspace]
members = [
    "consortium/components/agents/consortium/eula/python",
    "consortium/components/event_hooks/webhook_sender",
    "consortium/components/listeners/consortium/http",
]
```

Because the components are workspace members, syncing the whole workspace installs the
base framework dependencies **and** the dependencies of every bundled component in one
step. This is the `--all-packages` flag, which is used for the baseline install.

```shell
uv sync --all-packages
```

!!! important
    A component will **not load** if its declared Python dependencies are not installed
    in your environment. If you find a default component is missing at runtime, make
    sure you synced the workspace with `--all-packages` so its package dependencies were
    installed.

To install the dependencies for only a **particular** component, sync just that
workspace package with `--package`, passing the name declared in that component's own
`pyproject.toml` (`[project].name`).

```shell
uv sync --package <component-package-name>
```

You can pass multiple `--package` flags to sync several individual packages at once.

Components you add to a **Docker install** are built into the image, so rebuild the
image after adding one:

```shell
docker compose up -d --build
```

## Installing Consortium for Development

If you want to contribute to the development of Consortium, you need to additionally
install the development group dependencies and the pre-commit hooks.

1. Follow the steps in the [Manual install](#manual-install) section above to install the
   base dependencies
2. Install the development dependencies using `uv`.
    ```shell
    uv sync --all-packages --group dev
    ```
3. Install pre-commit hooks.
    ```shell
    uv run pre-commit install
    ```

## Installing Consortium with local documentation hosting via Zensical

If you want to host the documentation locally using Zensical, you need to additionally
install the documentation group dependencies.

1. Follow the steps in the [Manual install](#manual-install) section above to install the
   base
2. Install the documentation dependencies using `uv`.
    ```shell
    uv sync --all-packages --group docs
    ```
3. Serve the documentation locally.
    ```shell
    uv run zensical serve
    ```
