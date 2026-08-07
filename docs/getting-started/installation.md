# Installation

Consortium can be installed in one of two ways.

|                            | [Manual install](#manual-install)    | [Docker install](#docker-install)                             |
|----------------------------|--------------------------------------|---------------------------------------------------------------|
| Runs                       | Directly on the host                 | Server in a container, client on demand                       |
| Requires                   | Python 3.14+, uv, Git, Docker        | Docker, Git                                                   |
| Component dependencies     | Installed into the local environment | Bundled ones built into the image, added ones synced on start |
| Framework reloading (`-r`) | Supported                            | Not supported                                                 |
| Listener ports             | Bound directly on the host           | Published from the container                                  |

The manual install is the better fit for developing the framework itself, because source
changes take effect immediately and framework reloading works. The Docker install is the
better fit for running a server without provisioning Python on the host. Writing
components suits either.

Both installs read their configuration from the same `data/` directory, so a server can be
moved between them without reconfiguration. A manual install can also be
[done for you by a script](#automatic-install).

## Automatic install

The install scripts in `scripts/` carry out a [manual install](#manual-install) for you:
they install its prerequisites, then Consortium's own dependencies. Each script reports
what is already present and what is missing, shows the commands it intends to run, and
installs nothing until you agree. Only missing tools are installed, using **winget** on
Windows, **apt** on Debian based Linux, and **Homebrew** on macOS, which is installed
first because macOS does not ship with it.

1. Clone the repository and change into it.
    ```shell
    git clone https://github.com/not-sekiun/Consortium
    cd Consortium
    ```
    Without Git, download the repository as a ZIP archive from
    [GitHub](https://github.com/not-sekiun/Consortium) and run the script from the
    extracted directory instead: it installs Git along with everything else.
2. Run the script for your platform from the repository root.

    === "Windows"

        ```powershell
        powershell -ExecutionPolicy Bypass -File scripts\install.ps1
        ```

    === "Linux and macOS"

        ```shell
        bash scripts/install.sh
        ```

        Run it as your normal user rather than with `sudo`. On Linux it calls `sudo`
        itself for the `apt` steps, and Homebrew refuses to run as root.

3. Start the server, then connect to it with the client from a second terminal.
    ```shell
    uv run consortium.py server
    ```
    ```shell
    uv run consortium.py client
    ```

Both scripts take `--check-only` (`-CheckOnly` on Windows) to report what is present
without installing anything, and `--yes` (`-Yes`) for an unattended run. See
[`install.ps1`](../scripts/install-ps1.md) and [`install.sh`](../scripts/install-sh.md)
for what each one installs.

!!! note
    A tool installed just now often only appears on the PATH of a **new** terminal. If the
    script still reports it as missing, open a new terminal and run the script again
    before installing it by hand.

## Manual install

### Prerequisites

!!! important
    Consortium requires **Python 3.14 or newer**, and only supports
    [Python versions](https://devguide.python.org/versions/#versions) from 3.14 onwards
    that have not reached end-of-life.

- [Python (3.14 or newer)](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which manages
  Consortium's Python dependencies.
- [Docker](https://docs.docker.com/get-started/get-docker/): Docker Engine on Linux, or
  Docker Desktop on Windows and macOS. Only bundled agent generators that compile their
  payloads inside a container need it. Everything else runs without it, and a generator
  that needs a missing engine fails with an explanatory error.

!!! important
    Make sure that all the installed tools are visible on your system's PATH, and that
    the Docker engine is running before starting an agent generator that needs it.

### Installing Consortium

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

For component dependencies see
[Installing Component Dependencies](#installing-component-dependencies), and for
configuring the server and client see
[Server Usage](../server-usage/server-usage-overview.md) and
[Client Usage](../client-usage/client-usage-overview.md).

## Docker install

### Prerequisites

- [Docker](https://docs.docker.com/get-started/get-docker/): Docker Engine on Linux, or
  Docker Desktop on Windows and macOS. Docker Compose v2 is included with both.
- [Git](https://git-scm.com/downloads)

Python and uv are **not** required on the host. Both are provided inside the image.

### Installing Consortium

1. Clone the repository.
    ```shell
    git clone https://github.com/not-sekiun/Consortium
    cd Consortium
    ```
2. Build the image and start the stack.
    ```shell
    docker compose up -d --build
    ```
    This starts the server and the `dind` builder engine it compiles agents with (see
    [Building agents that compile in containers](#building-agents-that-compile-in-containers)).
    The server is ready once its health check reports `healthy`, which you can watch with
    `docker compose ps`.
3. Connect to the server with the CLI client, which runs in a container of its own from
   the same image.
    ```shell
    docker compose run --rm client
    ```
    `docker compose up` never starts the client: it needs an interactive terminal, which
    only `docker compose run` provides.

!!! important "The containerized client only sees what is mounted into it"
    Downloads with no `-o` path and relative upload paths use `/consortium/workspace`,
    which is `./workspace` on your host. Files written anywhere else in the container are
    lost when the client exits, uploads can only read files inside a mounted directory,
    and `exec` runs in the container's shell rather than your host's. See
    [Running the Client in Docker](../client-usage/running-the-client-in-docker.md) for
    the full set of differences.

Useful follow-up commands:

```shell
docker compose logs -f server   # follow the server's log output
docker compose ps               # show container and health status
docker compose down             # stop the stack, leaving data/ intact
```

### What the Compose stack does

- **Configuration, state, and components live on the host.** `data/` and
  `consortium/components/` are bind mounted, so the server reads the same configuration
  files a manual install uses, everything it writes survives `docker compose down`, and
  components you add or edit take effect on the next server start. See
  [Adding components](#adding-components).
- **The API is published on port 9999.** The REST API and the websockets events API are
  reachable at `127.0.0.1:9999`.
- **The client exchanges files through `workspace/`**, which is bind mounted into the
  client container as its working directory.
- **The client shares the server's network**, so a `data/client/client_config.json`
  pointing at `127.0.0.1` works both in a container and on the host.
- **Agent builds run on their own Docker engine**, provided by the `dind` service. The
  host's engine is never involved.

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

Agent generators that compile their payloads in a container need a Docker engine to build
on. The Compose stack runs one in the `dind` service and points the server at it with
`DOCKER_HOST=tcp://dind:2375`, so no extra setup is required and the same
`docker compose up -d` works on Linux, Windows, and macOS.

!!! note
    The builder's image cache lives in the `builder-cache` volume, so the first agent
    build downloads its base image before compiling and later builds reuse it. The volume
    is removed only by `docker compose down -v`.

!!! warning
    The `dind` service runs privileged, which it requires in order to run an engine of
    its own. A privileged container is not fully isolated from the host, but unlike a
    mounted Docker socket it grants no control over the host's engine. Switching its
    image to `docker:dind-rootless` narrows this further, at the cost of a slower storage
    driver.

To build on a different engine, such as a shared build server, repoint `DOCKER_HOST`:

```yaml title="docker-compose.yml"
    environment:
      - DOCKER_HOST=tcp://builder.internal:2375
```

If you do not intend to build these agents, delete the `dind` service from
`docker-compose.yml` along with the server's `DOCKER_HOST` entry and its `depends_on`
block.

### Adding components

`consortium/components/` is bind mounted, so adding a component is the same as on a
manual install: drop its directory into the right component type folder on the host and
restart the server, which syncs any dependencies it declares as part of that restart.

```shell
docker compose restart server
```

!!! note
    Editing a component's source, its manifest, or the Dockerfile a containerized agent
    generator builds with only needs this restart too. Changes to the framework or server
    code are baked into the image and need `docker compose up -d --build server`.

## Installing Component Dependencies

!!! note
    This section applies to the manual install. In a Docker install, every bundled
    component's dependencies are already built into the image, and components you add
    later are synced automatically when the server starts.

Consortium ships with a set of default components that extend the framework. They live in
`consortium/components` and come in four types: **listeners**, **agents**, **plugins**,
and **event-hooks**.

A component that needs its own third-party Python packages declares them in a
`pyproject.toml` of its own and is registered as a `uv` workspace member, so syncing the
whole workspace with `--all-packages` installs the base framework dependencies **and**
the dependencies of every bundled component in one step.

```shell
uv sync --all-packages
```

!!! important
    A component will **not load** if its declared Python dependencies are not installed
    in your environment. If you find a default component is missing at runtime, make
    sure you synced the workspace with `--all-packages` so its package dependencies were
    installed.

To install the dependencies for only a **particular** component, sync just that workspace
package with `--package`, passing the name declared in that component's own
`pyproject.toml` (`[project].name`). Several can be synced at once by passing the flag
more than once.

```shell
uv sync --package <component-package-name>
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
