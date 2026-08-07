# install.sh

`install.sh` installs the prerequisites for a
[manual install](../getting-started/installation.md#manual-install) of Consortium on
Debian based Linux and on macOS. It checks what is already present, reports what is
missing, prints the exact commands it intends to run, asks for permission, installs the
missing pieces with the platform's package manager, and then offers to install the
framework and bundled component dependencies with `uv sync --all-packages`.

The script only ever adds tools. It does not upgrade, reconfigure, or remove anything that
is already installed.

| Platform             | Package manager                                                       |
|----------------------|------------------------------------------------------------------------|
| Debian based Linux   | `apt`, with `sudo` for the steps that need root                       |
| macOS                | Homebrew, installed first when it is not already present              |

Only `apt` is supported on Linux. On any other distribution the script stops and says so
rather than guessing at a package manager, leaving you to install the four prerequisites
with the one your distribution uses. Any other operating system stops the same way, and
Windows is pointed at [`install.ps1`](install-ps1.md).

## Running the script

Run it from the repository root, as your normal user:

```shell
bash scripts/install.sh
```

Do not run it with `sudo`. On Linux it calls `sudo` itself for the `apt` steps and asks
for a password when one is needed, which keeps the tools that install per user (uv, and
any interpreter uv manages) belonging to your account. On macOS Homebrew refuses to run as
root altogether.

### Options

| Option              | Effect                                                                            |
|---------------------|------------------------------------------------------------------------------------|
| `-c`, `--check-only`| Report what is found and what is missing, then exit without installing anything.   |
| `-y`, `--yes`       | Answer yes to every prompt, for an unattended run. Also installs Homebrew in its `NONINTERACTIVE` mode. |
| `--skip-sync`       | Do not offer to run `uv sync --all-packages` once the prerequisites are in place.  |
| `-h`, `--help`      | Print usage and exit.                                                             |

Without `--yes`, a run whose input is not a terminal (a pipeline, a provisioning step)
declines every prompt rather than hanging on one, and exits non-zero.

## What it checks for

| Requirement   | How it is detected                                                                     |
|---------------|-----------------------------------------------------------------------------------------|
| Homebrew      | `brew` on PATH, or an install under `/opt/homebrew` or `/usr/local` (macOS only)        |
| Git           | `git --version`                                                                         |
| Python 3.14+  | `python3.14`, `python3`, then `python`, falling back to a uv managed interpreter         |
| uv            | `uv --version`                                                                          |
| Docker        | `docker --version`                                                                      |
| Docker engine | `docker info` succeeding, which only happens against a running engine                   |

Homebrew does not add itself to the PATH of a shell that is already running, so the script
looks for it under both of its usual prefixes (Apple silicon first, then Intel) and loads
its environment with `brew shellenv` when it finds one there.

A Python older than 3.14 is reported as missing, with the version that was found named in
the report so it is clear why. uv can manage interpreters itself, and `uv run` and
`uv sync` pick a managed interpreter up automatically, so an interpreter that only uv
knows about satisfies the requirement and is reported as `uv managed`.

The Docker engine is a requirement of its own because Docker being installed does not mean
the engine is reachable. On Linux the script distinguishes an engine that is not running
from one your user cannot reach because it is not in the `docker` group, and says which it
is.

## What it installs

Only the missing entries are acted on, and everything that can share a package manager
invocation does. The plan is printed in full and a single question asked before any of it
runs.

### Debian based Linux

| Requirement  | Action                                                          |
|--------------|------------------------------------------------------------------|
| Git          | `apt-get install -y git`                                        |
| Docker       | `apt-get install -y docker.io`                                  |
| Python 3.14+ | `apt-get install -y python3.14`, or `uv python install 3.14`    |
| uv           | `curl -LsSf https://astral.sh/uv/install.sh \| sh`              |

The apt packages are installed in one `apt-get install` preceded by an `apt-get update`.

Not every Debian or Ubuntu release carries a `python3.14` package. The script checks
whether apt has a candidate for it, and when it does not it installs the interpreter with
`uv python install 3.14` instead, rather than adding a third party archive to the system's
sources. uv is installed with the official installer from `astral.sh`, which is the
upstream supported way to install it on Linux, since it is not carried by apt. `curl` is
added to the apt packages when it is needed for that and is not already present.

uv installs into `~/.local/bin`, which is frequently not on the PATH of the shell that
started the script, so the script adds it to its own PATH for the rest of the run.

When the Docker engine is not running and `systemctl` is available, the engine is enabled
and started with `systemctl enable --now docker`.

### macOS

| Requirement  | Action                                                                             |
|--------------|-------------------------------------------------------------------------------------|
| Homebrew     | The official installer from `raw.githubusercontent.com/Homebrew/install`            |
| Git          | `brew install git`                                                                  |
| Python 3.14+ | `brew install python@3.14`                                                          |
| uv           | `brew install uv`                                                                   |
| Docker       | `brew install --cask docker-desktop`, falling back to the older `docker` cask name |

Homebrew is installed first when it is missing, because macOS does not ship with it and
everything else on this platform is installed through it. The formulae are installed in a
single `brew install`. Docker Desktop is a cask rather than a formula, and the cask was
renamed from `docker` to `docker-desktop`, so the script tries the current name and falls
back to the old one.

When the Docker engine is not running, the script opens Docker Desktop with `open -a`. The
engine takes a moment to come up after that, so it may still be reported as not running at
the end of the same run, and Docker Desktop asks for its own permissions the first time it
is opened.

## After installing

Everything is checked again once the plan has run, and the result is printed in full.
A tool installed just now may only appear on the PATH of a **new** shell, so anything
still reported as missing is worth re-checking from a new shell before installing it by
hand.

On Linux, a Docker engine that is running but not reachable by your user is reported with
the command that fixes it:

```shell
sudo usermod -aG docker $USER
```

Group membership is picked up at login, so this takes effect after logging out and back
in. The script prints this rather than running it, because adding a user to the `docker`
group grants that user control of the Docker engine, which is equivalent to root on the
host.

The script then offers to run `uv sync --all-packages` in the repository root, which
installs the framework dependencies along with the dependencies of every bundled
component. Declining leaves you to run it yourself before starting the server. See
[Installing Component Dependencies](../getting-started/installation.md#installing-component-dependencies).

## Exit codes

| Code | Meaning                                                                                |
|------|-----------------------------------------------------------------------------------------|
| `0`  | Every prerequisite is present, and the dependency sync succeeded or was declined.       |
| `1`  | The platform is unsupported, a prompt was declined, a tool is still missing, or `uv sync` failed. |

A Docker engine that is not running is a warning rather than a failure: the server, the
client, listeners, plugins, event hooks, and every agent that does not compile in a
container run without it.
