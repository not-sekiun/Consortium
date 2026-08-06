#!/usr/bin/env python3
"""
update_release.py

Bumps the project version and keeps pyproject.toml and data/release.json in
sync. Lives in /tools; pyproject.toml is at the repo root; release.json is
at /data/release.json (both resolved relative to this script's location).

Default behavior (no --version given):
    - If the current version is a pre-release (a/b/rc), bump the
      pre-release counter (e.g. 0.1.0a1 -> 0.1.0a2).
    - Otherwise, bump the patch number (e.g. 0.1.0 -> 0.1.1).

You can override with --version, which is validated against PEP 440 via
`packaging.version.Version` (raises if invalid).

If the major or minor segment changes relative to the current version,
you'll be prompted for a new codename. Otherwise the existing codename
carries over unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import tomlkit
from packaging.version import InvalidVersion, Version

# --- Paths -------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
RELEASE_JSON_PATH = REPO_ROOT / "data" / "release.json"


# --- Version helpers -----------------------------------------------------


def default_bump(current: Version) -> Version:
    """Lowest-level bump: increment pre-release counter if present,
    otherwise increment the patch number."""
    if current.pre is not None:
        phase, num = current.pre
        release_str = ".".join(str(part) for part in current.release)
        return Version(f"{release_str}{phase}{num + 1}")

    release = list(current.release)
    while len(release) < 3:
        release.append(0)
    release[-1] += 1
    return Version(".".join(str(part) for part in release))


def parse_user_version(raw: str) -> Version:
    try:
        return Version(raw)
    except InvalidVersion as exc:
        print(f"error: '{raw}' is not a valid PEP 440 version: {exc}", file=sys.stderr)
        sys.exit(1)


def major_minor_changed(old: Version, new: Version) -> bool:
    def pad(v: Version) -> tuple[int, int]:
        rel = list(v.release) + [0, 0]
        return rel[0], rel[1]

    return pad(old) != pad(new)


# --- File I/O ------------------------------------------------------------


def load_release_json(path: Path) -> dict:
    if not path.exists():
        print(f"error: release file not found at {path}", file=sys.stderr)
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_release_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.write("\n")


def update_pyproject_version(path: Path, new_version: str) -> None:
    if not path.exists():
        print(f"error: pyproject.toml not found at {path}", file=sys.stderr)
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())

    if "project" in doc and "version" in doc["project"]:
        doc["project"]["version"] = new_version
    elif (
        "tool" in doc and "poetry" in doc["tool"] and "version" in doc["tool"]["poetry"]
    ):
        doc["tool"]["poetry"]["version"] = new_version
    else:
        print(
            "error: could not find a [project].version or "
            "[tool.poetry].version field in pyproject.toml",
            file=sys.stderr,
        )
        sys.exit(1)

    with path.open("w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))


def prompt_for_codename(new_version: Version) -> str:
    while True:
        codename = input(
            f"Major/minor changed -> enter a new codename for v{new_version}: "
        ).strip()
        if codename:
            return codename
        print("Codename can't be empty.")


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- Main ------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump project version and codename.")
    parser.add_argument(
        "--version",
        dest="version",
        help="Explicit version to set (must be PEP 440 compliant). "
        "If omitted, the lowest-level bump is computed automatically.",
    )
    args = parser.parse_args()

    release_data = load_release_json(RELEASE_JSON_PATH)
    current_version = parse_user_version(release_data["version"])

    if args.version:
        new_version = parse_user_version(args.version)
    else:
        new_version = default_bump(current_version)

    if major_minor_changed(current_version, new_version):
        codename = prompt_for_codename(new_version)
    else:
        codename = release_data["codename"]

    new_version_str = str(new_version)

    print(f"Current version: {current_version}  ({release_data['codename']})")
    print(f"New version:     {new_version_str}  ({codename})")
    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted, no files changed.")
        return

    release_data["version"] = new_version_str
    release_data["codename"] = codename
    release_data["datetime_released"] = utc_now_iso()

    write_release_json(RELEASE_JSON_PATH, release_data)
    update_pyproject_version(PYPROJECT_PATH, new_version_str)

    print(f"Updated {RELEASE_JSON_PATH}")
    print(f"Updated {PYPROJECT_PATH}")


if __name__ == "__main__":
    main()
