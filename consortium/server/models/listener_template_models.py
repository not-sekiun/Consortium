from pydantic import UUID4, BaseModel

from consortium.server.models.c2_type_models import ListenerTypeModel
from consortium.server.models.option_models import OptionModel


class ListenerTemplateModel(BaseModel):
    listener_template_id: UUID4
    label: str
    name: str
    description: str
    version: str
    compatible_framework_version: str
    authors: list[str]
    listener_type: ListenerTypeModel
    options: dict[str, OptionModel]
    validating_function: None | str


class ListenerTemplateReferenceModel(BaseModel):
    listener_template_id: UUID4
    label: str
    name: str
