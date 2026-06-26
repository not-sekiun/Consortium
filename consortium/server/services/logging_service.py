from loguru import logger

from consortium.server.server_logging import LoggerType, LoggingConfigModel


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

    def configure_logger(self, logging_config: LoggingConfigModel) -> None:
        logger.remove()
        logger.add(
            sink=self.logging_config.log_file,
            level=self.logging_config.level,
            rotation=self.logging_config.rotation,
            retention=self.logging_config.retention,
            colorize=self.logging_config.colorize,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>",
        )
        self._logger.debug("Configured logger with {}", self.logging_config)
