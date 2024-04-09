# Exceptions for the client connection.
class AlreadyLoggedInError(Exception):
    pass


class NotLoggedInError(Exception):
    pass


class FailedToLoginError(Exception):
    pass


class InvalidServerLoginResponseError(Exception):
    pass


# TODO: Add more granular exception handling in the future for each particular error
#  response that may returned for each API endpoint.
class APIError(Exception):
    pass
