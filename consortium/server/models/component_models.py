from pydantic import BaseModel

from consortium.framework._core.components.component_status import State
from consortium.server.models.error_models import ErrorModel


class StatusModel(BaseModel):
    state: State
    error: ErrorModel | None
