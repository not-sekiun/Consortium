# Installation

## Prerequisites

!!! important
    Consortium requires **Python 3.14 or newer**. If you are using an older version of
    Python, you will need to upgrade to a newer version before you can install
    Consortium.

??? important "A note on supported Python versioning"
    Consortium aims to only support Python versions **from 3.14 onwards** that have not
    reached end-of-life status yet (See [here](https://devguide.python.org/versions/#versions)).

Before you can install Consortium, you need to install a few prerequisite dependencies
and tools.

- [Python (3.14 or newer)](https://www.python.org/downloads/) - The programming language
that the Consortium server and client are written in.
- [Git](https://git-scm.com/downloads) - The version control system that Consortium
uses to manage its source code.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - The package manager
that Consortium uses to manage its Python dependencies.

## Installing Consortium

!!! important
    Make sure that all the installed tools are visible on your system's PATH.

1. Clone the Consortium repository from GitHub and navigate to the root directory of the
repository.
    ```shell
    git clone https://github.com/not-sekiun/Consortium
    cd Consortium
    ```
2. Install the Python dependencies using `uv`.
    ```shell
    uv sync
    ```
3. Start the server.
    ```shell
    uv run consortium.py server
    ```
4. Connect to the server using the CLI client.
    ```shell
    uv run consortium.py client
    ```

## Installing Consortium for Development

If you want to contribute to the development of Consortium, you need to additionally
install the development group dependencies and the pre-commit hooks.

1. Follow the steps in the [Installing Consortium](#installing-consortium) section
above to install the base
2. Install the development dependencies using `uv`.
    ```shell
    uv sync --dev
    ```
3. Install pre-commit hooks.
    ```shell
    uv run pre-commit install
    ```

## Installing Consortium with local documentation hosting via MkDocs

If you want to host the documentation locally using MkDocs, you need to additionally
install the documentation group dependencies.

1. Follow the steps in the [Installing Consortium](#installing-consortium) section
above to install the base
2. Install the documentation dependencies using `uv`.
    ```shell
    uv sync --docs
    ```
3. Serve the documentation locally.
    ```shell
    uv run mkdocs serve
    ```
