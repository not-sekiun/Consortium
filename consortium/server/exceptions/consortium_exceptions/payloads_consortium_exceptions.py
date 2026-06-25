"""
Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`PayloadsError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadsError]
        - [`PayloadsFrameworkError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadsFrameworkError]
            - [`PayloadCreationError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadCreationError]
                - [`PayloadCreationParameterTypeError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadCreationParameterTypeError]
        - [`PayloadsServiceError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadsServiceError]
            - [`InvalidPayloadsMetadataFileError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.InvalidPayloadsMetadataFileError]
                - [`InvalidPayloadsMetadataFileJSONError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.InvalidPayloadsMetadataFileJSONError]
                - [`InvalidPayloadsMetadataFileSchemaError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.InvalidPayloadsMetadataFileSchemaError]
            - [`PayloadNotFoundError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadNotFoundError]
            - [`PayloadDeletionError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadDeletionError]
                - [`PayloadRepositoryResourceMissingError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadRepositoryResourceMissingError]
            - [`PayloadMetadataMissingError`][consortium.server.exceptions.consortium_exceptions.payloads_consortium_exceptions.PayloadMetadataMissingError]
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


class InvalidPayloadsMetadataFileError(PayloadsServiceError):
    code = "INVALID_PAYLOADS_METADATA_FILE_ERROR"


class InvalidPayloadsMetadataFileJSONError(InvalidPayloadsMetadataFileError):
    code = "INVALID_PAYLOADS_METADATA_FILE_JSON_ERROR"

    def __init__(self, repository_directory: str):
        super().__init__(
            message=(
                "Failed to load the payloads metadata file "
                "`.payloads.json` from the repository directory "
                f"'{repository_directory}'. The payloads metadata file is not"
                f"a valid JSON file. "
            ),
        )


class InvalidPayloadsMetadataFileSchemaError(
    InvalidPayloadsMetadataFileError,
):
    code = "INVALID_REPOSITORY_METADATA_FILE_SCHEMA_ERROR"

    def __init__(self, repository_directory: str, json_schema_error_message: str):
        super().__init__(
            message=(
                "Failed to load the payloads metadata file "
                "`.payloads.json` from the repository directory "
                f"'{repository_directory}'. The payloads metadata file does not "
                f"conform to the expected JSON schema. {json_schema_error_message}"
            ),
        )


class PayloadNotFoundError(PayloadsServiceError):
    code = "PAYLOAD_NOT_FOUND_ERROR"

    def __init__(self, payload_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested payload. No payload was found "
                f"with the provided payload ID '{payload_id}'."
            ),
        )


class PayloadDeletionError(PayloadsServiceError):
    code = "PAYLOAD_DELETION_ERROR"


class PayloadRepositoryResourceMissingError(PayloadDeletionError):
    code = "PAYLOAD_REPOSITORY_RESOURCE_MISSING_ERROR"

    def __init__(self, payload_id: str):
        super().__init__(
            message=(
                f"Failed to delete the payload with the provided payload ID "
                f"'{payload_id}'. The repository resource for the payload is "
                f"missing."
            ),
        )


class PayloadMetadataMissingError(PayloadsServiceError):
    code = "PAYLOAD_METADATA_MISSING_ERROR"

    def __init__(self, payload_id: str):
        super().__init__(
            message=(
                f"Failed to delete the payload with the provided payload ID "
                f"'{payload_id}'. The metadata for the payload is missing."
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
