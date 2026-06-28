import sys
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from consortium.server.models.logging_models import LoggerType, LoggingConfigModel

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

    def __str__(self) -> str:
        return "Logging Service"

    def __repr__(self) -> str:
        return "LoggingService()"

    @staticmethod
    def _log_formatter(record):
        logger_type_to_color_str_map = {
            LoggerType.LISTENER_LOGGER: "<bold><blue>",
            LoggerType.AGENT_LOGGER: "<bold><red>",
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

        # Can't use f-string here because of the loguru syntax. Also, we need to add
        # the newline character at the end of the string for formatter functions.
        return (
            "<dim><white>{time:YYYY-MM-DDTHH:mm:ss.SSSZ}</></> <level>{level:<8}</> "
            + color
            + "{extra[logger_name]}</></>: {message}\n{exception}"
        )

    def add_sink(
        self,
        sink: Any,
        level: str,
        label: str,
        *,
        format=None,
        is_server_default: bool = False,
        **kwargs,
    ) -> int:
        """Adds a new log sink to the logging service.

        All additional keyword arguments are forwarded directly to `loguru.logger.add`.

        Args:
            sink (Any): The sink target (e.g. `sys.stdout`, a file path, or a callable).
            level (str): The minimum log level for this sink (e.g. `"DEBUG"`,
                `"INFO"`).
            label (str): A unique label for identifying and referencing this sink.
            format: A loguru format string or callable. When `None`, the service's
                default formatter is used.
            is_server_default (bool): When `True`, marks this sink as a server-default
                sink. Defaults to `False`.
            **kwargs: Additional keyword arguments passed to `loguru.logger.add`.

        Returns:
            int: The handler ID returned by `loguru.logger.add`.

        Raises:
            ValueError: If a sink with the given label is already registered.
        """
        # Raises ValueError if label already registered to avoid silent double-registration.
        if label in self._sinks:
            raise ValueError(f"A sink with label '{label}' is already registered.")

        if format is None:
            format = self._log_formatter

        # Consolidate all logger.add() params so modify_sink can reconstruct faithfully.
        sink_kwargs = {"level": level, "format": format, **kwargs}
        handler_id = logger.add(sink, **sink_kwargs)
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
            label (str): The label of the sink to remove.

        Returns:
            None

        Raises:
            KeyError: If no sink with the given label is registered.
        """
        if label not in self._sinks:
            raise KeyError(f"No sink with label '{label}' is registered.")
        sink_info = self._sinks.pop(label)
        logger.remove(sink_info.handler_id)

    def modify_sink(self, label: str, *, sink: Any = _UNSET, **overrides) -> None:
        """Modifies an existing log sink in-place by rebuilding it with updated parameters.

        Because loguru provides no update API, the existing sink is torn down and
        reconstructed with the merged configuration. Successive calls layer correctly
        because `SinkInfo.sink_kwargs` is kept up to date after each modification.

        Args:
            label (str): The label of the sink to modify.
            sink (Any): A replacement sink target. When omitted, the existing sink
                target is preserved.
            **overrides: Any additional loguru `logger.add` keyword arguments to update.
                Provided values are merged over the existing sink kwargs.

        Returns:
            None

        Raises:
            KeyError: If no sink with the given label is registered.
        """
        # Loguru has no update API so we tear down the existing handler and rebuild it
        # with the merged kwargs. sink_kwargs on SinkInfo is kept up to date so
        # successive modify_sink calls layer correctly.
        if label not in self._sinks:
            raise KeyError(f"No sink with label '{label}' is registered.")

        info = self._sinks[label]
        logger.remove(info.handler_id)

        new_sink = info.sink if sink is _UNSET else sink
        new_kwargs = {**info.sink_kwargs, **overrides}

        info.handler_id = logger.add(new_sink, **new_kwargs)
        info.sink = new_sink
        info.level = new_kwargs.get("level", info.level)
        info.sink_kwargs = new_kwargs

    def get_all_sinks(self) -> list[SinkInfo]:
        """Returns all currently registered log sinks.

        Returns:
            list[SinkInfo]: A list of `SinkInfo` objects for all registered sinks.
                Empty if none have been added.
        """
        return list(self._sinks.values())

    def configure_default_logging(self, logging_config: LoggingConfigModel) -> None:
        """Configures default log level colors and registers the server's default sinks.

        Sets display colors for each log level and adds a `stdout` sink. A file sink is
        also added when `logging_config.log_file` is not `None`.

        Args:
            logging_config (LoggingConfigModel): The logging configuration model
                specifying the log level, colorize flag, and optional log file path,
                rotation policy, and retention policy.

        Returns:
            None
        """
        self.logging_config = logging_config

        # Set display colors per log level.
        logger.level("TRACE", color="<dim><magenta>")
        logger.level("DEBUG", color="<bold><cyan>")
        logger.level("INFO", color="<bold><blue>")
        logger.level("WARNING", color="<bold><yellow>")
        logger.level("ERROR", color="<bold><red>")
        logger.level("CRITICAL", color="<white><RED><bold>")
        logger.level("SUCCESS", color="<bold><green>")

        self.add_sink(
            sink=sys.stdout,
            level=logging_config.level,
            label="stdout",
            colorize=logging_config.colorize,
            is_server_default=True,
        )

        if logging_config.log_file is not None:
            self.add_sink(
                sink=logging_config.log_file,
                level=logging_config.level,
                label="file",
                format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} {level:<8} {extra[logger_name]}: {message}",
                colorize=False,
                rotation=logging_config.rotation,
                retention=logging_config.retention,
                is_server_default=True,
            )

        self._logger.debug("Started {}", self)
