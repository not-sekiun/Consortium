import pathlib

from loguru import logger

from consortium.server.models.logging_models import LoggerType


class PathsService:
    """Central registry of the filesystem paths the server depends on.

    Resolves and holds every well-known file and directory path relative to the
    consortium project root, so that other services resolve paths through this single
    service rather than recomputing them. On construction, it validates that the user
    accounts file exists and auto-creates any missing expected directories, aborting
    server startup if a path is in an unrecoverable status.

    Attributes:
        consortium_root: The project root directory, resolved as the ancestor three
            levels above this service's module file.
        release_json_file: The release metadata JSON file under `data`.
        server_config_json_file: The server configuration JSON file under `data/server`.
        logging_config_json_file: The logging configuration JSON file under
            `data/server`.
        user_accounts_json_file: The user accounts JSON file under `data/server`. Its
            existence is validated at startup.
        role_permissions_json_file: The role permissions JSON file under `data/server`.
        server_logs_directory: The directory under `data/server` where server log files
            are written.
        assets_directory: The directory under `data/server` where asset resources are
            stored.
        artifacts_directory: The directory under `data/server` where artifact resources
            are stored.
        payloads_directory: The directory under `data/server` where payload resources
            are stored.
        components_directory: The `consortium/components` directory holding user-created
            components that extend the framework.
        listeners_directory: The listeners subdirectory of the components directory.
        agents_directory: The agents subdirectory of the components directory.
        plugins_directory: The plugins subdirectory of the components directory.
        event_hooks_directory: The event hooks subdirectory of the components directory.

    Raises:
        FileNotFoundError: If the user accounts file does not exist at
            `user_accounts_json_file`.
        IsADirectoryError: If a directory exists at `user_accounts_json_file` instead
            of a file.
        NotADirectoryError: If a file exists at the path of one of the expected
            directories instead of a directory.
        PermissionError: If the process lacks permission to create one of the
            expected directories.
        OSError: If resolving the consortium root path, or creating one of the
            expected directories, fails for another operating-system-level reason.
    """

    def __init__(self):
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

        # This service is located at
        # consortium/server/services/paths_service.py, so the consortium
        # root is three levels up relative to it.
        self.consortium_root: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]

        # Data file paths
        self.release_json_file: pathlib.Path = (
            self.consortium_root / "data" / "release.json"
        )
        self.server_config_json_file: pathlib.Path = (
            self.consortium_root / "data" / "server" / "server_config.json"
        )
        self.logging_config_json_file: pathlib.Path = (
            self.consortium_root / "data" / "server" / "logging_config.json"
        )
        self.user_accounts_json_file: pathlib.Path = (
            self.consortium_root / "data" / "server" / "user_accounts.json"
        )
        self.role_permissions_json_file: pathlib.Path = (
            self.consortium_root / "data" / "server" / "role_permissions.json"
        )

        # Data directory paths
        self.server_logs_directory: pathlib.Path = (
            self.consortium_root / "data" / "server" / "logs"
        )
        self.assets_directory: pathlib.Path = (
            self.consortium_root / "data" / "server" / "assets"
        )
        self.artifacts_directory: pathlib.Path = (
            self.consortium_root / "data" / "server" / "artifacts"
        )
        self.payloads_directory: pathlib.Path = (
            self.consortium_root / "data" / "server" / "payloads"
        )

        # Component directory paths
        self.components_directory: pathlib.Path = (
            self.consortium_root / "consortium" / "components"
        )
        self.listeners_directory: pathlib.Path = self.components_directory / "listeners"
        self.agents_directory: pathlib.Path = self.components_directory / "agents"
        self.plugins_directory: pathlib.Path = self.components_directory / "plugins"
        self.event_hooks_directory: pathlib.Path = (
            self.components_directory / "event_hooks"
        )

        # These two methods will raise exceptions that are not subclasses of
        # `BaseConsortiumErrors` if there are issues with the paths that prevent
        # safe server startup. This is to ensure that the server does not start
        # in an invalid status by aborting the startup procedure.
        self._validate_user_accounts_json_file_exist()
        self._auto_create_missing_directories()

        self._logger.debug("Started {}", self)

    def __str__(self):
        return "Paths Service"

    def __repr__(self):
        return "PathsService()"

    def _validate_user_accounts_json_file_exist(self) -> None:
        if not self.user_accounts_json_file.exists():
            raise FileNotFoundError(
                f"Aborted server startup. User accounts file path "
                f"'{self.user_accounts_json_file}' does not exist. Create the file "
                f"before starting the server."
            )
        elif not self.user_accounts_json_file.is_file():
            raise IsADirectoryError(
                f"Aborted server startup. Expected file at "
                f"'{self.user_accounts_json_file}' but found a directory instead. "
                f"Delete or move the directory, replacing it with the corresponding "
                f"file and restart the server."
            )

    def _auto_create_missing_directories(self) -> None:
        expected_directories = [
            self.server_logs_directory,
            self.components_directory,
            self.listeners_directory,
            self.agents_directory,
            self.plugins_directory,
            self.event_hooks_directory,
            self.assets_directory,
            self.artifacts_directory,
            self.payloads_directory,
        ]
        for directory in expected_directories:
            if not directory.exists():
                self._logger.debug(
                    "Automatically created missing directory {}", directory
                )
                directory.mkdir(parents=True, exist_ok=True)
            elif not directory.is_dir():
                raise NotADirectoryError(
                    f"Aborted server startup. Expected directory at '{directory}' but "
                    f"found a file instead. Delete or move the file, replacing it with "
                    f"the corresponding directory and restart the server."
                )
