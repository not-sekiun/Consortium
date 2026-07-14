# Scripts Overview

The `scripts/` directory holds standalone developer utilities that support working on
Consortium. They are not part of the running server or client: each is a small,
self-contained program you invoke by hand from the repository root with `uv`, which
ensures the project environment and its dependencies are available:

```
uv run python scripts/<script_name>.py
```

## Available scripts

| Script                                | Purpose                                                                    |
|---------------------------------------|----------------------------------------------------------------------------|
| [`create_component_project.py`](create-component-project.md) | Interactive scaffolder that generates a new framework component (plugin, agent profile, listener profile, or event hook) under `consortium/components/`. |
| [`manage_repository.py`](manage-repository.md) | Interactive tool to browse the server's `assets`, `artifacts`, and `payloads` repositories under `data/server/`: inspect file metadata, open or delete individual files, and clear or hard reset each `.repository.json`-backed repository. |
| [`generate_distilled_mitre_attack_data.py`](generate-distilled-mitre-attack-data.md) | Downloads the MITRE ATT&CK dataset and distills it into a compact JSON file the server uses. |

Each script is documented on its own page linked above.
