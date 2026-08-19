import asyncio
import datetime
import json
import pathlib

from pydantic import BaseModel, ConfigDict, ValidationError

from consortium.framework.event_hooks import BaseEventHook, EventType

# `Event` is not re-exported from `consortium.framework.event_hooks`, despite being the
# argument type of the `on_triggered` method every hook overrides.
from consortium.framework.event_hooks._event import Event

_CONFIG_FILE_NAME = "config.json"
# Sentinel pushed onto the queue by `on_teardown` to wake the writer and tell it to stop
# once it has drained everything queued ahead of the sentinel.
_STOP = object()


class EventLoggerHookConfigModel(BaseModel):
    # Unknown keys are a typo in a hand-edited config, not an extension point. Rejecting
    # them here turns a silently-ignored setting into a startup failure.
    model_config = ConfigDict(extra="forbid")

    output_file: pathlib.Path
    # None subscribes to every event type. A subset is opt in, so the default records
    # everything and callers narrow it only when they know what they want to drop.
    event_types: set[EventType] | None = None
    # Unbounded by default. A cap trades event loss for memory ceiling, which is a
    # decision for whoever runs the server, not one this hook makes for them.
    queue_max_size: int | None = None


class EventLoggerHook(BaseEventHook):
    label = "event_logger_hook"
    name = "Event Logger Hook"
    description = (
        "Appends every framework event it is subscribed to as newline-delimited JSON, "
        "for offline analysis."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0a1"
    authors = {"Sekiun (github.com/not-sekiun)"}
    # Declared as the full set so subscription is on by default. `on_setup` narrows this
    # to the configured subset, since the class body cannot read the config.
    event_types = set(EventType)

    async def on_setup(self) -> None:
        self.environment.config = self._load_config()
        self.environment.output_file = self._resolve_output_file(
            self.environment.config.output_file
        )

        configured_event_types = self.environment.config.event_types
        if configured_event_types is not None:
            for event_type in set(EventType) - configured_event_types:
                self.unsubscribe_from_event_type(event_type)

        max_size = self.environment.config.queue_max_size
        self.environment.queue = asyncio.Queue(maxsize=max_size or 0)
        self.environment.writer_task = asyncio.create_task(self._write_queued_events())

        self.event_logger.success(
            f"Recording events to {self.environment.output_file}",
            data={
                "output_file": str(self.environment.output_file),
                "subscribed_event_types": len(self.subscribed_event_types),
            },
        )

    async def on_triggered(self, event: Event) -> None:
        # Only ever enqueues, so event dispatch is never blocked on disk. The timestamp
        # is stamped here rather than by the writer: the queue is what decouples the two,
        # so a writer-side timestamp would record when the batch was flushed instead of
        # when the event actually fired.
        record = event.to_json()
        record["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()
        await self.environment.queue.put(record)

    async def on_teardown(self) -> None:
        writer_task = getattr(self.environment, "writer_task", None)
        if writer_task is None:
            return

        await self.environment.queue.put(_STOP)
        await writer_task

    def _load_config(self) -> EventLoggerHookConfigModel:
        config_file = self.root_directory / _CONFIG_FILE_NAME
        try:
            with config_file.open("r", encoding="utf-8") as file:
                return EventLoggerHookConfigModel.model_validate_json(file.read())
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Event logger hook config not found at {config_file}"
            ) from None
        except ValidationError as exc:
            raise ValueError(
                f"Invalid event logger hook config at {config_file}: {exc}"
            ) from None

    def _resolve_output_file(self, output_file: pathlib.Path) -> pathlib.Path:
        # A relative path is taken against the hook's own directory so a default config
        # works without knowing the server's working directory.
        if not output_file.is_absolute():
            output_file = self.root_directory / output_file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        return output_file

    async def _write_queued_events(self) -> None:
        # One writer task owns the handle for the hook's lifetime, so appends are
        # serialised and ordered without a lock, and the file is opened once rather than
        # per event. Writes go through `to_thread` because the handle is a blocking one.
        def append(lines: list[str]) -> None:
            with self.environment.output_file.open("a", encoding="utf-8") as file:
                file.writelines(lines)

        while True:
            record = await self.environment.queue.get()
            if record is _STOP:
                return

            # Everything already queued behind the first record is taken in the same
            # batch, so a burst of events costs one write rather than one per event.
            batch = [record]
            stopping = False
            while not self.environment.queue.empty():
                queued = self.environment.queue.get_nowait()
                if queued is _STOP:
                    stopping = True
                    break
                batch.append(queued)

            lines = [json.dumps(entry) + "\n" for entry in batch]
            try:
                await asyncio.to_thread(append, lines)
            except OSError as exc:
                # A failed write must not kill the writer, or every later event would
                # queue up unwritten behind a task that is no longer draining.
                self.event_logger.error(
                    f"Failed to append {len(lines)} event(s): {exc}",
                    data={"output_file": str(self.environment.output_file)},
                )

            if stopping:
                return
