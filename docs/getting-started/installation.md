# Installation

## Prerequisites

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

## Installing Consortium

!!! important
    Make sure that all the installed tools are visible on your system's PATH.

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

## Installing Component Dependencies

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

## Installing Consortium for Development

If you want to contribute to the development of Consortium, you need to additionally
install the development group dependencies and the pre-commit hooks.

1. Follow the steps in the [Installing Consortium](#installing-consortium) section
   above to install the base dependencies
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

1. Follow the steps in the [Installing Consortium](#installing-consortium) section
   above to install the base
2. Install the documentation dependencies using `uv`.
    ```shell
    uv sync --all-packages --group docs
    ```
3. Serve the documentation locally.
    ```shell
    uv run zensical serve
    ```
