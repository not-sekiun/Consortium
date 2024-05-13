# Consortium
Consortium is a _programming language agnostic_, and _networking protocol agnostic_
command and control (C2) framework that is designed to be _highly extensible_ and
_modular_. The framework ships with its own listeners and agents while also allowing
users to rapidly develop their own highly customized listeners and agents.



> 🔴 **Warning:** Consortium is in active development. Backwards incompatible or
> breaking changes may be made to the core REST API/framework/default listener and
> agent implementations. As such, compatability is only guaranteed between clients,
> servers, listeners, and agents of the _exact same framework version_.

## Features ⚙️
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

## Quickstart ✨
### Prerequisites 📝
Consortium requires Python 3.12+ and uses the Poetry package manager to handle its
Python dependencies. Git is recommended for installing and updating the framework, no
binary releases will be provided.
1. [Install Python 3.12+](https://www.python.org/downloads)
2. [Install Poetry](https://python-poetry.org/docs/#installation).
3. [Install Git](https://www.git-scm.com)

_Make sure your installed tools are visible on your system PATH._

### Installation 🛠️
1. Clone the Consortium repository with `git` and `cd` into its root folder.
```bash
git clone https://github.com/not-sekiun/Consortium.git
cd Consortium
```

2. Install dependencies through `poetry`.
```bash
poetry install
```

### Updating 🔃
1. In the root folder of the project pull the new repository changes with `git`.
```shell
git pull
```

2. Update any dependencies that are present using `poetry`.
```shell
poetry install
```

### Basic Usage 🚀
1. Start the Consortium server. By default, it binds at `0.0.0.0:1337`.
```bash
poetry run python consortium.py server
```

2. Start the Consortium client. By default, it connects to `127.0.0.1:1337`
```bash
poetry run python consortium.py client
```

Changing these default configuration values can be done at `data/server/config.json` and
`data/client/config.json` respectively.

### Further Usage 🔎
Typing `help` in any of the CLI interpreters will provide a list of all available
commands and their descriptions.

```
Consortium (Listener) > help
                                                                             Commands
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command                  ┃ Description                                                                                                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ agents                   │ Switch to the agents interpreter, the interface for managing and controlling connected agents.                                      │
│ banner                   │ Display a banner with information and branding about the Consortium framework.                                                      │
│ cancel_listener          │ Forcefully stop a running listener.                                                                                                 │
│ clear                    │ Clear the terminal screen.                                                                                                          │
│ delete_listener          │ Delete a non-running listener.                                                                                                      │
│ exit                     │ Close the Consortium client and exit the program.                                                                                   │
│ generators               │ Switch to the generators interpreter, the interface for creating and managing the generation of agent payloads.                     │
│ help                     │ Display the help summary of a specific command or display the help menu listing all available commands for the current interpreter. │
│ home                     │ Return to the home interpreter, the main control interface of the Consortium framework.                                             │
│ info_listener            │ Display detailed information about a specific listener.                                                                             │
│ info_listener_template   │ Display detailed information about a specific listener template.                                                                    │
│ list_listener_templates  │ List all available listener templates for reference and selection.                                                                  │
│ list_listeners           │ List all created listeners along with their essential information.                                                                  │
│ redescribe_listener      │ Update the description of a listener instance for better organization and identification.                                           │
│ rename_listener          │ Change the name of a listener instance without altering its configured parameters.                                                  │
│ set_listener_parameter   │ Modify the parameters of an existing listener to adjust its behavior or configuration.                                              │
│ start_listener           │ Start a created listener using its configured parameters.                                                                           │
│ stop_listener            │ Stop a running listener, suspending its operation.                                                                                  │
│ unset_listener_parameter │ Unset a listener parameter for a specified listener to adjust its behavior or configuration.                                        │
│ use_listener_template    │ Select a listener template to use to create a new listener.                                                                         │
└──────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The `help` command can
also be used to get basic information about a specific command by typing
`help <command>`.

```
Consortium (Generators) > help list_agent_templates
description: List all available agent templates for reference and selection.
usage: list_agent_templates [-h]
```

For the most detailed help with examples and comments, run commands with the
`-h/--help` flag.

```
Consortium (Agents) > interact_agent --help
usage: interact_agent [-h] agent_id

Choose a specific agent to interact with.

positional arguments:
  agent_id    The agent ID of the agent to interact with.

options:
  -h, --help  show this help message and exit

Examples:
    interact_agent 123e4567-e89b-12d3-a456-42661417400
```

Automatically generated documentation with Swagger UI for the server's REST API is
available at `https://127.0.0.1:1337/docs`. This documentation is only viewable from
the localhost.

For more information, please refer to the
[Consortium Wiki](https://github.com/not-sekiun/Consortium/wiki).
