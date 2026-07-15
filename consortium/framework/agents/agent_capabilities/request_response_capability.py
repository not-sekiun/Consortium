from typing import final

from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.agents.base_agent_capability import (
    BaseAgentCapability,
)


class RequestResponseCapability(BaseAgentCapability, abstract=True):
    """Template base class for capabilities that send one task and await one response.

    This is the class-based counterpart to the request_response_capability factory.
    Subclass it, declare the usual capability metadata as class attributes (name,
    description, options, and so on), and override only the hooks you need. The
    request-then-response machinery, including timeout handling, lives in the final
    on_launch and on_execute methods so subclasses never have to reimplement it.

    Intermediate state that used to be threaded through a SimpleNamespace context is
    now just instance state on self, and the agent is always available as self.agent.

    Attributes:
        timeout (int | float | None): Default number of seconds to wait for the agent's
            response. None waits indefinitely. Override resolve_timeout for a value
            computed per task.

    Example: A capability that trims the agent's response
        ```python
        class Whoami(RequestResponseCapability):
            name = "whoami"
            description = "Return the current user."
            timeout = 30

            async def on_response(self, task_output_message):
                task_output_message.message = task_output_message.message.strip()
                return task_output_message
        ```
    """

    timeout: int | float | None = None

    async def resolve_timeout(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> int | float | None:
        """Return the number of seconds to wait for the agent's response.

        Override to compute the timeout dynamically from the outgoing task message.
        The default returns the class-level timeout attribute.

        Args:
            task_launch_message: The task message about to be sent to the agent.

        Returns:
            The receive timeout in seconds, or None to wait indefinitely.
        """
        return self.timeout

    async def on_request(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        """Inspect or mutate the task message before it is sent to the agent.

        Override to enrich or replace the outgoing message. The default returns it
        unchanged.

        Args:
            task_launch_message: The task message prepared for launch.

        Returns:
            The message to transmit, or None to cancel the launch.
        """
        return task_launch_message

    async def on_response(
        self,
        task_output_message: TaskOutputMessageModel,
    ) -> TaskOutputMessageModel:
        """Post-process the agent's response before it becomes the outcome.

        Override to reshape or annotate the response. The default returns it unchanged.

        Args:
            task_output_message: The output message received from the agent.

        Returns:
            The output message to wrap in the Success or Failure outcome.
        """
        return task_output_message

    async def on_timeout(self) -> TaskOutputMessageModel:
        """Handle the case where the agent does not respond within the timeout.

        Override to return a substitute output message instead of failing. The default
        re-raises the TimeoutError so the task errors out.

        Returns:
            A substitute output message to report as the outcome.
        """
        # A bare raise re-raises the TimeoutError currently being handled in on_execute.
        raise

    @final
    async def on_launch(
        self,
        task_launch_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | None:
        # Resolve the receive timeout from the original message before on_task can
        # replace it, matching the request_response_capability factory's ordering.
        self._recv_timeout = await self.resolve_timeout(task_launch_message)
        return await self.on_request(task_launch_message)

    @final
    async def on_execute(self) -> Success | Failure:
        try:
            response_message = await self.recv_from_agent(timeout=self._recv_timeout)
        except TimeoutError:
            # on_timeout re-raises by default; an override may return a substitute
            # result message to report instead.
            response_message = await self.on_timeout()
            return response_message.to_outcome()

        response_message = await self.on_response(response_message)
        if not isinstance(response_message, TaskOutputMessageModel):
            raise TypeError(
                "The `on_response` hook must return a `TaskOutputMessageModel`."
            )
        return response_message.to_outcome()
