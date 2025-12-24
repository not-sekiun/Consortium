import uuid
from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field


class AgentTaskMessageModel(BaseModel):
    """
    Model representing a task message sent to an agent.

    Attributes:
        task_id (uuid.UUID): Unique identifier for the task.
        command (str): The command to be executed by the agent.
        arguments (dict[str, Any]): Arguments required for the command.
        data (dict[str, Any]): Additional data related to the task.
    """

    task_id: uuid.UUID
    command: str
    arguments: dict[str, Any]
    data: dict[str, Any] = Field(default_factory=dict)

    def make_copy(self):
        """
        Create a deep copy of the current `AgentTaskMessageModel`.
        """
        new_task_message_model = deepcopy(self)
        return new_task_message_model

    def to_json(self):
        """
        Serialize the AgentTaskMessageModel to a JSON-compatible dictionary.
        """
        return {
            "task_id": str(self.task_id),
            "command": self.command,
            "arguments": self.arguments,
            "data": self.data,
        }


class AgentResultMessageModel(BaseModel):
    """
    Model representing a result message sent from an agent.

    Attributes:
        task_id (uuid.UUID): Unique identifier for the associated task.
        success (bool): Indicates if the task was successful.
        message (str): A message providing additional information about the result.
        data (dict[str, Any]): Additional data related to the result.
    """

    task_id: uuid.UUID
    success: bool
    message: str
    data: dict[str, Any]

    def make_copy(self):
        """
        Make a deep copy of the current `AgentResultMessageModel`.
        """
        new_result_message_model = deepcopy(self)
        return new_result_message_model

    def to_json(self):
        """
        Serialize the AgentResultMessageModel to a JSON-compatible dictionary.
        """
        return {
            "task_id": str(self.task_id),
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }
