from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError


class ArtifactNotFoundError(NotFoundError):
    code = "ARTIFACT_NOT_FOUND_ERROR"
