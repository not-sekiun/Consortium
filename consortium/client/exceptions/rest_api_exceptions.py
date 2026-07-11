from pydantic import JsonValue

from consortium.client.exceptions.client_session_exceptions import (
    BaseClientSessionError,
)


class RestAPIError(BaseClientSessionError): ...


class RestAPIAuthenticationError(RestAPIError): ...


class RestAPIAlreadyLoggedInError(RestAPIAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port}. Client is already logged in as '{username}'.",
        )


class RestAPINotLoggedInError(RestAPIAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int):
        super().__init__(
            "Failed to perform the requested operation over the server's REST API "
            f"at {remote_host}:{remote_port}. Client is not logged in to the server.",
        )


class InvalidRestAPICredentialsError(RestAPIAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port} as '{username}'. Check that valid "
            "credentials were provided.",
        )


class InvalidServerRestAPILoginResponseError(RestAPIAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port} as '{username}'. Server did not return a "
            f"valid login response. Check that the server is a valid Consortium "
            f"server instance.",
        )


class RestAPIConnectionError(RestAPIAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port} as '{username}'. Could not establish a "
            f"connection with the server.",
        )


class RestAPIOperationError(RestAPIError):
    def __init__(
        self, status_code: int, code: str, message: str, detail: dict[str, JsonValue]
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail

        super().__init__(f"[{self.status_code}] {code}: {message}")
