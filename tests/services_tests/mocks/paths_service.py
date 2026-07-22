import pathlib
from unittest.mock import MagicMock

# Repo root, resolved from tests/services_tests/mocks/paths_service.py
_CONSORTIUM_ROOT = pathlib.Path(__file__).resolve().parents[3]


def make_mock_paths_service(
    *,
    consortium_root: pathlib.Path = _CONSORTIUM_ROOT,
    plugins_directory: pathlib.Path | None = None,
    event_hooks_directory: pathlib.Path | None = None,
    agents_directory: pathlib.Path | None = None,
    listeners_directory: pathlib.Path | None = None,
) -> MagicMock:
    # Lightweight stand-in for PathsService. Threads real filesystem paths into the
    # services under test without triggering the real PathsService startup validation
    # and directory auto-creation side effects. Only the attributes a service actually
    # reads need to be provided; the rest remain unconfigured MagicMock attributes.
    paths_service = MagicMock()
    paths_service.consortium_root = consortium_root
    paths_service.plugins_directory = plugins_directory
    paths_service.event_hooks_directory = event_hooks_directory
    paths_service.agents_directory = agents_directory
    paths_service.listeners_directory = listeners_directory
    return paths_service
