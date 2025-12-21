from loguru import logger

from consortium.server.server_logging import LoggerType, LoggingConfigModel


class LoggingService:
    def __init__(self, logging_config: LoggingConfigModel):
        self.logging_config = logging_config
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Logging Service"

    def __repr__(self) -> str:
        return f"LoggingService(logging_config={self.logging_config!r})"
