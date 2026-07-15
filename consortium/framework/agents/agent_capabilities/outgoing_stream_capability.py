from typing import final

from consortium.framework.agents import TaskInputMessageModel
from consortium.framework.agents.agent_capabilities.control_models import Finish
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.signal_exceptions import AgentCapabilityExecutionError


class OutgoingStreamCapability(BaseAgentCapability, abstract=True):
    async def on_handle_outgoing_message(
        self,
    ) -> TaskInputMessageModel | Success | Failure:
        # Returns a TaskInputMessageModel to send, a Success/Failure to short-circuit
        # with that outcome, or the Finish sentinel to half-close (stop sending, then
        # await and process the single final response). Finish is a plain object()
        # sentinel and so cannot appear in the annotation until PEP 661 lands in 3.15.
        pass

    async def on_handle_final_response(
        self, task_output_message: TaskOutputMessageModel
    ) -> Success | Failure | None:
        return task_output_message.to_outcome()

    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        return task_launch_message

    @final
    async def on_execute(self) -> Success | Failure | None:
        while True:
            outgoing = await self.on_handle_outgoing_message()
            # A `Success`/`Failure` short-circuits: the developer has already decided
            # the result, so report it and skip the final response.
            if isinstance(outgoing, (Success, Failure)):
                return outgoing
            # A bare `Finish` is a half-close: stop sending, then await and process the
            # single final response from the agent.
            if outgoing is Finish:
                final_response = await self.recv_from_agent()
                return await self.on_handle_final_response(
                    task_output_message=final_response
                )
            if not isinstance(outgoing, TaskInputMessageModel):
                raise AgentCapabilityExecutionError(
                    "`on_handle_outgoing_message` must return a `TaskInputMessageModel`, "
                    "`Success`, `Failure`, or `Finish` but instead returned value of "
                    f"type {type(outgoing).__name__}"
                )
            await self.send_to_agent(task_message=outgoing)
