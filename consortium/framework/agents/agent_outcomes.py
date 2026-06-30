from pydantic import JsonValue

from consortium.framework.agents.agent_message_models import TaskOutputMessageModel


class Success:
    """Represents a successful outcome from an agent capability execution.

    Carries a message and structured data extracted from a TaskOutputMessageModel
    or supplied directly. Individual fields can be overridden when constructing
    from a task output message.

    Attributes:
        message (str): Human-readable description of the successful result.
        data (dict[str, JsonValue]): Structured result data from the execution.
    """

    def __init__(
        self,
        task_output_message: TaskOutputMessageModel | None = None,
        message: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ):
        """Initialize a Success outcome from a task output message or explicit values.

        When task_output_message is provided, message and data are sourced from it
        unless overridden by the corresponding keyword arguments.

        Args:
            task_output_message: The raw output message received from the agent.
                When provided, message and data default to the values from this model.
            message: Human-readable description of the result. Overrides the message
                from task_output_message when both are provided.
            data: Structured result data. Overrides the data from task_output_message
                when both are provided.
        """
        if isinstance(task_output_message, TaskOutputMessageModel):
            self.message = task_output_message.message if message is None else message
            self.data = task_output_message.data if data is None else data
        else:
            self.message = message if message is not None else ""
            self.data = data if data is not None else {}


class Failure:
    """Represents a failed outcome from an agent capability execution.

    Carries a message and structured diagnostic data extracted from a
    TaskOutputMessageModel or supplied directly. Individual fields can be
    overridden when constructing from a task output message.

    Attributes:
        message (str): Human-readable description of the failure.
        data (dict[str, JsonValue]): Structured diagnostic data from the failed execution.
    """

    def __init__(
        self,
        task_output_message: TaskOutputMessageModel | None = None,
        message: str | None = None,
        data: dict[str, JsonValue] | None = None,
    ):
        """Initialize a Failure outcome from a task output message or explicit values.

        When task_output_message is provided, message and data are sourced from it
        unless overridden by the corresponding keyword arguments.

        Args:
            task_output_message: The raw output message received from the agent.
                When provided, message and data default to the values from this model.
            message: Human-readable description of the failure. Overrides the message
                from task_output_message when both are provided.
            data: Structured diagnostic data. Overrides the data from task_output_message
                when both are provided.
        """
        if isinstance(task_output_message, TaskOutputMessageModel):
            self.message = task_output_message.message if message is None else message
            self.data = task_output_message.data if data is None else data
        else:
            self.message = message if message is not None else ""
            self.data = data if data is not None else {}
