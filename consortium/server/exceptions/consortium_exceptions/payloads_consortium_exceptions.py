"""Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`PayloadsError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadsError]
        - [`PayloadsFrameworkError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadsFrameworkError]
            - [`PayloadCreationError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadCreationError]
                - [`PayloadCreationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadCreationParameterTypeError]
        - [`PayloadsServiceError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadsServiceError]
            - [`PayloadNotFoundError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadNotFoundError]
            - [`PayloadIDReservationNotFoundError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadIDReservationNotFoundError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class PayloadsError(BaseConsortiumError):
    code = "PAYLOADS_ERROR"


class PayloadsFrameworkError(PayloadsError):
    code = "PAYLOAD_FRAMEWORK_ERROR"


class PayloadCreationError(PayloadsFrameworkError):
    code = "PAYLOAD_CREATION_ERROR"


class PayloadCreationParameterTypeError(PayloadCreationError):
    code = "PAYLOAD_CREATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
    ):
        super().__init__(
            message=(
                f"Failed to create the payload. The parameter "
                f"'{parameter_name}' must be of type '{parameter_type}' in the "
                f"payload's provided parameters."
            ),
        )


class PayloadsServiceError(PayloadsError):
    code = "PAYLOADS_SERVICE_ERROR"


class PayloadNotFoundError(PayloadsServiceError):
    code = "PAYLOAD_NOT_FOUND_ERROR"

    def __init__(self, payload_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested payload. No payload was found "
                f"with the provided payload ID '{payload_id}'."
            ),
        )


class PayloadIDReservationNotFoundError(PayloadsServiceError):
    code = "PAYLOAD_ID_RESERVATION_NOT_FOUND_ERROR"

    def __init__(self, payload_id: str):
        super().__init__(
            message=(
                f"Failed to create the payload file and assign it the provided payload "
                f"ID reservation. No reservation was found for the provided payload "
                f"ID '{payload_id}'. Check that you reserved a payload ID first using "
                f"`PayloadsService.reserve_payload_id` before creating a payload with "
                f"that ID."
            ),
        )
