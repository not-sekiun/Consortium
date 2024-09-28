class ClientRESTAPIAuthenticationError(Exception):
    pass


class ClientRESTAPIConnectionAlreadyLoggedInError(ClientRESTAPIAuthenticationError):
    def __init__(self):
        super().__init__(
            "Failed to login to the server over its REST API. Client is already "
            "logged in to the server over its REST API (Log out from server before "
            "attempting to log in again).",
        )


class ClientRESTAPIConnectionNotLoggedInError(ClientRESTAPIAuthenticationError):
    def __init__(self):
        super().__init__(
            "Failed to perform the requested operation over the server's REST API. "
            "Client is not logged in to server over its REST API.",
        )


class ClientRESTAPIConnectionFailedToLoginError(ClientRESTAPIAuthenticationError):
    def __init__(self):
        super().__init__(
            "Failed to login to the server over its REST API. Either invalid "
            "credentials were provided or the server is not a valid Consortium "
            "server instance.",
        )


class InvalidServerRESTAPILoginResponseError(ClientRESTAPIAuthenticationError):
    def __init__(self):
        super().__init__(
            "Failed to login to the server over its REST API. Server did not "
            "return a valid OAuth2 JSON web token. The server is likely not a "
            "valid Consortium server instance.",
        )


# TODO: Add more granular exception handling in the future for each particular error
#  response that may returned for each API endpoint.
class ClientRESTAPIOperationError(Exception):
    pass
