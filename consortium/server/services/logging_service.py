import pathlib
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from consortium.server.exceptions.service_exceptions.logging_service_exceptions import (
    SinkConfigurationError,
    SinkFileSystemError,
    SinkLabelAlreadyExistsError,
    SinkNotFoundError,
    StaleSinkHandlerError,
)
from consortium.server.models.logging_models import LoggerType, LoggingConfigModel
from consortium.server.utils import wrap_filesystem_errors

# Sentinel used to distinguish "not passed" from None in modify_sink's sink argument.
# TODO: Transition to using Sentinel() in python 3.15
_UNSET = object()


@dataclass
class SinkInfo:
    handler_id: int
    sink: Any
    level: str
    label: str
    is_server_default: bool
    # All kwargs passed to logger.add() (including format and level) so the sink can be
    # fully reconstructed when modify_sink tears it down and rebuilds it.
    sink_kwargs: dict = field(default_factory=dict)


class LoggingService:
    def __init__(self):
        logger.remove()  # Remove all default loggers.

        self._sinks: dict[str, SinkInfo] = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self.logging_config = LoggingConfigModel()
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Logging Service"

    def __repr__(self) -> str:
        return "LoggingService()"

    @staticmethod
    def _log_formatter(record) -> str:
        logger_type_to_color_str_map = {
            LoggerType.LISTENER_LOGGER: "<bold><blue>",
            LoggerType.AGENT_LOGGER: "<bold><red>",
            LoggerType.AGENT_TASK_LOGGER: "<bold><red>",
            LoggerType.GENERATOR_LOGGER: "<bold><green>",
            LoggerType.EVENT_HOOK_LOGGER: "<bold><yellow>",
            LoggerType.PLUGIN_LOGGER: "<bold><cyan>",
            LoggerType.REST_API_LOGGER: "<bold><magenta>",
            LoggerType.WEBSOCKET_EVENTS_API_LOGGER: "<bold><magenta>",
            LoggerType.SERVICE_LOGGER: "<bold><magenta>",
            LoggerType.SERVER_LOGGER: "<bold><magenta>",
        }

        logger_type = record["extra"].get("logger_type")

        if not logger_type:
            color = "<dim><white>"
        else:
            color = logger_type_to_color_str_map.get(logger_type, "<dim><white>")

        logger_name = record["extra"].get("logger_name") or record["name"]

        # logger_name is resolved here rather than via {extra[logger_name]} in the
        # format string to avoid a KeyError when logging without a bound logger_name.
        # Can't use f-string here because of the loguru syntax. Also, we need to add
        # the newline character at the end of the string for formatter functions.
        return (
            "<dim><white>{time:YYYY-MM-DDTHH:mm:ss.SSSZ}</></> <level>{level:<8}</> "
            + color
            + logger_name
            + "</></>: {message}\n{exception}"
        )

    def _add_sink_to_loguru(
        self,
        sink: Any,
        sink_kwargs: dict,
        label: str,
        operation: str,
    ) -> int:
        # Shared by add_sink and by modify_sink's rebuild and rollback steps. loguru
        # raises OSError only when `sink` is a file path it cannot open, and raises
        # ValueError or TypeError for every other configuration problem (an invalid
        # level, filter, or format string, or a keyword argument of the wrong type).
        # The filesystem check only wraps the call when `sink` is actually a path:
        # a stream or callable sink is not opened by loguru, so an OSError raised by
        # calling it later is not a sink configuration problem this service can
        # explain.
        try:
            if isinstance(sink, (str, pathlib.Path)):
                with wrap_filesystem_errors(
                    SinkFileSystemError, operation=operation, path=str(sink)
                ):
                    return logger.add(sink, **sink_kwargs)
            return logger.add(sink, **sink_kwargs)
        except (ValueError, TypeError) as exc:
            raise SinkConfigurationError(
                operation=operation,
                label=label,
                underlying_error=f"{type(exc).__name__}: {exc}",
            ) from exc

    def add_sink(
        self,
        sink: Any,
        level: str,
        label: str,
        format: str | Callable[[Any], str] | None = None,
        is_server_default: bool = False,
        **kwargs,
    ) -> int:
        """Adds a new log sink to the logging service.

        All additional keyword arguments are forwarded directly to `loguru.logger.add`.

        Args:
            sink: The sink target, for example `sys.stdout`, a file path, or a
                callable.
            level: The minimum log level for this sink, for example `"DEBUG"` or
                `"INFO"`.
            label: A unique label for identifying and referencing this sink.
            format: A loguru format string or callable. When `None`, the service's
                default formatter is used.
            is_server_default: When `True`, marks this sink as a server-default sink.
                Defaults to `False`.
            **kwargs: Additional keyword arguments passed to `loguru.logger.add`.

        Returns:
            The handler ID returned by `loguru.logger.add`.

        Raises:
            SinkLabelAlreadyExistsError: If a sink with the given label is already
                registered.
            SinkConfigurationError: If `loguru.logger.add` rejects the sink
                configuration, for example an invalid level, filter, or format
                string, or `sink` or one of the forwarded keyword arguments is of an
                invalid type.
            SinkFileSystemError: If `sink` is a file path that cannot be opened, for
                example because the containing directory does not exist.
        """
        # Checked before `loguru.logger.add` is ever called to avoid silent
        # double-registration under one label.
        if label in self._sinks:
            raise SinkLabelAlreadyExistsError(label=label)

        if format is None:
            format = self._log_formatter

        # Consolidate all logger.add() params so modify_sink can reconstruct faithfully.
        sink_kwargs = {"level": level, "format": format, **kwargs}
        handler_id = self._add_sink_to_loguru(
            sink=sink, sink_kwargs=sink_kwargs, label=label, operation="add the sink"
        )
        self._sinks[label] = SinkInfo(
            handler_id=handler_id,
            sink=sink,
            level=level,
            label=label,
            is_server_default=is_server_default,
            sink_kwargs=sink_kwargs,
        )
        return handler_id

    def remove_sink(self, label: str) -> None:
        """Removes a registered log sink by its label.

        Args:
            label: The label of the sink to remove.

        Raises:
            SinkNotFoundError: If no sink with the given label is registered.
            StaleSinkHandlerError: If the sink's handler ID is no longer registered
                with loguru.
        """
        if label not in self._sinks:
            raise SinkNotFoundError._during_removal(label=label)
        sink_info = self._sinks.pop(label)
        try:
            logger.remove(sink_info.handler_id)
        except ValueError as exc:
            raise StaleSinkHandlerError(
                operation="remove the sink",
                label=label,
                handler_id=sink_info.handler_id,
                underlying_error=f"{type(exc).__name__}: {exc}",
            ) from exc

    def remove_all_sinks(self) -> None:
        """Removes all registered log sinks.

        Raises:
            StaleSinkHandlerError: If a sink's handler ID is no longer registered with
                loguru (raised via `remove_sink`).
        """
        for label in list(self._sinks.keys()):
            self.remove_sink(label)

    def modify_sink(self, label: str, sink: Any = _UNSET, **overrides) -> None:
        """Modifies an existing log sink in-place by rebuilding it with updated
        parameters.

        Because loguru provides no update API, the existing sink is torn down and
        reconstructed with the merged configuration. Successive calls layer correctly
        because `SinkInfo.sink_kwargs` is kept up to date after each modification.

        The existing handler is removed via `loguru.logger.remove` before the
        replacement is added via `loguru.logger.add`. If rebuilding the replacement
        fails, the sink is re-added with its previous configuration so that logging
        through it continues uninterrupted, and the label keeps pointing at the
        (restored) handler's current ID, before the typed error describing the
        rebuild failure is raised. If that rollback itself fails, the sink is dropped
        from this service's bookkeeping (it is no longer registered with loguru
        either way) and the rollback failure is logged, while the original error is
        still raised to the caller so the reason the modification failed is never
        masked.

        Args:
            label: The label of the sink to modify.
            sink: A replacement sink target. When omitted, the existing sink target is
                preserved.
            **overrides: Additional loguru `logger.add` keyword arguments to update.
                Provided values are merged over the existing sink kwargs.

        Raises:
            SinkNotFoundError: If no sink with the given label is registered.
            StaleSinkHandlerError: If the existing handler's ID is no longer
                registered with loguru.
            SinkConfigurationError: If `loguru.logger.add` rejects the merged
                configuration when rebuilding the sink, for example an invalid level,
                filter, or format string, or the replacement sink or one of the
                merged keyword arguments is of an invalid type.
            SinkFileSystemError: If the replacement sink is a file path that cannot
                be opened.
        """
        # Loguru has no update API so we tear down the existing handler and rebuild it
        # with the merged kwargs. sink_kwargs on SinkInfo is kept up to date so
        # successive modify_sink calls layer correctly.
        if label not in self._sinks:
            raise SinkNotFoundError._during_modification(label=label)

        info = self._sinks[label]
        try:
            logger.remove(info.handler_id)
        except ValueError as exc:
            raise StaleSinkHandlerError(
                operation="modify the sink",
                label=label,
                handler_id=info.handler_id,
                underlying_error=f"{type(exc).__name__}: {exc}",
            ) from exc

        new_sink = info.sink if sink is _UNSET else sink
        new_kwargs = {**info.sink_kwargs, **overrides}

        try:
            new_handler_id = self._add_sink_to_loguru(
                sink=new_sink,
                sink_kwargs=new_kwargs,
                label=label,
                operation="modify the sink",
            )
        except (SinkConfigurationError, SinkFileSystemError) as exc:
            # The old handler is already gone from loguru at this point, so leaving
            # things as they are would silently stop the sink from emitting logs
            # while it stayed registered here under a stale handler_id. Re-add it
            # with its previous configuration so logging keeps working, then still
            # raise the original error: the caller asked to modify the sink and needs
            # to know that failed, even though the sink itself is fine.
            try:
                restored_handler_id = self._add_sink_to_loguru(
                    sink=info.sink,
                    sink_kwargs=info.sink_kwargs,
                    label=label,
                    operation="restore the sink after a failed modification",
                )
            except (SinkConfigurationError, SinkFileSystemError) as rollback_exc:
                # The rollback failed too (for example, the previous config's log
                # file directory was deleted out from under it). There is no
                # configuration left that this service can register for `label`, so
                # bookkeeping for it is dropped rather than kept pointing at a
                # handler_id that no longer exists in loguru. The rollback failure is
                # logged here since nothing else observes it, and the ORIGINAL error
                # (`exc`) is still what gets raised to the caller, chained onto the
                # rollback failure with `from` so both are visible in the traceback:
                # masking `exc` behind the rollback failure would hide the reason the
                # modification itself failed, which is what the caller actually asked
                # about.
                del self._sinks[label]
                self._logger.error(
                    "Failed to roll back sink '{}' to its previous configuration "
                    "after a failed modification. The sink is no longer registered "
                    "with loguru. {}: {}",
                    label,
                    type(rollback_exc).__name__,
                    rollback_exc,
                )
                raise exc from rollback_exc
            info.handler_id = restored_handler_id
            raise exc

        info.handler_id = new_handler_id
        info.sink = new_sink
        info.level = new_kwargs.get("level", info.level)
        info.sink_kwargs = new_kwargs

    def get_all_sinks(self) -> list[SinkInfo]:
        """Returns all currently registered log sinks.

        Returns:
            A list of `SinkInfo` objects for all registered sinks, or an empty list if
            none have been added.
        """
        return list(self._sinks.values())

    def configure_default_logging(self, logging_config: LoggingConfigModel) -> None:
        """Configures default log level colors and registers the server's default
        sinks.

        Sets display colors for each log level and adds a `stdout` sink. A file sink is
        also added when `logging_config.log_file` is not `None`.

        Args:
            logging_config: The logging configuration model specifying the log level,
                colorize flag, and optional log file path, rotation policy, and
                retention policy.

        Raises:
            StaleSinkHandlerError: If a stale handler ID is encountered while removing
                the existing server-default sinks (raised via `remove_sink`).
            SinkLabelAlreadyExistsError: If the `stdout` or `file` label collides with
                an already-registered non-default sink (raised via `add_sink`).
            SinkConfigurationError: If `loguru.logger.add` rejects a sink
                configuration (for example, an invalid level or format string), or a
                sink or one of its keyword arguments is of an invalid type.
            SinkFileSystemError: If `logging_config.log_file` is a path that cannot be
                opened.
        """
        self.logging_config = logging_config

        # Find all server default sinks and remove them first.
        for label in [
            sink_label
            for sink_label, sink in self._sinks.items()
            if sink.is_server_default
        ]:
            self.remove_sink(label)

        # Set display colors per log level.
        logger.level("TRACE", color="<dim><magenta>")
        logger.level("DEBUG", color="<bold><cyan>")
        logger.level("INFO", color="<bold><blue>")
        logger.level("WARNING", color="<bold><yellow>")
        logger.level("ERROR", color="<bold><red>")
        logger.level("CRITICAL", color="<white><RED><bold>")
        logger.level("SUCCESS", color="<bold><green>")

        # Add default stdout logging
        self.add_sink(
            sink=sys.stdout,
            level=logging_config.level,
            format=self._log_formatter,
            label="stdout",
            colorize=logging_config.colorize,
            is_server_default=True,
        )

        # Add default file based logging if specified
        if logging_config.log_file is not None:
            self.add_sink(
                sink=logging_config.log_file,
                level=logging_config.level,
                label="file",
                format=self._log_formatter,
                colorize=False,
                rotation=logging_config.rotation,
                retention=logging_config.retention,
                is_server_default=True,
            )
