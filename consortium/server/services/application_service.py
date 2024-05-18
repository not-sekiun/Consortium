from fastapi import FastAPI
from loguru import logger


class ApplicationService:
    def __init__(self):
        self._application = FastAPI(
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
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
        return "Consortium Application Service"

    def __repr__(self) -> str:
        return "ApplicationService()"
