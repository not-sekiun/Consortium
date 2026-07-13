# clear_repository.py

`clear_repository.py` is an interactive tool for emptying the server's resource
repositories: `assets`, `artifacts`, and `payloads` under `data/server/`. Each repository
stores its files alongside a `.repository.json` metadata index (and a `.keep` placeholder
that keeps the otherwise-empty directory tracked in git). This script removes the stored
files and resets the index, so you can return a repository to a clean state without
editing anything by hand.

## Running the tool

Run it from the repository root in an interactive terminal (it uses selection menus, so it
needs a real TTY):

```
uv run python scripts/clear_repository.py
```

## What it does

You answer a short series of prompts: first the clear mode, then which repositories to
clear (all are pre-selected). The tool prints the full plan for every selected repository
and asks for a final confirmation (defaulting to **No**) before deleting anything. All
three repositories share the same metadata schema, so the tool treats them identically;
the per-entry `data` field holding domain-specific metadata is never inspected.

### Clear modes

- **Normal clear** removes only the files listed in `.repository.json`, read explicitly
  from the index. Each entry's on-disk file is resolved as `<resource_id><extension>`.
  Entries whose backing file is missing are reported as **stale** and skipped. Untracked
  files (anything on disk that the index does not reference) are left untouched. After the
  files are removed, `.repository.json` is reset to an empty object (`{}`).
- **Hard clear** removes every entry in the repository directory, including untracked
  files, restoring the default state of just `.keep` and an empty `.repository.json`.

In both modes `.keep` and `.repository.json` are protected: `.keep` is preserved (and
recreated if absent) and the index is reset in place rather than deleted.

### Review before deletion

For each selected repository the tool prints a table before anything is removed:

- **Normal clear** lists the tracked resources with their display name, on-disk file,
  size, and status (`clear` or `stale (skip)`).
- **Hard clear** lists every on-disk entry that will be removed, tracked or not.

A summary panel then shows the mode, the selected repositories, and the total number of
files to remove. Deletion only proceeds if you confirm; otherwise nothing is changed. A
missing or unparseable `.repository.json` is treated as an empty index (with a warning),
so a broken repository can still be hard cleared.
