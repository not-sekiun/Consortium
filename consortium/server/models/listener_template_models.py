from typing import Any

from pydantic import BaseModel

from consortium.server.models.c2_types_models import ListenerTypeModel


class ListenerTemplateModel(BaseModel):
    listener_template_id: str
    name: str
    description: str
    listener_type: ListenerTypeModel
    authors: list[str]
    options: dict[str, Any]
    validating_function: None | str
