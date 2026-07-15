from typing import final

from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.signal_exceptions import AgentCapabilityExecutionError


class IncomingStreamCapability(BaseAgentCapability, abstract=True):
    async def on_handle_incoming_message(
        self, index: int, task_output_message: TaskOutputMessageModel
    ) -> Success | Failure | None:
        pass

    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        return task_launch_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        index = 0
        while True:
            task_output_message = await self.recv_from_agent()
            result = await self.on_handle_incoming_message(
                index=index, task_output_message=task_output_message
            )
            # A `Success`/`Failure` stops the stream and becomes the task result; the
            # `Finish` sentinel stops with no outcome; `None` continues the loop to await
            # the next response.
            if result is Finish:
                return None
            if isinstance(result, (Success, Failure)):
                return result
            if result is not None:
                raise AgentCapabilityExecutionError(
                    "`on_handle_incoming_message` must return a `Success`, `Failure`, "
                    "`Finish`, or `None` but instead returned value of type "
                    f"{type(result).__name__}"
                )
            index += 1
