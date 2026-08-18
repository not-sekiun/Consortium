import asyncio
import uuid

import pytest
from loguru import logger

from consortium.framework.agents._channel_buffer import ChannelBuffer
from consortium.framework.agents._memory_bounded_buffer import END_OF_STREAM
from consortium.framework.agents.agent_message_models import TaskLaunchMessageModel
from consortium.framework.agents.agent_outcomes import Success
from consortium.framework.agents.base_agent_capability import BaseAgentCapability
from consortium.framework.agents.channels import Channel, ChannelDirection
from consortium.server.objects.agent_objects import Agent
from consortium.server.objects.task_objects import Task
from consortium.server.services.task_runtime_service import TaskRuntimeService
from consortium.server.services.tasks_service import TasksService

pytestmark = pytest.mark.anyio

# Channels are a purely in-memory construct at this point: a capability declares them,
# gets a buffer per declaration and the runtime holds the same buffers so teardown can
# reach them. Nothing outside the capability writes to or reads from one yet.


class _RecordingEventsService:
    async def trigger_event(self, *_args, **_kwargs):
        return None


def _make_agent() -> Agent:
    # A bare instance wired with only what capability construction and the record store
    # need. A fully constructed Agent requires a configured listener, payload and agent
    # type.
    task_runtime_service = TaskRuntimeService()
    tasks_service = TasksService(
        events_service=_RecordingEventsService(),
        task_runtime_service=task_runtime_service,
    )
    agent = Agent.__new__(Agent)
    agent.agent_id = uuid.uuid4()
    agent.name = "mock-agent"
    agent.logger = logger
    agent._tasks_service = tasks_service
    agent._task_runtime_service = task_runtime_service
    agent._outbox_activity = asyncio.Condition()
    agent._new_task_started_event = asyncio.Event()
    return agent


class _StreamingCapability(BaseAgentCapability):
    name = "streaming_cmd"
    channels = {Channel(name="stdout", direction=ChannelDirection.OUTPUT)}

    async def on_execute(self) -> Success:
        return Success(message="done")


class _PlainCapability(BaseAgentCapability):
    name = "plain_cmd"

    async def on_execute(self) -> Success:
        return Success(message="done")


def _make_capability(
    capability_class: type[BaseAgentCapability],
) -> BaseAgentCapability:
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command=capability_class.name, arguments={})
    return capability_class(agent=agent, task=task)


async def test_a_buffer_exists_for_every_declared_channel():
    capability = _make_capability(_StreamingCapability)

    assert list(capability.channels) == ["stdout"]
    assert isinstance(capability.channels["stdout"], ChannelBuffer)


async def test_a_channel_is_writable_before_the_capability_has_run():
    # Attach-before-produce: the buffers are built during construction, so a client can
    # be attached to a channel that has not seen a byte yet.
    capability = _make_capability(_StreamingCapability)

    await capability.channels["stdout"].put(b"early")

    assert await capability.channels["stdout"].get() == b"early"


async def test_each_running_capability_gets_its_own_buffers():
    first = _make_capability(_StreamingCapability)
    second = _make_capability(_StreamingCapability)

    assert first.channels["stdout"] is not second.channels["stdout"]


async def test_a_capability_declaring_no_channels_holds_none():
    capability = _make_capability(_PlainCapability)

    assert capability.channels == {}


async def test_execute_shuts_down_the_channels_it_declared():
    # How a pump parked on a channel learns the capability has finished: the same
    # teardown that closes the inbox and outbox closes every channel.
    capability = _make_capability(_StreamingCapability)
    stdout = capability.channels["stdout"]

    await capability.execute(
        task_launch_message=TaskLaunchMessageModel(
            task_id=capability.task.task_id,
            command=capability.name,
            arguments={},
        )
    )

    assert await stdout.get() is END_OF_STREAM


async def test_teardown_leaves_buffered_bytes_readable():
    # Graceful shutdown, matching the outbox: what the capability wrote before returning
    # is still there to be drained rather than dropped at teardown.
    capability = _make_capability(_StreamingCapability)
    stdout = capability.channels["stdout"]
    await stdout.put(b"last words")

    await capability._shutdown_task_queues()

    assert await stdout.get() == b"last words"
    assert await stdout.get() is END_OF_STREAM


async def test_starting_a_capability_hands_its_channels_to_the_runtime():
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command="streaming_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)

    await agent._start_agent_capability(
        agent_capability=_StreamingCapability,
        task=task,
    )

    runtime = agent._task_runtime_service.get_task_runtime(task_id=task.task_id)
    assert list(runtime.channels) == ["stdout"]
    runtime.detach()


async def test_detaching_a_runtime_returns_the_channel_buffers_to_shut_down():
    agent = _make_agent()
    task = Task(agent_id=agent.agent_id, command="streaming_cmd", arguments={})
    agent._tasks_service._register_task(task=task, agent=agent)
    await agent._start_agent_capability(
        agent_capability=_StreamingCapability,
        task=task,
    )
    runtime = agent._task_runtime_service.get_task_runtime(task_id=task.task_id)
    stdout = runtime.channels["stdout"]

    buffers = runtime.detach()

    assert stdout in buffers
    assert runtime.channels == {}
