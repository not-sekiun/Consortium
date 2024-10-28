# Installation

## Prerequisites

!!! important
    Consortium requires **Python 3.12 or newer**. If you are using an older version of
    Python, you will need to upgrade to a newer version before you can install
    Consortium.

Before you can install Consortium, you need to install a few prerequisite dependencies
and tools.

- [Python (3.12 or newer)](https://www.python.org/downloads/) - The programming language that the
Consortium server and client are written in.
- [Git](https://git-scm.com/downloads) - The version control system that Consortium
uses to manage its source code.
- [Poetry](https://python-poetry.org/docs/#installation) - The package manager that
Consortium uses to manage its Python dependencies.

## Installing Consortium

!!! important
    Make sure that all the installed tools are visible on your system's PATH.

1. Clone the Consortium repository from GitHub and navigate to the root directory of the
repository.
    ```shell
    git clone https://github.com/not-sekiun/Consortium
    cd Consortium
    ```

2. Install the Python dependencies using Poetry.
    ```shell
    poetry install
    ```

3. Start the server.
    ```shell
    poetry run python consortium.py server
    ```

4. Connect to the server using the CLI client.
    ```shell
    poetry run python consortium.py client
    ```
