import os
from pathlib import Path


def ensure_within_root(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> Path:
    """Resolve a path and verify that it is contained by a root directory.

    Args:
        path: Path to resolve and validate.
        root: Directory that must contain the resolved path.

    Returns:
        The resolved path.

    Raises:
        ValueError: If the resolved path is outside the resolved root directory.
    """
    resolved_path = Path(path).resolve()
    resolved_root = Path(root).resolve()

    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"{resolved_path} is outside {resolved_root}") from error

    return resolved_path


def unique_path(path: str | os.PathLike[str]) -> Path:
    """Return a path that does not currently exist.

    Args:
        path: Preferred path to use.

    Returns:
        The preferred path when available, otherwise a suffixed alternative path.
    """
    requested_path = Path(path)
    if not requested_path.exists():
        return requested_path

    suffix = requested_path.suffix
    stem = requested_path.stem
    parent = requested_path.parent
    index = 1

    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1
