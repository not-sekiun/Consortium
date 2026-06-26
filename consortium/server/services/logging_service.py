import sys

from loguru import logger

from consortium.server.models.logging_models import LoggerType, LoggingConfigModel


class LoggingService:
    def __init__(self):
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)
        self.logging_config = LoggingConfigModel(
            level="TRACE",
        )

    def __str__(self) -> str:
        return "Logging Service"

    def __repr__(self) -> str:
        return f"LoggingService(logging_config={self.logging_config!r})"

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

    def configure_logger(self, logging_config: LoggingConfigModel) -> None:
        logger.remove()  # Remove all default loggers.

        # Add file logging if `log_file` is provided
        if logging_config.log_file is not None:
            logger.add(
                logging_config.log_file,
                format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} {level:<8} {extra[logger_name]}: {message}",
                level=logging_config.level,
                rotation=logging_config.rotation,
                retention=logging_config.retention,
                colorize=False,
            )

        # Always log to stdout
        logger.add(
            sys.stdout,
            colorize=logging_config.colorize,
            format=self._log_formatter,
            level=logging_config.level,
        )

        logger.level("TRACE", color="<dim><magenta>")
        logger.level("DEBUG", color="<bold><cyan>")
        logger.level("INFO", color="<bold><blue>")
        logger.level("WARNING", color="<bold><yellow>")
        logger.level("ERROR", color="<bold><red>")
        logger.level("CRITICAL", color="<white><RED><bold>")
        logger.level("SUCCESS", color="<bold><green>")
