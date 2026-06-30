from enum import StrEnum

from consortium.framework.agents._agent_communicator import _AgentCommunicator


class AgentLifecycleEvent(StrEnum):
    """Agent lifecycle events that can trigger automatic hook execution.

    Used as the value for BaseAgentHook.execution_triggers to specify which
    phase of an agent's lifecycle activates the hook.
    """

    ON_REGISTERED = "ON_REGISTERED"
    ON_CHECKED_IN = "ON_CHECKED_IN"


class BaseAgentHook(_AgentCommunicator):
    """Base class for hooks that run automatically at specific agent lifecycle events.

    Subclasses declare which lifecycle event triggers them via the execution_triggers
    class attribute and implement on_execute to define their behavior. Hooks share the
    same agent-and-task communication interface provided by _AgentCommunicator.

    Attributes:
        execution_triggers (AgentLifecycleEvent): The lifecycle event that causes this
            hook to be invoked automatically by the framework.
    """

    execution_triggers: AgentLifecycleEvent

    async def on_execute(self) -> None:
        """Execute the hook logic when the declared lifecycle event fires.

        Override to implement behavior that should run when execution_triggers
        fires on the associated agent.
        """
        ...
