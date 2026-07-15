import asyncio
from datetime import datetime

from consortium.framework.agents.agent_message_models import TaskLaunchMessageModel
from consortium.framework.agents.agent_outcomes import Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.server.models.agent_task_models import AgentTaskState


class MockCapability(BaseAgentCapability):
    name = "mock_cmd"
    description = "No-op capability that returns success immediately for API tests."
    authors = {"test"}

    async def execute(self, task_launch_message: TaskLaunchMessageModel) -> Success:
        # Transition QUEUED -> RUNNING directly, mirroring what get_next_task_message
        # does, so the framework can then transition RUNNING -> SUCCEEDED on return.
        if self.task.status.state == AgentTaskState.QUEUED:
            self.task.status.state = AgentTaskState.RUNNING
            self.task.datetime_started = datetime.now()
        return Success(message="mock success", data={"result": "ok"})


class MockBlockingCapability(BaseAgentCapability):
    # Holds the task in QUEUED state so DELETE-queued-task tests can run reliably.
    # QUEUED -> RUNNING only happens via get_next_task_message(), which no listener
    # calls in this test context, so the task stays QUEUED while execute() is sleeping.
    name = "mock_blocking_cmd"
    description = "No-op capability that blocks so the task stays QUEUED for API tests."
    authors = {"test"}

    async def execute(self, task_launch_message: TaskLaunchMessageModel) -> Success:
        # Block so the task stays QUEUED long enough for the deletion tests to act on
        # it. On cancellation at teardown, report Success explicitly rather than
        # returning None: a None return now means "completed normally" as well, but
        # being explicit keeps this mock independent of that convention.
        try:
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            return Success(message="mock cancelled")
        return Success(message="mock success")
