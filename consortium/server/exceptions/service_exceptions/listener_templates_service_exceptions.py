"""
Exception hierarchy for the listener templates service.

- [BaseServiceException][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceException]
  - [ListenerTemplatesServiceError][consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions.ListenerTemplatesServiceError]
    - [ListenerTemplateNotFoundError][consortium.server.exceptions.service_exceptions.listener_templates_service_exceptions.ListenerTemplateNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class ListenerTemplatesServiceError(BaseServiceException):
    """
    Base exception for all listener templates service errors.
    """

    code = "LISTENER_TEMPLATES_SERVICE_ERROR"


class ListenerTemplateNotFoundError(ListenerTemplatesServiceError):
    """
    Raised when the requested listener template is not found.
    """

    code = "LISTENER_TEMPLATE_NOT_FOUND_ERROR"


class ListenerTemplateIDNotFoundError(ListenerTemplateNotFoundError):
    """
    Raised when the requested listener template with the provided listener template ID
    was not found.

    Args:
        listener_template_id (str): The listener template ID that was not found.
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
    """
    Raised when the requested listener template with the provided label was not found.

    Args:
        label (str): The label of the listener template that was not found.
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
