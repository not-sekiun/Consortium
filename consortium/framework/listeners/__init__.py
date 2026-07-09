"""The listeners framework provides the building blocks for defining listeners that
manage connected agents.

A listener is implemented by subclassing
[`BaseListener`][consortium.framework.listeners.BaseListener], which handles the
lifecycle of agents that connect through it (registration, check-ins, task
distribution, and result collection). Each listener declares a
[`BaseListenerType`][consortium.framework.listeners.BaseListenerType] that determines
which agent types are compatible with it, and listeners are configured and created
through a [`BaseListenerTemplate`][consortium.framework.listeners.BaseListenerTemplate].
Listeners exchange task messages with agents using
[`TaskLaunchMessageModel`][consortium.framework.listeners.TaskLaunchMessageModel],
[`TaskInputMessageModel`][consortium.framework.listeners.TaskInputMessageModel], and
[`TaskOutputMessageModel`][consortium.framework.listeners.TaskOutputMessageModel].
"""

from consortium.framework.agents.agent_message_models import (
    TaskInputMessageModel,
    TaskLaunchMessageModel,
    TaskOutputMessageModel,
)
from consortium.framework.listeners.base_listener import BaseListener
from consortium.framework.listeners.base_listener_template import BaseListenerTemplate
from consortium.framework.listeners.base_listener_type import BaseListenerType

__all__ = [
    "BaseListener",
    "BaseListenerTemplate",
    "BaseListenerType",
    "TaskLaunchMessageModel",
    "TaskOutputMessageModel",
    "TaskInputMessageModel",
]
