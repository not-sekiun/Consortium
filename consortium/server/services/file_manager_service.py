from loguru import logger


class FileManagerService:
    def __init__(self):
        self.file_manager_service_logger = logger.bind(
            service=str(self),
        )

    def __str__(self) -> str:
        return "File Manager Service"

    def __repr__(self) -> str:
        return "FileManagerService()"

    # TODO: Implement the file manager. 😡😡😡
