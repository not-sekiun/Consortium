# manage_repository.py

`manage_repository.py` is an interactive tool for inspecting and maintaining the server's
resource repositories: `assets`, `artifacts`, and `payloads` under `data/server/`. Each
repository stores its files alongside a `.repository.json` metadata index (and a `.gitkeep`
placeholder that keeps the otherwise-empty directory tracked in git). The tool lets you
browse a repository, view the metadata for any file, open or delete individual files, and
clear or hard reset the whole repository, all without editing anything by hand.

## Running the tool

Run it from the repository root in an interactive terminal (it uses selection menus, so it
needs a real TTY):

```
uv run python scripts/manage_repository.py
```

## What it does

The tool opens on a repository picker that lists each repository with a quick summary
(tracked file count, untracked file count, and total size). Selecting one opens a menu of
actions; you can move between repositories and actions freely and leave with **Exit**. All
three repositories share the same metadata schema, so the tool treats them identically.

### Browsing files and metadata

**Browse files and metadata** lists every entry in the repository. Each row shows the
name, whether it is a file or directory, its size, and a status:

- **tracked** files are referenced by `.repository.json` and backed by a file on disk.
- **stale** entries are tracked in the index but their backing file is missing.
- **untracked** files exist on disk but are not referenced by the index.
- **malformed** entries are index entries that are not valid objects.

Selecting a file shows its full metadata. For tracked files this includes the resource ID,
name, description, on-disk file, size, extension, timestamps, and MD5 checksum. The MD5
checksum is only stored in the index when explicitly requested, so when it is absent the
tool computes it on demand from the on-disk resource (marked `(computed)`), using the same
algorithm as the framework: a chunked hash for files, and for directories a folded hash of
each entry's relative path and content. The per-entry `data` field holds domain-specific
metadata that varies by repository, so it is rendered generically as pretty-printed JSON
rather than parsed field by field. Untracked files have no metadata, so only basic on-disk
facts are shown.

### Opening and deleting files

From a file's view you can:

- **Open in default viewer** hands the file to the platform's default application. This
  works cross-platform (`os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux);
  if no opener is available the tool reports it instead of failing.
- **Delete this file** removes the file from disk and, when the file is tracked, drops its
  entry from `.repository.json`. Deletion always asks for confirmation (defaulting to
  **No**).

### Clearing and hard resetting

Two repository-wide actions remove files in bulk. Both print the full plan and ask for a
final confirmation (defaulting to **No**) before deleting anything.

- **Clear** removes only the files listed in `.repository.json`, read explicitly from the
  index. Each entry's on-disk file is resolved as `<resource_id><extension>`. Stale
  entries are skipped and untracked files are left untouched. Afterwards the index is reset
  to an empty object (`{}`).
- **Hard reset** removes every entry in the repository directory, including untracked
  files, restoring the default state of just `.gitkeep` and an empty `.repository.json`.

In both actions `.gitkeep` and `.repository.json` are protected: `.gitkeep` is preserved (and
recreated if absent) and the index is reset in place rather than deleted. A missing or
unparseable `.repository.json` is treated as an empty index (with a warning), so a broken
repository can still be inspected or hard reset.
