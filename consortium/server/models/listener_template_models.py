from typing import Any

from pydantic import BaseModel

from consortium.server.models.listener_models import ListenerTypeModel


class ListenerTemplateModel(BaseModel):
    name: str
    description: str
    listener_type: ListenerTypeModel
    authors: list[str]
    options: dict[str, Any]
    listener_template_id: str
    validating_function: None | str
