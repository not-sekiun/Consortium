import pathlib

from loguru import logger

from consortium.server.exceptions.service_exceptions.paths_service_exceptions import (
    ConsortiumDirectoryFileSystemError,
    ConsortiumReleaseFileSystemError,
    ConsortiumRolePermissionsFileSystemError,
    ConsortiumUserAccountsFileSystemError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.utils import wrap_filesystem_errors


class PathsService:
    """Central registry of the filesystem paths the server depends on.

    Resolves and holds every well-known file and directory path relative to the
    consortium project root, so that other services resolve paths through this single
    service rather than recomputing them. Construction only resolves paths, it performs
    no filesystem validation. Call `_run_preflight_path_validations` once, at server
    boot, to validate that the required files exist and to auto-create any missing
    expected directories, aborting server startup if a path is in an unrecoverable
    status.

    Attributes:
        consortium_root: The project root directory, resolved as the ancestor three
            levels above this service's module file.
        release_json_file: The release metadata JSON file under `data`. Its existence
            is validated by `_run_preflight_path_validations`.
        server_config_json_file: The server configuration JSON file under `data/server`.
            Not preflight-validated by this service: it is read directly by
            `start_server.py` before this service is usable, so kept here only so
            plugins and components have a single place to resolve it.
        logging_config_json_file: The logging configuration JSON file under
            `data/server`. Not preflight-validated by this service, for the same reason
            as `server_config_json_file` above.
        user_accounts_json_file: The user accounts JSON file under `data/server`. Its
            existence is validated by `_run_preflight_path_validations`.
        role_permissions_json_file: The role permissions JSON file under `data/server`.
            Its existence is validated by `_run_preflight_path_validations`.
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
        ConsortiumUserAccountsFileSystemError: If, when
            `_run_preflight_path_validations` is called, the user accounts file does
            not exist at `user_accounts_json_file`, is a directory, or cannot otherwise
            be confirmed present.
        ConsortiumRolePermissionsFileSystemError: If, when
            `_run_preflight_path_validations` is called, the role permissions file does
            not exist at `role_permissions_json_file`, is a directory, or cannot
            otherwise be confirmed present.
        ConsortiumReleaseFileSystemError: If, when `_run_preflight_path_validations` is
            called, the release file does not exist at `release_json_file`, is a
            directory, or cannot otherwise be confirmed present.
        ConsortiumDirectoryFileSystemError: If, when `_run_preflight_path_validations`
            is called, one of the expected directories cannot be created, or a file
            exists at the path of one of the expected directories instead of a
            directory.
    """

    def __init__(self):
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

        # This service is located at
        # consortium/server/services/paths_service.py, so the consortium
        # root is three levels up relative to it. `resolve()` can raise `OSError` (for
        # example on some platforms if the current working directory no longer exists),
        # so it is wrapped like every other filesystem touch in this service. There is
        # no dedicated error type for this one path since it is not one of the three
        # preflight-validated files, so it is reported through the directory error type,
        # the closest available "cannot establish a filesystem location" type.
        with wrap_filesystem_errors(
            error_type=ConsortiumDirectoryFileSystemError,
            operation="resolve the consortium root directory",
            path=str(pathlib.Path(__file__)),
        ):
            self.consortium_root: pathlib.Path = (
                pathlib.Path(__file__).resolve().parents[3]
            )

        # Data file paths
        self.release_json_file: pathlib.Path = (
            self.consortium_root / "data" / "release.json"
        )
        # Not preflight-validated here: read directly by start_server.py before this
        # service is usable. Kept as an attribute regardless so plugins and components
        # have a single place to resolve it.
        self.server_config_json_file: pathlib.Path = (
            self.consortium_root / "data" / "server" / "server_config.json"
        )
        # Not preflight-validated here, for the same reason as server_config_json_file
        # above: read directly by start_server.py before this service is usable.
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

        # Construction is deliberately side-effect free beyond resolving paths.
        # `_run_preflight_path_validations` is called by the server at boot instead (see
        # `Server._server_startup_procedure`), not here, because
        # `server_singletons.py` constructs `PathsService()` at import time: running
        # filesystem validation from `__init__` would make importing this module able to
        # abort the process.
        self._logger.debug("Started {}", self)

    def __str__(self):
        return "Paths Service"

    def __repr__(self):
        return "PathsService()"

    def _run_preflight_path_validations(self) -> None:
        # Consolidates every startup path validation into a single call site so the
        # server has one thing to invoke, in the right order, before any service reads
        # from these paths. Must be called before any of `release_service`,
        # `authorization_service` or `user_accounts_service` read their respective
        # files, so that a missing or invalid file aborts startup here, with a clear
        # typed error naming the file, rather than failing later inside whichever
        # service happens to touch it first.
        self._validate_required_files_exist()
        self._auto_create_missing_directories()

    def _validate_required_files_exist(self) -> None:
        self._validate_file_exists(
            path=self.user_accounts_json_file,
            error_type=ConsortiumUserAccountsFileSystemError,
        )
        self._validate_file_exists(
            path=self.role_permissions_json_file,
            error_type=ConsortiumRolePermissionsFileSystemError,
        )
        self._validate_file_exists(
            path=self.release_json_file,
            error_type=ConsortiumReleaseFileSystemError,
        )

    @staticmethod
    def _validate_file_exists(
        path: pathlib.Path,
        error_type: type[
            ConsortiumUserAccountsFileSystemError
            | ConsortiumRolePermissionsFileSystemError
            | ConsortiumReleaseFileSystemError
        ],
    ) -> None:
        with wrap_filesystem_errors(
            error_type=error_type,
            operation="confirm the file exists",
            path=path,
        ):
            file_exists = path.exists()
            file_is_a_file = path.is_file() if file_exists else False

        if not file_exists:
            raise error_type(
                operation="confirm the file exists",
                path=str(path),
                underlying_error="No file exists at this path.",
            )
        if not file_is_a_file:
            raise error_type(
                operation="confirm the file exists",
                path=str(path),
                underlying_error=(
                    "The path points to an existing directory where a file was "
                    "expected."
                ),
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
            with wrap_filesystem_errors(
                error_type=ConsortiumDirectoryFileSystemError,
                operation="confirm or create the expected directory",
                path=directory,
            ):
                directory_exists = directory.exists()
                directory_is_a_directory = (
                    directory.is_dir() if directory_exists else False
                )

                if not directory_exists:
                    directory.mkdir(parents=True, exist_ok=True)
                    self._logger.debug(
                        "Automatically created missing directory {}", directory
                    )
                    continue

            if not directory_is_a_directory:
                raise ConsortiumDirectoryFileSystemError(
                    operation="confirm or create the expected directory",
                    path=str(directory),
                    underlying_error=(
                        "The path points to an existing file where a directory was "
                        "expected."
                    ),
                )
