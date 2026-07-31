"""Errors for the api endpoint /api/listener-templates.
- HTTPError
  - NotFoundError
    - ListenerTemplateNotFoundError: The requested listener template with the provided
    listener template ID was not found.
  - UnprocessableEntityError
    - ListenerTemplateOptionNotFoundError: The provided listener template option
    could not be found.
    - ListenerTemplateOptionValueError: The provided listener template option
    value failed option value validation.
    - ListenerTemplateValidatingFunctionError: The provided set of listener template
    options was rejected by the listener template's validating function.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)


# At the services level, Listener templates distinguish between not being found by their
# `listener_template_id` (`LISTENER_TEMPLATE_ID_NOT_FOUND_ERROR`) or `label`
# (`LISTENER_TEMPLATE_ID_NOT_FOUND_ERROR`). But this distinction does not exist at the
# API level hence we override using those error codes with this error code
class ListenerTemplateNotFoundError(NotFoundError):
    code = "LISTENER_TEMPLATE_NOT_FOUND_ERROR"


class ListenerTemplateOptionNotFoundError(UnprocessableEntityError): ...


class ListenerTemplateOptionValueValidationError(UnprocessableEntityError): ...


class MissingRequiredListenerTemplateOptionError(UnprocessableEntityError): ...


class ListenerTemplateValidatingFunctionError(UnprocessableEntityError): ...
