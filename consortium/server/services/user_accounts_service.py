import functools
import json
import pathlib
import uuid
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    EmptyUserAccountPasswordError,
    EmptyUserAccountUsernameError,
    InvalidUserAccountRoleError,
    UserAccountAuthenticationError,
    UserAccountIDNotFoundError,
    UserAccountsFileContainsDuplicateUsernamesError,
    UserAccountsFileEncodingError,
    UserAccountsFileIsNotJSONError,
    UserAccountsFileSchemaError,
    UserAccountsFileSystemError,
    UserAccountsServiceError,
    UserAccountUsernameAlreadyExistsError,
    UserAccountUsernameNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.user_account_models import (
    PersistentUserAccountsFileModel,
    UserAccountModel,
)
from consortium.server.services.authorization_service import AuthorizationService
from consortium.server.utils import (
    format_validation_error,
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    wrap_filesystem_errors,
)

# This module reports every filesystem fault through `UserAccountsFileSystemError`, so the
# error type is bound once here rather than repeated at each call site. Decoding and
# encoding failures are caught separately at the two call sites: they describe the file's
# text rather than the filesystem operation carrying it.
_wrap_filesystem_errors = functools.partial(
    wrap_filesystem_errors,
    UserAccountsFileSystemError,
)


class UserAccountsService:
    def __init__(
        self,
        user_accounts_json_file: pathlib.Path,
        authorization_service: AuthorizationService,
    ) -> None:
        self._user_accounts_json_file = user_accounts_json_file
        self._authorization_service = authorization_service
        self._user_accounts = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "User Accounts Service"

    def __repr__(self) -> str:
        return "UserAccountsService()"

    @log_and_propagate_error_on_service_method
    def get_user_account_by_user_account_id(
        self,
        user_account_id: str | uuid.UUID,
    ) -> UserAccountModel:
        """Returns a user account by its ID.

        Args:
            user_account_id: The ID of the user account to retrieve.

        Returns:
            The requested user account.

        Raises:
            UserAccountIDNotFoundError: If no user account with the given ID exists.
        """
        user_account_id = normalize_uuid(user_account_id)

        try:
            user_account = self._user_accounts[user_account_id]
        except KeyError:
            raise UserAccountIDNotFoundError(
                user_account_id=user_account_id,
            ) from None

        self._logger.debug("Retrieved user account: {!r}", user_account)
        return user_account

    @log_and_propagate_error_on_service_method
    def get_user_account_by_username(self, username: str) -> UserAccountModel:
        """Returns a user account by its username.

        Args:
            username: The username of the account to retrieve.

        Returns:
            The requested user account.

        Raises:
            UserAccountUsernameNotFoundError: If no user account with the given username
                exists.
        """
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self._logger.debug("Retrieved user account: {!r}", user_account)
                return user_account
        raise UserAccountUsernameNotFoundError(username=username)

    @log_and_propagate_error_on_service_method
    def get_all_user_accounts(self) -> list[UserAccountModel]:
        """Returns all registered user accounts.

        Returns:
            A list of all user accounts. Empty if none exist.
        """
        all_user_accounts = list(self._user_accounts.values())
        self._logger.debug(
            "Retrieved all user accounts ({} user account(s) retrieved)",
            len(all_user_accounts),
        )
        return all_user_accounts

    @log_and_propagate_error_on_service_method
    def create_user_account(
        self,
        username: str,
        password: str,
        role: str,
    ) -> UserAccountModel:
        """Creates a new user account and adds it to the in-memory registry.

        Args:
            username: The username for the new account. Must be non-empty and
                unique.
            password: The password for the new account. Must be non-empty.
            role: The role to assign to the new account.

        Returns:
            The newly created user account.

        Raises:
            EmptyUserAccountUsernameError: If `username` is empty.
            EmptyUserAccountPasswordError: If `password` is empty.
            InvalidUserAccountRoleError: If `role` is not a valid user role value.
            UserAccountUsernameAlreadyExistsError: If an account with the given username
                already exists.
        """
        if not username:
            raise EmptyUserAccountUsernameError._during_user_account_creation()
        if not password:
            raise EmptyUserAccountPasswordError._during_user_account_creation()
        if role not in self._authorization_service.get_all_roles():
            raise InvalidUserAccountRoleError._during_user_account_creation(role=role)
        for user_account in self.get_all_user_accounts():
            if user_account.username == username:
                raise UserAccountUsernameAlreadyExistsError._during_user_account_creation(
                    username=username,
                )

        user_account = UserAccountModel(
            username=username,
            password=password,
            role=role,
        )
        self._user_accounts[str(user_account.user_account_id)] = user_account
        self._logger.info("Created new user account: {}", user_account)

        return user_account

    @log_and_propagate_error_on_service_method
    def update_user_account_by_user_account_id(
        self,
        user_account_id: str | uuid.UUID,
        username: str | None = None,
        password: str | None = None,
        role: str | None = None,
    ) -> UserAccountModel:
        """Updates a user account's username, password, and/or role.

        Only fields that are not `None` are updated.

        Args:
            user_account_id: The ID of the user account to update.
            username: The new username. When `None`, the username is not changed.
            password: The new password. When `None`, the password is not changed.
            role: The new role. When `None`, the role is not changed.

        Returns:
            The updated user account.

        Raises:
            UserAccountIDNotFoundError: If no user account with the given ID exists.
            EmptyUserAccountUsernameError: If `username` is an empty string.
            EmptyUserAccountPasswordError: If `password` is an empty string.
            InvalidUserAccountRoleError: If `role` is not a valid user role value.
            UserAccountUsernameAlreadyExistsError: If an account with the given username
                already exists.
        """
        # Calling the `get_user_account_by_user_account_id()` method will implicitly
        # check to see if the user account ID is valid.
        user_account = self.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )

        # TODO: Check for no ops and also add event firing
        if username is not None:
            if not username:
                raise EmptyUserAccountUsernameError._during_user_account_modification(
                    user_account_str=str(user_account),
                )
            for existing_user_account in self.get_all_user_accounts():
                if existing_user_account.username == username:
                    raise UserAccountUsernameAlreadyExistsError._during_user_account_modification(
                        username=username,
                        user_account_str=str(user_account),
                    )
            old_username = user_account.username
            user_account.username = username
            self._logger.info(
                "Updated username for user account {} from '{}' to '{}'",
                user_account,
                old_username,
                username,
            )
        if password is not None:
            if not password:
                raise EmptyUserAccountPasswordError._during_user_account_modification(
                    user_account_str=str(user_account),
                )
            old_password = user_account.password
            user_account.password = password
            self._logger.info(
                "Updated password for user account {} from '{}' to '{}'",
                user_account,
                old_password,
                password,
            )
        if role is not None:
            if role not in self._authorization_service.get_all_roles():
                raise InvalidUserAccountRoleError._during_user_account_modification(
                    role=role,
                    user_account_str=str(user_account),
                )
            old_role = user_account.role
            user_account.role = role
            self._logger.info(
                "Updated role for {} from '{}' to '{}'",
                user_account,
                old_role,
                role,
            )

        return user_account

    @log_and_propagate_error_on_service_method
    def delete_user_account_by_user_account_id(
        self,
        user_account_id: str | uuid.UUID,
    ) -> None:
        """Deletes a user account from the in-memory registry.

        Args:
            user_account_id: The ID of the user account to delete.

        Raises:
            UserAccountIDNotFoundError: If no user account with the given ID exists.
        """
        user_account = self.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
        deleted_user_account = self._user_accounts.pop(
            str(user_account.user_account_id)
        )
        self._logger.info("Deleted user account: {}", deleted_user_account)
        self._logger.debug("- {!r}", deleted_user_account)

    @log_and_propagate_error_on_service_method
    def authenticate_user_account_credentials(
        self,
        username: str,
        password: str,
    ) -> UserAccountModel:
        """Validates a username and password against registered user accounts.

        Args:
            username: The username to authenticate.
            password: The password to validate.

        Returns:
            The authenticated user account.

        Raises:
            UserAccountAuthenticationError: If the username does not exist or the
                password does not match.
        """
        existing_usernames = [
            user_account.username for user_account in self.get_all_user_accounts()
        ]
        try:
            user_account = self.get_user_account_by_username(username=username)
        except UserAccountUsernameNotFoundError:
            raise UserAccountAuthenticationError() from None
        if username not in existing_usernames or user_account.password != password:
            raise UserAccountAuthenticationError()

        self._logger.debug("Authenticated user account: {!r}", user_account)

        return user_account

    @log_and_propagate_error_on_service_method
    def load_user_accounts_from_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> list[UserAccountModel]:
        """Reads user accounts from a JSON file and adds them to the in-memory registry.

        Delegates parsing to `read_user_accounts_from_user_accounts_file` and then
        registers each parsed account.

        Args:
            user_accounts_filepath: Path to the JSON file to read accounts from.

        Returns:
            The list of user accounts loaded from the file.

        Raises:
            UserAccountsFileSystemError: If the file cannot be read, for example because
                it does not exist, the process lacks read permission, or the path points
                to a directory.
            UserAccountsFileEncodingError: If the file's bytes are not valid UTF-8.
            UserAccountsFileIsNotJSONError: If the file is not valid JSON.
            UserAccountsFileSchemaError: If the JSON does not follow the expected schema,
                including when an entry is missing a required field, carries an empty
                username or password, or carries an unrecognised field.
            InvalidUserAccountRoleError: If an entry's role is not one of the roles
                currently registered with the authorization service.
            UserAccountUsernameAlreadyExistsError: If a username from the file conflicts
                with an already-registered account.
            UserAccountsFileContainsDuplicateUsernamesError: If the file itself contains
                duplicate usernames.
        """
        new_user_accounts = self.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_filepath,
        )
        for user_account in new_user_accounts:
            self._user_accounts[str(user_account.user_account_id)] = user_account
            self._logger.debug("Loaded user account: {!r}", user_account)
        return new_user_accounts

    @log_and_propagate_error_on_service_method
    def read_user_accounts_from_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> list[UserAccountModel]:
        """Reads and validates user accounts from a JSON file without registering them.

        Validates the file path, JSON structure, and schema. Checks that usernames are
        unique against both existing registered accounts and entries within the file
        itself.

        Args:
            user_accounts_filepath: Path to the JSON file to read accounts from.

        Returns:
            The list of parsed user accounts.

        Raises:
            UserAccountsFileSystemError: If the file cannot be read, for example because
                it does not exist, the process lacks read permission, or the path points
                to a directory.
            UserAccountsFileEncodingError: If the file's bytes are not valid UTF-8.
            UserAccountsFileIsNotJSONError: If the file is not valid JSON.
            UserAccountsFileSchemaError: If the JSON does not follow the expected schema,
                including when an entry is missing a required field, carries an empty
                username or password, or carries an unrecognised field.
            InvalidUserAccountRoleError: If an entry's role is not one of the roles
                currently registered with the authorization service.
            UserAccountUsernameAlreadyExistsError: If a username from the file conflicts
                with an already-registered account.
            UserAccountsFileContainsDuplicateUsernamesError: If the file itself contains
                duplicate usernames.
        """
        # A missing file is deliberately left to `open()` below: `FileNotFoundError` is
        # self-explanatory once wrapped, and checking first would only add a syscall and a
        # window in which the file can disappear between the check and the open. A
        # directory does need the check, because the `OSError` it produces does not name
        # the real problem on every platform.
        if user_accounts_filepath.is_dir():
            raise UserAccountsFileSystemError._path_is_a_directory(
                operation="read the user accounts file",
                path=str(user_accounts_filepath),
            )

        self._logger.debug("Reading user accounts from: {}", user_accounts_filepath)
        # The encoding is pinned rather than left to the platform default so that a file
        # written on one machine reads back identically on another. Usernames are the
        # persistent identifier for an account, so a locale-dependent decode would not
        # merely garble a display string, it would change who an entry refers to.
        with _wrap_filesystem_errors(
            operation="read the user accounts file",
            path=user_accounts_filepath,
        ):
            try:
                with user_accounts_filepath.open("r", encoding="utf-8") as file:
                    data = file.read()
            except UnicodeDecodeError as exc:
                raise UserAccountsFileEncodingError(
                    user_accounts_filepath=str(user_accounts_filepath),
                    underlying_error=f"{type(exc).__name__}: {exc}",
                ) from None

        try:
            json_data = json.loads(data)
        except json.JSONDecodeError:
            raise UserAccountsFileIsNotJSONError(
                user_accounts_filepath=str(user_accounts_filepath),
            ) from None

        # One validation pass covers the top level array, every entry in it and the
        # non-empty constraints on each field. This replaced a JSON schema that declared
        # `properties` without `required`, so an entry missing a field passed validation
        # and then escaped as a raw `pydantic.ValidationError` from the model
        # construction below.
        try:
            persistent_user_accounts = PersistentUserAccountsFileModel.model_validate(
                json_data,
            ).root
        except ValidationError as exc:
            raise UserAccountsFileSchemaError(
                user_accounts_filepath=str(user_accounts_filepath),
                validation_error_message=format_validation_error(exc),
            ) from None

        # Roles are validated separately from the file's own shape because the valid set
        # is whatever the authorization service loaded from the role permissions file at
        # runtime, which a static model cannot express. Checking them here also keeps the
        # file loading path agreeing with `create_user_account`, which has always
        # validated against the same source.
        valid_roles = self._authorization_service.get_all_roles()

        existing_usernames = [
            user_account.username for user_account in self.get_all_user_accounts()
        ]
        new_usernames = []
        new_user_accounts = []
        for persistent_user_account in persistent_user_accounts:
            if persistent_user_account.role not in valid_roles:
                raise InvalidUserAccountRoleError._during_user_accounts_file_loading(
                    user_accounts_filepath=str(user_accounts_filepath),
                    username=persistent_user_account.username,
                    role=persistent_user_account.role,
                )
            # The model guarantees the usernames and passwords are not empty strings, so
            # we do not need to check for that condition here.
            new_user_account = UserAccountModel(
                username=persistent_user_account.username,
                password=persistent_user_account.password,
                role=persistent_user_account.role,
            )
            if new_user_account.username in existing_usernames:
                raise UserAccountUsernameAlreadyExistsError._during_user_accounts_file_loading(
                    username=new_user_account.username,
                    user_accounts_filepath=str(user_accounts_filepath),
                )
            # Known defect, tracked as H4 in HIGH_DIFF.md and left unchanged here:
            # `new_usernames` is never appended to, so this check cannot fire and a file
            # containing the same username twice loads as two separate accounts that
            # share it. Deliberately not fixed alongside the validation rework, because
            # making it fire can stop a server that boots today from booting.
            if new_user_account.username in new_usernames:
                raise UserAccountsFileContainsDuplicateUsernamesError(
                    user_accounts_filepath=user_accounts_filepath,
                    duplicate_username=new_user_account.username,
                )
            self._logger.debug("Read user account: {}", new_user_account)
            new_user_accounts.append(new_user_account)

        self._logger.debug(
            "Read user accounts from user accounts file ({} user account(s) read)",
            len(new_user_accounts),
        )
        return new_user_accounts

    @log_and_propagate_error_on_service_method
    def write_user_accounts_to_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> int:
        """Serializes and writes all registered user accounts to a JSON file.

        Args:
            user_accounts_filepath: Path to the file to write accounts to.

        Returns:
            The number of bytes written.

        Raises:
            UserAccountsFileSystemError: If the file cannot be written, for example
                because the process lacks write permission, the path points to a
                directory, or the disk is full.
        """
        if user_accounts_filepath.is_dir():
            raise UserAccountsFileSystemError._path_is_a_directory(
                operation="write the user accounts file",
                path=str(user_accounts_filepath),
            )

        self._logger.debug("Writing user accounts to: {}", user_accounts_filepath)

        serializable_user_accounts = []
        for user_account in self.get_all_user_accounts():
            self._logger.debug("Writing user account: {}", user_account)
            serializable_user_accounts.append(
                {
                    "username": user_account.username,
                    "password": user_account.password,
                    "role": user_account.role,
                },
            )

        # Data is guaranteed to be JSON serializable at this point.
        data = json.dumps(serializable_user_accounts, indent=4)

        # Encoded here and written as bytes rather than handed to a text mode file, so
        # that the returned count is the number of bytes that actually reached the disk.
        # A text mode write returns characters, and on a platform that translates newlines
        # it writes more bytes than it reports: this file is 96 characters but 102 bytes
        # on Windows, because each of the six `\n` separators becomes `\r\n`. Writing
        # bytes also makes the file byte identical whatever host produced it, which is the
        # same reason the read path pins its encoding.
        #
        # The encode itself cannot fail: `json.dumps` defaults to `ensure_ascii=True`, so
        # `data` is always pure ASCII. That is also why there is no `UnicodeEncodeError`
        # counterpart to the decode handling on the read path. Passing
        # `ensure_ascii=False` would change both facts.
        encoded_data = data.encode("utf-8")

        with _wrap_filesystem_errors(
            operation="write the user accounts file",
            path=user_accounts_filepath,
        ):
            with user_accounts_filepath.open("wb") as file:
                number_of_bytes_written = file.write(encoded_data)

        self._logger.debug(
            "Wrote user accounts to user accounts file ({} byte(s) written)",
            number_of_bytes_written,
        )
        return number_of_bytes_written

    @log_and_propagate_error_on_service_method
    def load_framework_user_accounts(self) -> bool:
        """Loads user accounts from the framework's configured user accounts file.

        Every failure this can encounter is a `UserAccountsServiceError`, so all of them
        are logged and reported through the return value rather than raised. Callers that
        need the server to react to a failed load have to check that return value: it is
        the only signal, and a `False` leaves the service with no accounts registered.

        Returns:
            `True` if accounts were loaded successfully, `False` if a
            `UserAccountsServiceError` occurred.
        """
        self._logger.debug("Loading framework user accounts...")

        try:
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=self._user_accounts_json_file,
            )
        except UserAccountsServiceError as exc:
            self._logger.error(exc)
            return False

        for user_account in loaded_user_accounts:
            self._logger.debug("Loaded user account: {}", user_account)
        self._logger.debug(
            "Loaded framework user accounts ({} user account(s) loaded)",
            len(loaded_user_accounts),
        )
        return True

    @log_and_propagate_error_on_service_method
    def reload_framework_user_accounts(self) -> bool:
        """Deletes all existing user accounts then reloads them from the framework's file.

        Every failure this can encounter is a `UserAccountsServiceError`, so all of them
        are logged and reported through the return value rather than raised. The existing
        accounts are deleted before the reload is attempted, so a `False` leaves the
        service with no accounts registered rather than with the previous set.

        Returns:
            `True` if accounts were reloaded successfully, `False` if a
            `UserAccountsServiceError` occurred.
        """
        self._logger.debug("Reloading framework user accounts...")

        try:
            for user_account_id in list(self._user_accounts.keys()):
                self.delete_user_account_by_user_account_id(
                    user_account_id=user_account_id,
                )
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=self._user_accounts_json_file,
            )
        except UserAccountsServiceError as exc:
            self._logger.error("{}: {}", exc.__class__.__name__, exc)
            return False

        for user_account in loaded_user_accounts:
            self._logger.debug("Reloaded user account: {}", user_account)
        self._logger.debug(
            "Reloaded framework user accounts ({} user account(s) reloaded)",
            len(loaded_user_accounts),
        )
        return True

    @log_and_propagate_error_on_service_method
    def write_framework_user_accounts(self) -> int:
        """Writes all in-memory user accounts to the framework's configured user accounts file.

        Failures propagate rather than being reported through the return value. A failed
        write means the in-memory registry and the file have diverged and the change will
        be lost on the next restart, which a caller that just accepted a change has to be
        able to react to. `log_and_propagate_error_on_service_method` logs the error on
        the way out, so nothing is lost by not catching it here.

        Returns:
            The number of bytes written.

        Raises:
            UserAccountsFileSystemError: If the file cannot be written, for example
                because the process lacks write permission, the configured path points to
                a directory, or the disk is full.
        """
        self._logger.debug("Writing framework user accounts...")

        number_of_bytes_written = self.write_user_accounts_to_user_accounts_file(
            user_accounts_filepath=self._user_accounts_json_file,
        )

        for user_account in self.get_all_user_accounts():
            self._logger.debug(
                "Wrote user account: {!r}",
                user_account,
            )
        self._logger.debug(
            "Wrote framework user accounts ({} byte(s) written)",
            number_of_bytes_written,
        )
        return number_of_bytes_written
