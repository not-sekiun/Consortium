from fastapi import FastAPI
from loguru import logger

from consortium.server.server_event_handlers import lifespan


class ApplicationService:
    def __init__(self):
        self._application = FastAPI(
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
            lifespan=lifespan,
        )
        self.application_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.application_service_logger.debug(
            f"Started {self}",
        )

    def get_application(self) -> FastAPI:
        self.application_service_logger.debug("Retrieved application.")
        return self._application

    def __str__(self) -> str:
        return "Application Service"

    def __repr__(self) -> str:
        return "ApplicationService()"

    # TODO: Consider if we should just move the REST API to a plugin instead.
