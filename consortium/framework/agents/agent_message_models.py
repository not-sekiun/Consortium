import uuid
from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field


class AgentTaskMessageModel(BaseModel):
    task_id: uuid.UUID
    command: str
    arguments: dict[str, Any]
    data: dict[str, Any] = Field(default_factory=dict)

    def create_new_related_task_message(self):
        new_task_message_model = deepcopy(self)
        new_task_message_model.data = {}
        return new_task_message_model

    def to_json(self):
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "data": self.data,
        }


class AgentResultMessageModel(BaseModel):
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    task_id: uuid.UUID
    success: bool
    message: str
    data: dict[str, Any]

    def create_new_related_result_message(self):
        new_result_message_model = deepcopy(self)
        new_result_message_model.data = {}
        return new_result_message_model

    def to_json(self):
        return {
            "result_id": str(self.result_id),
            "task_id": str(self.task_id),
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }
