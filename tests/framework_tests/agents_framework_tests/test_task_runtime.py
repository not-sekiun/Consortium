import asyncio
import uuid

import pytest

from consortium.framework._core.framework_exceptions.agent_capabilities_framework_exceptions import (  # noqa: E501
    AgentCapabilityExecutionError,
)
from consortium.framework.agents._task_messages_queue import (
    END_OF_STREAM,
    TaskMessagesQueue,
)
from consortium.server.models.task_models import TaskState
from consortium.server.objects.task_objects import TaskStatus
from consortium.server.objects.task_runtime import TaskRuntime
from consortium.server.services.task_runtime_service import TaskRuntimeService

pytestmark = pytest.mark.anyio


def _an_error() -> AgentCapabilityExecutionError:
    return AgentCapabilityExecutionError(
        agent_capability_name="stub_cmd",
        error_message="mock failure",
    )


def _attached_runtime(
    handler: asyncio.Task | None = None,
) -> tuple[TaskRuntime, TaskMessagesQueue, TaskMessagesQueue]:
    inbox = TaskMessagesQueue()
    outbox = TaskMessagesQueue()
    runtime = TaskRuntime()
    runtime.attach(handler=handler, inbox=inbox, outbox=outbox)
    return runtime, inbox, outbox


# --- TaskRuntime.detach ---


async def test_detach_cancels_the_handler_and_hands_back_the_queues():
    handler = asyncio.create_task(asyncio.Event().wait())
    runtime, inbox, outbox = _attached_runtime(handler=handler)

    queues = runtime.detach()

    assert set(queues) == {inbox, outbox}
    assert handler.cancelling()
    assert runtime.is_exhausted()
    assert runtime.handler is None
    assert runtime.inbox is None
    assert runtime.outbox is None
    await asyncio.gather(handler, return_exceptions=True)


async def test_detach_leaves_the_queues_running_for_the_caller_to_shut_down():
    # Severing the references has to happen synchronously alongside the record removal,
    # but shutting a queue down awaits both the queue's own condition and the agent's
    # outbox condition. detach therefore hands the queues back rather than shutting them
    # down itself, and the caller decides whether to await that or background it.
    runtime, inbox, outbox = _attached_runtime()

    queues = runtime.detach()

    for queue in queues:
        assert not queue.is_at_end_of_stream()
        # Still open: a reader is told "nothing yet" by timing out, rather than being
        # told the stream has ended.
        with pytest.raises(TimeoutError):
            await queue.get(timeout=0)

    for queue in queues:
        await queue.shutdown(immediate=True)
    assert await inbox.get(timeout=0) is END_OF_STREAM
    assert await outbox.get(timeout=0) is END_OF_STREAM


async def test_detaching_twice_hands_the_queues_to_the_first_caller_only():
    # Whoever detaches owns the shutdown. A second caller must come away empty rather
    # than with queues it also believes it is responsible for.
    runtime, _inbox, _outbox = _attached_runtime()

    first = runtime.detach()
    second = runtime.detach()

    assert len(first) == 2
    assert second == []


async def test_detach_tolerates_a_partially_released_runtime():
    runtime, _inbox, outbox = _attached_runtime()
    runtime.release_inbox()

    queues = runtime.detach()

    assert queues == [outbox]


# --- TaskRuntime release and exhaustion ---


async def test_runtime_is_exhausted_only_once_every_reference_is_released():
    handler = asyncio.create_task(asyncio.Event().wait())
    runtime, _inbox, _outbox = _attached_runtime(handler=handler)

    assert not runtime.is_exhausted()
    runtime.release_handler()
    assert not runtime.is_exhausted()
    runtime.release_inbox()
    assert not runtime.is_exhausted()
    runtime.release_outbox()
    assert runtime.is_exhausted()

    handler.cancel()
    await asyncio.gather(handler, return_exceptions=True)


async def test_has_readable_outbox_follows_the_outbox_lifecycle():
    runtime, _inbox, outbox = _attached_runtime()

    assert runtime.has_readable_outbox()
    await outbox.shutdown(immediate=True)
    # Shut down and drained: nothing further can arrive, so it is no longer readable.
    assert not runtime.has_readable_outbox()
    runtime.release_outbox()
    assert not runtime.has_readable_outbox()


# --- TaskRuntimeService ownership ---


async def test_runtimes_are_scoped_and_ordered_per_agent():
    task_runtime_service = TaskRuntimeService()
    first_agent_id = uuid.uuid4()
    second_agent_id = uuid.uuid4()
    first_task_id = uuid.uuid4()
    second_task_id = uuid.uuid4()
    other_task_id = uuid.uuid4()
    for task_id, agent_id in (
        (first_task_id, first_agent_id),
        (second_task_id, first_agent_id),
        (other_task_id, second_agent_id),
    ):
        runtime, _inbox, _outbox = _attached_runtime()
        task_runtime_service.attach_task_runtime(
            task_id=task_id,
            agent_id=agent_id,
            task_runtime=runtime,
        )

    # Insertion order is the sequential muxer's ordering policy: the earliest tasked
    # runtime with a readable outbox is served first.
    assert task_runtime_service.first_readable_task_id_for_agent(
        agent_id=first_agent_id
    ) == str(first_task_id)
    assert [
        task_id
        for task_id, _outbox in task_runtime_service.readable_outboxes_for_agent(
            agent_id=first_agent_id
        )
    ] == [str(first_task_id), str(second_task_id)]

    popped = task_runtime_service.pop_all_for_agent(agent_id=first_agent_id)

    assert len(popped) == 2
    assert task_runtime_service.get_task_runtime(task_id=first_task_id) is None
    assert task_runtime_service.get_task_runtime(task_id=second_task_id) is None
    # The other agent's runtime is untouched.
    assert task_runtime_service.get_task_runtime(task_id=other_task_id) is not None


async def test_releasing_the_last_reference_drops_the_runtime_from_the_registry():
    task_runtime_service = TaskRuntimeService()
    task_id = uuid.uuid4()
    runtime, _inbox, _outbox = _attached_runtime()
    task_runtime_service.attach_task_runtime(
        task_id=task_id,
        agent_id=uuid.uuid4(),
        task_runtime=runtime,
    )

    task_runtime_service.release_inbox(task_id=task_id)
    assert task_runtime_service.get_task_runtime(task_id=task_id) is runtime
    task_runtime_service.release_outbox(task_id=task_id)

    assert task_runtime_service.get_task_runtime(task_id=task_id) is None


async def test_lookups_with_a_non_uuid_are_absent_rather_than_errors():
    task_runtime_service = TaskRuntimeService()

    assert task_runtime_service.get_task_runtime(task_id="not-a-uuid") is None
    assert task_runtime_service.pop(task_id="not-a-uuid") is None
    assert task_runtime_service.pop_all_for_agent(agent_id="not-a-uuid") == []
    assert not task_runtime_service.has_readable_outbox_for_agent(agent_id="not-a-uuid")


# --- TaskStatus compare and swap ---


def test_try_transition_declines_instead_of_raising_from_a_terminal_state():
    # The distinction the teardown paths depend on: losing a race to a concurrently
    # running handler is an ordinary outcome and must not raise, while the raising form
    # stays available for callers that provably own the task.
    status = TaskStatus()
    status._transition_to_succeeded()

    assert status._try_transition_to_errored(error=_an_error()) is False
    assert status.state == TaskState.SUCCEEDED
    with pytest.raises(AssertionError):
        status._transition_to_errored(error=_an_error())


def test_try_transition_performs_a_legal_transition():
    status = TaskStatus()

    assert status._try_transition_to_running() is True
    assert status.state == TaskState.RUNNING
    assert status._try_transition_to_errored(error=_an_error()) is True
    assert status.state == TaskState.ERRORED
    assert status.error is not None


def test_try_transition_to_running_declines_once_the_task_is_terminal():
    # A reader holding a launch message it dequeued before teardown must not be able to
    # drag the task back to RUNNING.
    status = TaskStatus()
    status._transition_to_errored(error=_an_error())

    assert status._try_transition_to_running() is False
    assert status.state == TaskState.ERRORED


def test_try_transition_still_raises_on_a_malformed_call():
    # The compare and swap only absorbs lost races. A caller that asks for an error
    # state without supplying an error has a bug, and that still fails loudly.
    status = TaskStatus()

    with pytest.raises(AssertionError):
        status._try_transition_to_state(new_state=TaskState.ERRORED, error=None)
