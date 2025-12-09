"""
Errors for the api endpoint /api/listener-templates.
- HTTPError
  - NotFoundError
    - ListenerTemplateNotFoundError: The requested listener template with the provided
    listener template ID was not found.
  - UnprocessableEntityError
    - ListenerTemplateOptionNotFoundError: The provided listener template option
    could not be found.
    - ListenerTemplateOptionValueError: The provided listener template option
    value failed option value validation.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


class ListenerTemplateNotFoundError(NotFoundError): ...


class ListenerTemplateOptionNotFoundError(UnprocessableEntityError): ...


class ListenerTemplateOptionValueError(UnprocessableEntityError): ...
