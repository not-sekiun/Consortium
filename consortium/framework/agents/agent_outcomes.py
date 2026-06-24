from consortium.framework.agent_message_models import TaskOutputMessageModel


class Success:
    def __init__(self, task_output_message: TaskOutputMessageModel):
        self.task_output_message = task_output_message


class Failure:
    def __init__(self, task_output_message: TaskOutputMessageModel):
        self.task_output_message = task_output_message
