from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class PayloadsServiceError(BaseServiceException):
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
