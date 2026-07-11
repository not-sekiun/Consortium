"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`ListenerTemplatesServiceError`][consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions.ListenerTemplatesServiceError]
        - [`ListenerTemplateNotFoundError`][consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions.ListenerTemplateNotFoundError]
            - [`ListenerTemplateIDNotFoundError`][consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions.ListenerTemplateIDNotFoundError]
            - [`ListenerTemplateLabelNotFoundError`][consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions.ListenerTemplateLabelNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class ListenerTemplatesServiceError(BaseServiceError):
    """Base exception for all errors that occur within the listener templates service."""

    code = "LISTENER_TEMPLATES_SERVICE_ERROR"


class ListenerTemplateNotFoundError(ListenerTemplatesServiceError):
    """Raised when the requested listener template was not found in the listener templates
    service.
    """

    code = "LISTENER_TEMPLATE_NOT_FOUND_ERROR"


class ListenerTemplateIDNotFoundError(ListenerTemplateNotFoundError):
    """Raised when the requested listener template with the provided listener template ID
    was not found in the listener templates service.
    """

    code = "LISTENER_TEMPLATE_ID_NOT_FOUND_ERROR"

    def __init__(self, listener_template_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested listener template. No listener template "
                f"was found with the provided listener template ID "
                f"'{listener_template_id}'."
            ),
            detail={"listener_template_id": listener_template_id},
        )


class ListenerTemplateLabelNotFoundError(ListenerTemplateNotFoundError):
    """Raised when the requested listener template with the provided label was not found
    in the listener templates service.
    """

    code = "LISTENER_TEMPLATE_LABEL_NOT_FOUND_ERROR"

    def __init__(self, label: str):
        super().__init__(
            message=(
                f"Failed to find the requested listener template. No listener template "
                f"was found with the provided label '{label}'."
            ),
            detail={"label": label},
        )
