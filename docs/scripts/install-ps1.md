# install.ps1

`install.ps1` installs the prerequisites for a
[manual install](../getting-started/installation.md#manual-install) of Consortium on
Windows, using [winget](https://learn.microsoft.com/windows/package-manager/winget/) as
the package manager. It checks what is already present, reports what is missing, asks for
permission before changing anything, installs the missing tools, and then offers to
install the framework and bundled component dependencies with `uv sync --all-packages`.

The script only ever adds tools. It does not upgrade, reconfigure, or remove anything that
is already installed.

## Running the script

Run it from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
```

`-ExecutionPolicy Bypass` applies to that one invocation only and leaves the machine's
execution policy untouched. It is needed because the default policy on Windows blocks
unsigned scripts.

Administrator rights are not needed to start the script. winget elevates on its own for
the packages that require it, which shows a UAC prompt during the install.

### Options

| Option       | Effect                                                                                     |
|--------------|--------------------------------------------------------------------------------------------|
| `-CheckOnly` | Report what is found and what is missing, then exit without installing anything.           |
| `-Yes`       | Answer yes to every prompt, for an unattended run. Also passes `--disable-interactivity` to winget. |
| `-SkipSync`  | Do not offer to run `uv sync --all-packages` once the prerequisites are in place.          |

`Get-Help scripts\install.ps1 -Full` prints the same information from the script itself.

Without `-Yes`, a run that is not interactive (a scheduled task, a pipeline) declines
every prompt rather than hanging on one, and exits non-zero.

## What it checks for

winget is checked first. It ships as part of the **App Installer** package, and when it is
missing the script explains where to get it and stops without touching anything else.

| Requirement    | How it is detected                                                                   |
|----------------|---------------------------------------------------------------------------------------|
| Python 3.14+   | `py -3.14`, `py -3`, `python`, then `python3`, falling back to a uv managed interpreter |
| Git            | `git --version`                                                                       |
| uv             | `uv --version`                                                                        |
| Docker Desktop | `docker --version`, or the installed `Docker Desktop.exe`                             |
| Docker engine  | `docker info` succeeding, which only happens against a running engine                 |

Two details are worth knowing about the Python check:

- A version older than 3.14 is reported as missing, and the version that was found is
  named in the report so it is clear why.
- `python.exe` and `python3.exe` under `WindowsApps` are app execution aliases. When the
  Microsoft Store Python is not installed they are stubs that open the Store rather than
  reporting a version, so the script treats them as absent unless the Store package is
  actually installed. Every other alias in that directory, `winget.exe` included, is used
  normally.
- uv can manage interpreters itself, and `uv run` and `uv sync` pick a managed interpreter
  up automatically, so an interpreter that only uv knows about satisfies the requirement.
  The report names it as `uv managed`.

The Docker engine is listed as a requirement of its own because Docker Desktop being
installed does not mean the engine is running, and an agent generator that compiles its
payload in a container needs it running.

## What it installs

Only the missing entries are acted on. The script prints the plan first, then asks a
single question before running any of it:

| Requirement    | winget package ID      |
|----------------|------------------------|
| Python 3.14+   | `Python.Python.3.14`   |
| Git            | `Git.Git`              |
| uv             | `astral-sh.uv`         |
| Docker Desktop | `Docker.DockerDesktop` |

Each is installed with `winget install --id <id> --exact --source winget`, accepting the
package and source agreements. A package winget reports as already installed is treated as
a success rather than a failure, since the end state is the one that was asked for.

If the Docker engine is not running, the script starts Docker Desktop after the installs
rather than installing anything for it. The engine takes a moment to come up after that,
so it may still be reported as not running at the end of the same run.

## After installing

Installers write to the machine and user PATH, which a process that is already running
does not see, so the script rebuilds its own PATH from the registry before re-checking.
This does not always cover every tool, so anything still reported as missing immediately
after being installed is usually present in a **new** terminal: open one and run the
script again before installing that tool by hand.

The script then offers to run `uv sync --all-packages` in the repository root, which
installs the framework dependencies along with the dependencies of every bundled
component. Declining leaves you to run it yourself before starting the server. See
[Installing Component Dependencies](../getting-started/installation.md#installing-component-dependencies).

## Exit codes

| Code | Meaning                                                                          |
|------|-----------------------------------------------------------------------------------|
| `0`  | Every prerequisite is present, and the dependency sync succeeded or was declined. |
| `1`  | winget is missing, a prompt was declined, a tool is still missing, or `uv sync` failed. |

A Docker engine that is not running is a warning rather than a failure: the server, the
client, listeners, plugins, event hooks, and every agent that does not compile in a
container run without it.
