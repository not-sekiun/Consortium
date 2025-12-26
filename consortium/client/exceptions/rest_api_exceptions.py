from typing import Any


class RestApiAuthenticationError(Exception): ...


class RestApiAlreadyLoggedInError(RestApiAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port}. Client is already logged in as '{username}'.",
        )


class RestApiNotLoggedInError(RestApiAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int):
        super().__init__(
            "Failed to perform the requested operation over the server's REST API "
            f"at {remote_host}:{remote_port}. Client is not logged in to the server.",
        )


class InvalidRestApiCredentialsError(RestApiAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port} as '{username}'. Check that valid "
            "credentials were provided.",
        )


class InvalidServerRestApiLoginResponseError(RestApiAuthenticationError):
    def __init__(self, remote_host: str, remote_port: int, username: str):
        super().__init__(
            f"Failed to login to the server over its REST API at "
            f"{remote_host}:{remote_port} as '{username}'. Server did not return a "
            f"valid login response. Check that the server is a valid Consortium "
            f"server instance.",
        )


# TODO: Add more granular exception handling in the future for each particular error
#  response that may return for each API endpoint. <- hell no lol
class RestApiOperationError(Exception):
    def __init__(self, code: str, message: str, detail: Any):
        if detail:
            super().__init__(
                f"{code}: {message} (Detail: {detail})",
            )  # TODO: Consider formatting this more nicely
        else:
            super().__init__(
                f"{code}: {message}",
            )
