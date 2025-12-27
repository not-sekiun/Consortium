from consortium.server.exceptions.api_exceptions.http_exceptions import (
    UnprocessableEntityError,
)


class InvalidUUIDError(UnprocessableEntityError):
    code = "INVALID_UUID_ERROR"

    def __init__(self, resource_name: str, uuid_value: str):
        super().__init__(
            message=(
                f"Failed to perform the requested operation on the {resource_name}. "
                f"The provided {resource_name} ID value '{uuid_value}' is not a valid "
                f"UUID4 string."
            ),
        )
