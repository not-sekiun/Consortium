from pydantic import BaseModel

from consortium.framework._components._component_status import State
from consortium.server.models.common_models import ErrorModel


class StatusModel(BaseModel):
    state: State
    error: ErrorModel | None
