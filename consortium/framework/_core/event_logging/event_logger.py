import uuid
from typing import Any

from consortium.framework._core.event_logging.event_log import EventLog
from consortium.framework._core.event_logging.event_log_models import (
    CurrentProgressModel,
    EventLogEntryModel,
    EventLogEntryType,
)


class EventLogger:
    # loguru has no native FAILURE or ARTIFACT level, so they're mapped to the
    # closest equivalent. Adjust this mapping if a different one is preferred.
    _LOGURU_LEVELS: dict[EventLogEntryType, str] = {
        EventLogEntryType.SUCCESS: "SUCCESS",
        EventLogEntryType.INFO: "INFO",
        EventLogEntryType.WARNING: "WARNING",
        EventLogEntryType.FAILURE: "ERROR",
        EventLogEntryType.ERROR: "CRITICAL",
        EventLogEntryType.ARTIFACT: "INFO",
    }

    def __init__(
        self,
        event_log: EventLog,
        logger: Any = None,
        mirror_to_logger: bool = True,
    ):
        self.mirror_to_logger = mirror_to_logger

        self._event_log = event_log
        self._logger = logger

    def _mirror_entry(
        self,
        entry_type: EventLogEntryType,
        message: str,
        mirror_to_logger: bool | None,
    ) -> None:
        should_log = (
            mirror_to_logger if mirror_to_logger is not None else self.mirror_to_logger
        )
        if should_log and self._logger is not None:
            self._logger.log(self._LOGURU_LEVELS[entry_type], message)

    def log_event(
        self,
        event_type: EventLogEntryType,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log an event of any type to the event log and optionally mirror it to the
        system logger.

        Args:
            event_type: The type of event to log.
            message: Human-readable message to record.
            data: Optional structured data to include with the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.log_event(event_type=event_type, message=message, data=data)
        self._mirror_entry(event_type, message, mirror_to_logger)

    def success(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log a SUCCESS event to the event log and optionally mirror it to the
        system logger.

        Args:
            message: Human-readable description of the successful action or result.
            data: Optional structured data to include with the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.success(message=message, data=data)
        self._mirror_entry(EventLogEntryType.SUCCESS, message, mirror_to_logger)

    def failure(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log a FAILURE event to the event log and optionally mirror it to the
        system logger.

        Args:
            message: Human-readable description of the failure condition.
            data: Optional structured diagnostic data to include with the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.failure(message=message, data=data)
        self._mirror_entry(EventLogEntryType.FAILURE, message, mirror_to_logger)

    def info(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log an INFO event to the event log and optionally mirror it to the
        system logger.

        Args:
            message: Human-readable informational message to record.
            data: Optional structured data to include with the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.info(message=message, data=data)
        self._mirror_entry(EventLogEntryType.INFO, message, mirror_to_logger)

    def warning(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log a WARNING event to the event log and optionally mirror it to the
        system logger.

        Args:
            message: Human-readable warning message to record.
            data: Optional structured data to include with the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.warning(message=message, data=data)
        self._mirror_entry(EventLogEntryType.WARNING, message, mirror_to_logger)

    def artifact(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log an ARTIFACT event to the event log and optionally mirror it to the
        system logger.

        Used to signal that a file, binary blob, or other collectible output was
        produced.

        Args:
            message: Human-readable description or filename of the artifact.
            data: Optional structured metadata to attach to the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.artifact(message=message, data=data)
        self._mirror_entry(EventLogEntryType.ARTIFACT, message, mirror_to_logger)

    def error(
        self,
        message: str,
        data: dict[str, Any] | None = None,
        mirror_to_logger: bool | None = None,
    ) -> None:
        """Log an ERROR event to the event log and optionally mirror it to the
        system logger.

        Args:
            message: Human-readable error message to record.
            data: Optional structured data to include with the event.
            mirror_to_logger: Overrides the instance default for this call.
        """
        self._event_log.error(message=message, data=data)
        self._mirror_entry(EventLogEntryType.ERROR, message, mirror_to_logger)

    def update_progress(
        self,
        percent_complete: float = 0,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Report a partial progress update on the event log.

        Args:
            percent_complete: Completion percentage as a value from 0.0 to 100.0.
            message: Optional human-readable status message to accompany the update.
            data: Optional structured data to include with the progress update.
        """
        self._event_log.update_progress(
            percent_complete=percent_complete, message=message, data=data
        )

    def clear_progress(self) -> None:
        """Clear the current progress update on the event log."""
        self._event_log.clear_progress()

    def get_events(
        self, limit: int = 10, offset: int | None = None
    ) -> list[EventLogEntryModel]:
        """Retrieve events from the event log.

        Args:
            limit: Maximum number of event log entries to return.
            offset: Sequence offset to start from
        """
        return self._event_log.get_events(limit=limit, offset=offset)

    def to_json(self, limit: int = 10, offset: int | None = None) -> dict[str, Any]:
        """Serialize the wrapped log to a JSON-compatible dict.

        Args:
            limit: Maximum number of entries to include.
            offset: Sequence offset to start from; see :class:`EventLog`.
        """
        return self._event_log.to_json(limit=limit, offset=offset)

    @property
    def subject_id(self) -> uuid.UUID:
        """The UUID of the subject this log is attached to."""
        return self._event_log.subject_id

    @property
    def current_progress(self) -> CurrentProgressModel | None:
        """The most recently reported progress update, if any."""
        return self._event_log.current_progress

    @property
    def total_count(self) -> int:
        """Total number of entries in the wrapped log."""
        return self._event_log.total_count
