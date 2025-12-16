from consortium.framework.agents.agent_message_models import AgentTaskMessageModel


def remove_task_message_arguments(
    task_message: AgentTaskMessageModel,
    argument_names: list[str],
) -> AgentTaskMessageModel:
    """
    Remove specified arguments from an agent task message.

    Useful for pre-processing task messages by removing framework-specific arguments
    before they are sent over the network to agents, reducing payload sizes.

    Args:
        task_message: The original agent task message.
        argument_names: List of argument names to remove.

    Returns:
        AgentTaskMessageModel: A new agent task message with the specified arguments
            removed.
    """
    updated_arguments = {
        key: value
        for key, value in task_message.arguments.items()
        if key not in argument_names
    }
    return AgentTaskMessageModel(
        task_id=task_message.task_id,
        command=task_message.command,
        arguments=updated_arguments,
        data=task_message.data,
    )
