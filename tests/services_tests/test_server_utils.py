import os

import pytest

from consortium.server.utils import atomic_write_bytes


def test_atomic_write_bytes_writes_data_and_returns_count(tmp_path):
    path = tmp_path / "data.json"

    written = atomic_write_bytes(path, b"hello world")

    assert path.read_bytes() == b"hello world"
    assert written == len(b"hello world")
    # The temp file is replaced, not left behind, on success.
    assert not (tmp_path / "data.json.tmp").exists()


def test_atomic_write_bytes_leaves_original_intact_on_failure(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    path.write_bytes(b"original")

    def failing_replace(src, dst):
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError):
        atomic_write_bytes(path, b"new content")

    # The atomic replace never happened, so the original file is untouched.
    assert path.read_bytes() == b"original"
