from consortium.framework.agents import BaseAgentGenerator
from consortium.framework.event_hooks import BaseEventHook
from consortium.framework.listeners import BaseListener
from consortium.framework.plugins import BasePlugin


def register_plugin(plugin_class: BasePlugin):
    """
    Register a plugin class.

    Args:
        plugin_class (BasePlugin): The plugin class to register.
    """
    # Implementation for registering the plugin
    print(f"Registering plugin: {plugin_class}")
    return plugin_class


def register_listener(listener_class: BaseListener):
    """
    Register a listener class.

    Args:
        listener_class (BaseListener): The listener class to register.
    """
    # Implementation for registering the listener
    print(f"Registering listener: {listener_class}")
    return listener_class


def register_event_hook(event_hook_class: BaseEventHook):
    """
    Register an event hook class.

    Args:
        event_hook_class (BaseEventHook): The event hook class to register
    """
    # Implementation for registering the event hook
    print(f"Registering event hook: {event_hook_class}")
    return event_hook_class


def register_agent_generator(agent_generator_class: BaseAgentGenerator):
    """
    Register an agent generator class.

    Args:
        agent_generator_class (BaseAgentGenerator): The agent generator class to register
    """
    # Implementation for registering the agent generator
    print(f"Registering agent generator: {agent_generator_class}")
    return agent_generator_class
