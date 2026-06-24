from pydantic import JsonValue

from consortium.framework.agents.agent_message_models import TaskOutputMessageModel


class Success:
    def __init__(
        self,
        task_output_message: TaskOutputMessageModel | None = None,
        message: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ):
        if isinstance(task_output_message, TaskOutputMessageModel):
            self.message = task_output_message.message if message is None else message
            self.data = task_output_message.data if data is None else data
        else:
            self.message = message if message is not None else ""
            self.data = data if data is not None else {}


class Failure:
    def __init__(
        self,
        task_output_message: TaskOutputMessageModel | None = None,
        message: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ):
        if isinstance(task_output_message, TaskOutputMessageModel):
            self.message = task_output_message.message if message is None else message
            self.data = task_output_message.data if data is None else data
        else:
            self.message = message if message is not None else ""
            self.data = data if data is not None else {}
