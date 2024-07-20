"""
Errors for the api endpoint /api/users:

- HTTPError
 - NotFoundError
   - UserNotFoundError: User with provided ID not found.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError


class UserNotFoundError(NotFoundError):
    code = "USER_NOT_FOUND_ERROR"
