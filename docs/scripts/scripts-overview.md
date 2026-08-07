# Scripts Overview

The `scripts/` directory holds standalone developer utilities that support working on
Consortium. They are not part of the running server or client: each is a small,
self-contained program you invoke by hand from the repository root.

Most are Python programs, run with `uv` so that the project environment and its
dependencies are available:

```
uv run python scripts/<script_name>.py
```

The two install scripts are the exception. They exist to put the prerequisites for a
manual install in place, uv among them, so they cannot be run through uv and are shell
scripts rather than Python ones.

## Available scripts

| Script                                                                               | Purpose                                                                                                                                                                                                                                                                                                    |
|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`install.ps1`](install-ps1.md)                                                      | Installs the prerequisites for a manual install on Windows with winget: checks for Python 3.14+, Git, uv and Docker Desktop (and whether the Docker engine is running), reports what is found and missing, asks before installing the missing ones, then offers to run `uv sync --all-packages`.           |
| [`install.sh`](install-sh.md)                                                        | The same for Debian based Linux (`apt`) and macOS (Homebrew, installed first when missing).                                                                                                                                                                                                                |
| [`manage_components.py`](manage-components.md)                                       | Interactive component project manager for framework components (plugin, agent profile, listener profile, or event hook) under `consortium/components/`: scaffold new components, enable/disable and inspect existing ones, install from a local directory, git repository, or HTTP archive, and uninstall. |
| [`manage_repository.py`](manage-repository.md)                                       | Interactive tool to browse the server's `assets`, `artifacts`, and `payloads` repositories under `data/server/`: inspect file metadata, open or delete individual files, and clear or hard reset each `.repository.json`-backed repository.                                                                |
| [`generate_distilled_mitre_attack_data.py`](generate-distilled-mitre-attack-data.md) | Downloads the MITRE ATT&CK dataset and distills it into a compact JSON file the server uses.                                                                                                                                                                                                               |

Each script is documented on its own page linked above.
