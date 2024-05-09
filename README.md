# Consortium
Consortium is a _programming language agnostic_, and _networking protocol agnostic_
command and control (C2) framework that is designed to be _highly extensible_ and
_modular_. The framework ships with its own listeners and agents while also allowing
users to rapidly develop their own highly customized listeners and agents.

## Features
- **asynchronous multiplayer/multiserver support** - Multiple clients can connect to
the same server to perform all C2 related operations, including the sharing of agent
sessions. The default client allows the ability to seamlessly switch between different
servers.
- **High extensibility and automation** - The server supports writing custom plugins
and event hooks in python that interface natively with the backend. The server performs
all communications through either its REST API (for most C2 related operations) or
its websockets endpoint (for server initiated push events)
- **Modular listener-agent design** - Consortium ships with its own listeners and
agents. However, custom listeners and agents can be added to the framework. Agents can
be written in any language while listeners can be written in python to natively
interact with the server, or they can be written in a different language to interact
with the server through its REST API.

## Installation
Consortium requires Python 3.12+ and uses the poetry package manager to handle its
dependencies. Additionally, docker is required to run the server's

1. [Install poetry](https://python-poetry.org/docs/#installation). There are different
ways to do this but this guide will use poetry's official installer.

Linux, macOS
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Windows (Powershell).
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

2. Clone the Consortium repository and `cd` into its root folder.
```bash
git clone https://github.com/not-sekiun/Consortium.git
cd Consortium
```

3. Install dependencies through poetry.
```bash
poetry install
```

4. Start the Consortium server.
```bash
poetry run python -m consortium.py server
```

5. Start the Consortium client.
```bash
poetry run python -m consortium.py client
```

Configuring the server is done through its config file located at
`data/server/config.json`. Similarly, the client is configured through its config file
located at `data/client/config.json`. The default configuration should work out of the
box for most users.
