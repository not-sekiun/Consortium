# Consortium
Consortium is a _programming language agnostic_, and _networking protocol agnostic_
command and control (C2) framework that is designed to be _highly extensible_ and
_modular_. The framework ships with its own listeners and agents while also allowing
users to rapidly develop their own highly customized listeners and agents.


> [!WARNING]
> Consortium is in active development. Backwards incompatible or
> breaking changes may be made to the core REST API/framework/default listener and
> agent implementations. As such, compatability is only guaranteed between clients,
> servers, listeners, and agents of the _exact same framework version_.

## ⚙️ Features
- **📡 Asynchronous multiplayer/multiserver support** - Multiple clients can connect to
the same server to perform all C2 related operations, including the sharing of agent
sessions. The default client allows the ability to seamlessly switch between different
servers. The server runs asynchronously on FastAPI allowing for blazing fast speeds.
- **🤖 High extensibility and automation** - The server supports writing custom plugins
and event hooks in python that interface natively with the backend. The server performs
all communications through either its REST API (for most C2 related operations) or
its websockets endpoint (for server initiated push events)
- **🔌 Modular listener-agent design** - Consortium ships with its own listeners and
agents. However, custom listeners and agents can be added to the framework. Agents can
be written in any language while listeners can be written in python to natively
interact with the server, or they can be written in a different language to interact
with the server through its REST API.

and more!

## ✨ Quickstart
### Prerequisites
Consortium requires Python 3.12+ and uses the Poetry package manager to handle its
Python dependencies. Git is recommended for installing and updating the framework, no
binary releases will be provided.
1. [Install Python 3.12+](https://www.python.org/downloads)
2. [Install Poetry](https://python-poetry.org/docs/#installation).
3. [Install Git](https://www.git-scm.com)

> [!IMPORTANT]
> Make sure your installed tools are visible on your system PATH.

### Installation
1. Clone the Consortium repository with `git` and `cd` into its root folder.
```bash
git clone https://github.com/not-sekiun/Consortium.git
cd Consortium
```

2. Install dependencies through `poetry`.
```bash
poetry install
```

### Starting the Framework
The Consortium C2 framework runs on a client-server model. To use the
framework the server must be started before starting any compatible client
to connect to the server.

1. Start the Consortium server. By default, it binds at `0.0.0.0:1337`.
```bash
poetry run python consortium.py server
```

2. Start the Consortium client. By default, it connects to `127.0.0.1:1337`
```bash
poetry run python consortium.py client
```

### Updating
1. In the project's root folder, pull the new repository changes with `git`.
```shell
git pull
```

2. Update any dependencies that are present using `poetry`.
```shell
poetry install
```

## 📚 Documentation
### Server REST API Documentation
The Consortium server is powered by FastAPI, which provides a built-in Swagger UI
for interacting with the server's REST API. The Swagger UI can be accessed by
navigating to `/doc` or `/redoc` at the server's root URL in a web browser.

> [!Note]
> The REST API documentation is only accessible to the local host.

### Client Documentation
To view all commands for a particular interpreter in the client type `help`.

```shell
Consortium (Home) > help
                                                                               Help Menu
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command                      ┃ Description                                                                                                                           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ agents                       │ Switch to the agents interpreter, the interface for managing and controlling connected agents.                                        │
│ banner                       │ Display a banner with information and branding about the Consortium framework.                                                        │
│ clear                        │ Clear the terminal screen.                                                                                                            │
│ connect                      │ Create a new client connection to a Consortium server using a configuration file or by manually specifying connection details.        │
│ disconnect                   │ Disconnect the current client connection or a specific client connection from a Consortium server                                     │
│ exit                         │ Close the Consortium client and exit the program.                                                                                     │
│ generators                   │ Switch to the generators interpreter, the interface for creating and managing the generation of agent payloads.                       │
│ help                         │ Display the help summary of a specific command or display the help menu listing all available commands for the current interpreter.   │
│ info_client_connection       │ Display detailed information for the current client connection or for a specific client connection.                                   │
│ interact_client_connection   │ Choose a specific client connection to interact with that is associated with a specific user account instance of a Consortium server. │
│ list_client_connections      │ List basic information for all current client connections to a Consortium server.                                                     │
│ listeners                    │ Switch to the listeners interpreter, the interface for creating and managing listeners.                                               │
│ redescribe_client_connection │ Change the description of the current client connection or a specific client connection.                                              │
│ rename_client_connection     │ Rename the current client connection or a specific client connection.                                                                 │
└──────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

To view the summary for a specific command, which includes all of its arguments, type
`help <command>`.

```shell
Consortium (Home) > help connect
description: Create a new client connection to a Consortium server using a configuration file or by manually specifying connection details.
usage: connect [-h] [-c [CONFIG_FILEPATH]] [-rh HOSTNAME/IP] [-rp PORT] [-u USERNAME] [-p PASSWORD]
```

To get the most comprehensive help for a specific command, including examples on how to
use that particular command, type `<command> --help` or
`<command> -h`.

> [!Note]
> The portion of the example behind the `#` is a comment that is not part of the
> command.

```shell
Consortium (Home) > connect --help
usage: connect [-h] [-c [CONFIG_FILEPATH]] [-rh HOSTNAME/IP] [-rp PORT] [-u USERNAME] [-p PASSWORD]

Create a new client connection to a Consortium server using a configuration file or by manually specifying connection details.

options:
  -h, --help            show this help message and exit
  -c [CONFIG_FILEPATH], --config [CONFIG_FILEPATH]
                        The filepath to a configuration JSON file containing the client settings specifying the remote host, remote port, username, and password to use when connecting to the Consortium server. If not provided, the default filepath to the configuration file is
                        used.
  -rh HOSTNAME/IP, --remote-host HOSTNAME/IP
                        The remote hostname or IP address of the Consortium server to connect to.
  -rp PORT, --remote-port PORT
                        The port of the Consortium server to connect to.
  -u USERNAME, --username USERNAME
                        The username of the account to login to when connecting to the Consortium server.
  -p PASSWORD, --password PASSWORD
                        The password of the account to login to when connecting to the Consortium server.

Examples:
    connect -c  # Connect using the default filepath to the client configuration file.
    connect -c path/to/client_config.json  # Connect using a custom configuration file.
    connect -u username -p password -rh server.com -rp 1234  # Connect through manually provided connection details.
```

### Complete Framework Documentation (WIP)
The complete documentation for the Consortium framework is available at the
[Consortium wiki](https://github.com/not-sekiun/Consortium/wiki).

The wiki provides:

1. A detailed guide on using the framework
2. An introduction to the workflow of the framework
3. Explanations of commonly used terms
4. An overview of the infrastructure of the framework

The wiki also covers advanced topics not documented within the application itself,
including:

- Writing custom native listeners, agents, plugins, and event hooks
- Utilizing the WebSocket API for server-initiated push events
- Writing listeners and agents in languages other than Python
