import io
import sys

import pytest
from loguru import logger

from consortium.server.models.logging_models import LoggingConfigModel
from consortium.server.services.logging_service import LoggingService


@pytest.fixture(autouse=True)
def clean_loguru():
    # LoggingService.__init__ calls logger.remove() at the start, but we also clean up
    # after each test so stale handlers never bleed into the next test.
    yield
    logger.remove()


# ---------------------------------------------------------------------------
# add_sink
# ---------------------------------------------------------------------------


def test_add_sink_returns_int_handler_id():
    service = LoggingService()
    handler_id = service.add_sink(sink=io.StringIO(), level="DEBUG", label="test")
    assert isinstance(handler_id, int)


def test_add_sink_stores_correct_sink_info():
    service = LoggingService()
    sink = io.StringIO()
    service.add_sink(sink=sink, level="DEBUG", label="test")
    sinks = service.get_sinks()
    assert len(sinks) == 1
    info = sinks[0]
    assert info.label == "test"
    assert info.sink is sink
    assert info.level == "DEBUG"
    assert info.is_server_default is False


def test_add_sink_duplicate_label_raises():
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="test")
    with pytest.raises(ValueError, match="already registered"):
        service.add_sink(sink=io.StringIO(), level="INFO", label="test")


def test_add_sink_server_default_flag_stored():
    service = LoggingService()
    service.add_sink(
        sink=io.StringIO(), level="INFO", label="default", is_server_default=True
    )
    assert service.get_sinks()[0].is_server_default is True


def test_add_sink_kwargs_stored_in_sink_info():
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="WARNING", label="test", colorize=False)
    info = service.get_sinks()[0]
    assert info.sink_kwargs["level"] == "WARNING"
    assert info.sink_kwargs["colorize"] is False


# ---------------------------------------------------------------------------
# remove_sink
# ---------------------------------------------------------------------------


def test_remove_sink_removes_from_registry():
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="test")
    service.remove_sink("test")
    assert service.get_sinks() == []


def test_remove_sink_unknown_label_raises():
    service = LoggingService()
    with pytest.raises(KeyError):
        service.remove_sink("nonexistent")


# ---------------------------------------------------------------------------
# get_sinks
# ---------------------------------------------------------------------------


def test_get_sinks_returns_all_registered():
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="a")
    service.add_sink(sink=io.StringIO(), level="INFO", label="b")
    labels = {info.label for info in service.get_sinks()}
    assert labels == {"a", "b"}


def test_get_sinks_returns_empty_when_none_added():
    service = LoggingService()
    assert service.get_sinks() == []


# ---------------------------------------------------------------------------
# modify_sink
# ---------------------------------------------------------------------------


def test_modify_sink_updates_level():
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="test")
    service.modify_sink("test", level="WARNING")
    info = service.get_sinks()[0]
    assert info.level == "WARNING"
    assert info.sink_kwargs["level"] == "WARNING"


def test_modify_sink_changes_sink_target():
    service = LoggingService()
    old_sink = io.StringIO()
    new_sink = io.StringIO()
    service.add_sink(sink=old_sink, level="DEBUG", label="test")
    service.modify_sink("test", sink=new_sink)
    info = service.get_sinks()[0]
    assert info.sink is new_sink


def test_modify_sink_preserves_unmodified_kwargs():
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="test", colorize=False)
    service.modify_sink("test", level="INFO")
    info = service.get_sinks()[0]
    assert info.sink_kwargs.get("colorize") is False
    assert info.sink_kwargs["level"] == "INFO"


def test_modify_sink_successive_calls_layer_correctly():
    # Each modify_sink must build on the previous state, not reset to the original.
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="test")
    service.modify_sink("test", level="INFO")
    service.modify_sink("test", level="WARNING")
    assert service.get_sinks()[0].level == "WARNING"


def test_modify_sink_unknown_label_raises():
    service = LoggingService()
    with pytest.raises(KeyError):
        service.modify_sink("nonexistent", level="INFO")


def test_modify_sink_handler_id_changes_after_modify():
    # loguru assigns a new int on each logger.add() call; after modify the old ID is gone.
    service = LoggingService()
    service.add_sink(sink=io.StringIO(), level="DEBUG", label="test")
    original_id = service.get_sinks()[0].handler_id
    service.modify_sink("test", level="INFO")
    new_id = service.get_sinks()[0].handler_id
    assert new_id != original_id


# ---------------------------------------------------------------------------
# configure_default_logging
# ---------------------------------------------------------------------------


def test_configure_default_logging_registers_stdout_as_server_default():
    service = LoggingService()
    config = LoggingConfigModel(
        level="DEBUG", log_file=None, rotation=None, retention=None, colorize=False
    )
    service.configure_default_logging(config)
    sinks = {info.label: info for info in service.get_sinks()}
    assert "stdout" in sinks
    assert sinks["stdout"].is_server_default is True
    assert sinks["stdout"].sink is sys.stdout


def test_configure_default_logging_no_file_sink_when_log_file_is_none():
    service = LoggingService()
    config = LoggingConfigModel(
        level="INFO", log_file=None, rotation=None, retention=None, colorize=False
    )
    service.configure_default_logging(config)
    labels = {info.label for info in service.get_sinks()}
    assert "file" not in labels


def test_configure_default_logging_registers_file_sink_as_server_default(tmp_path):
    service = LoggingService()
    log_path = str(tmp_path / "test.log")
    config = LoggingConfigModel(
        level="INFO",
        log_file=log_path,
        rotation=None,
        retention=None,
        colorize=False,
    )
    service.configure_default_logging(config)
    sinks = {info.label: info for info in service.get_sinks()}
    assert "file" in sinks
    assert sinks["file"].is_server_default is True


def test_configure_default_logging_respects_level():
    service = LoggingService()
    config = LoggingConfigModel(
        level="ERROR", log_file=None, rotation=None, retention=None, colorize=False
    )
    service.configure_default_logging(config)
    assert service.get_sinks()[0].level == "ERROR"
