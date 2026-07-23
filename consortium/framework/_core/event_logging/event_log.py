import uuid

from pydantic import JsonValue

from consortium.framework._core.event_logging.event_log_models import (
    CurrentProgressModel,
    EventLogEntryModel,
    EventLogEntryType,
)


class EventLog:
    def __init__(self, subject_id: uuid.UUID):
        # TODO: To be used in the future as a foreign key when transitioning to using a
        #  SQL style database
        self.subject_id = subject_id
        self.current_progress: CurrentProgressModel | None = None

        self._events = []  # TODO: Move to a SQL style database
        self._sequence = 0

    @property
    def total_count(self) -> int:  # TODO: Make it a query to a SQL style database
        return len(self._events)

    def get_events(
        self, limit: int = 10, offset: int | None = None
    ) -> list[EventLogEntryModel]:  # TODO: Make it a query to a SQL style database
        total_count = len(self._events)

        if total_count == 0:
            filtered_events = []
        else:
            # Get min and max sequence numbers
            sequences = [event.sequence for event in self._events]
            min_seq = min(sequences)
            max_seq = max(sequences)

            # If offset is None, return the tail (entries with highest sequence numbers)
            if offset is None:
                # Get entries with the highest sequence numbers, up to limit
                start_seq = max(min_seq, max_seq - limit + 1)
                filtered_events = [
                    event for event in self._events if event.sequence >= start_seq
                ]
                # Sort by sequence and take the last limit entries
                filtered_events = sorted(filtered_events, key=lambda e: e.sequence)[
                    -limit:
                ]
            # Handle negative offset (from max sequence)
            elif offset < 0:
                start_seq = max(min_seq, max_seq + offset + 1)
                end_seq = start_seq + limit - 1
                filtered_events = [
                    event
                    for event in self._events
                    if start_seq <= event.sequence <= end_seq
                ]
                filtered_events = sorted(filtered_events, key=lambda e: e.sequence)
            else:
                # Filter entries where sequence >= offset
                start_seq = offset
                end_seq = offset + limit - 1
                filtered_events = [
                    event
                    for event in self._events
                    if start_seq <= event.sequence <= end_seq
                ]
                filtered_events = sorted(filtered_events, key=lambda e: e.sequence)

        return filtered_events

    def update_progress(
        self,
        percent_complete: float = 0,
        message: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ) -> None:
        self.current_progress = CurrentProgressModel(
            percent_complete=percent_complete,
            message=message,
            data=data or {},
        )

    def clear_progress(self) -> None:
        self.current_progress = None

    def log_event(
        self,
        event_type: EventLogEntryType,
        message: str,
        data: dict[str, JsonValue] | None = None,
    ) -> None:
        self._events.append(
            EventLogEntryModel(
                sequence=self._sequence,
                event_type=event_type,
                message=message,
                data=data or {},
            )
        )
        self._sequence += 1

    def success(self, message: str, data: dict[str, JsonValue] | None = None):
        self.log_event(
            event_type=EventLogEntryType.SUCCESS, message=message, data=data or {}
        )

    def failure(self, message: str, data: dict[str, JsonValue] | None = None):
        self.log_event(
            event_type=EventLogEntryType.FAILURE, message=message, data=data or {}
        )

    def info(self, message: str, data: dict[str, JsonValue] | None = None):
        self.log_event(
            event_type=EventLogEntryType.INFO, message=message, data=data or {}
        )

    def warning(self, message: str, data: dict[str, JsonValue] | None = None):
        self.log_event(
            event_type=EventLogEntryType.WARNING, message=message, data=data or {}
        )

    def error(self, message: str, data: dict[str, JsonValue] | None = None):
        self.log_event(
            event_type=EventLogEntryType.ERROR, message=message, data=data or {}
        )

    def artifact(self, message: str, data: dict[str, JsonValue] | None = None):
        self.log_event(
            event_type=EventLogEntryType.ARTIFACT, message=message, data=data or {}
        )

    def to_json(
        self, limit: int = 10, offset: int | None = None, include_entries: bool = True
    ) -> dict[str, JsonValue]:
        return {
            "current_progress": self.current_progress.model_dump(mode="json")
            if self.current_progress is not None
            else None,
            "total_count": self.total_count,
            # Collection endpoints pass include_entries=False so the potentially large
            # per-resource entry list is dropped; total_count still reports how many
            # entries exist so clients can page them via the detail endpoint.
            "entries": [
                event.model_dump(mode="json")
                for event in self.get_events(limit=limit, offset=offset)
            ]
            if include_entries
            else [],
        }
