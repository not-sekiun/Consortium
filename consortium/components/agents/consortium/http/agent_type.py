from datetime import datetime

from consortium.framework.agent_message_models import AgentResultMessageModel
from consortium.framework.agents import (
    BaseAgentType,
    remove_task_message_arguments,
    request_response_capability,
)
from consortium.framework.options import SingleValueOption

authors = {"Sekiun (github.com/not-sekiun)"}

disconnect_capability = request_response_capability(
    name="disconnect",
    description="Disconnect the agent from the server",
    options={
        SingleValueOption(
            name="duration",
            description=(
                "Time in seconds to wait before attempting to reconnect. "
                "Set to 0 for immediate reconnection."
            ),
            value_type=float,
            required=False,
            default_value=0.0,
            greater_than_or_equal_to=0,
        ),
    },
    authors=authors,
)

kill_capability = request_response_capability(
    name="kill", description="Terminate the agent process immediately.", authors=authors
)

delay_capability = request_response_capability(
    name="delay",
    description="Configure the delay between agent check-ins",
    options={
        SingleValueOption(
            name="duration",
            description="Time in seconds between check-ins.",
            required=True,
            value_type=float,
            default_value=1.0,
            greater_than_or_equal_to=0,
        ),
        SingleValueOption(
            name="jitter",
            description=(
                "Random delay variance as a percentage of duration. "
                "Example: 0.5 adds +-50% randomness to timing."
            ),
            required=False,
            value_type=float,
            default_value=0.5,
            greater_than_or_equal_to=0,
        ),
    },
    authors=authors,
)

sleep_capability = request_response_capability(
    name="sleep",
    description="Put the agent to sleep for a specified duration",
    options={
        SingleValueOption(
            name="duration",
            description="Time in seconds for the agent to sleep.",
            required=True,
            value_type=float,
            default_value=1.0,
            greater_than_or_equal_to=0,
        ),
    },
    authors=authors,
)


def ping_task_handler(agent, task_message, context):
    context.task_id = task_message.task_id
    context.run = datetime.now()
    task_message = remove_task_message_arguments(task_message, ["timeout"])
    return task_message


def ping_result_handler(agent, result_message, context):
    delta = datetime.now() - context.run
    result_message.message = (
        f"Agent returned ping response. Latency: {delta.total_seconds():.3f} seconds"
    )
    return result_message


def ping_timeout_handler(agent, context):
    delta = datetime.now() - context.run
    result_message = AgentResultMessageModel(
        task_id=context.task_id,
        success=False,
        message=(
            f"Ping request timed out before agent could return ping response. "
            f"Latency: {delta.total_seconds():.3f} seconds"
        ),
        data={},
    )
    return result_message


ping_capability = request_response_capability(
    name="ping",
    description="Ping the agent to check responsiveness and measure latency",
    authors=authors,
    options={
        SingleValueOption(
            name="timeout",
            description="Time in seconds to wait for a response before timing out.",
            required=False,
            default_value=5.0,
            value_type=float,
            greater_than=0,
        )
    },
    resolve_timeout=lambda agent, task_message, context: task_message.arguments[
        "timeout"
    ],
    task_handler=ping_task_handler,
    result_handler=ping_result_handler,
    timeout_handler=ping_timeout_handler,
)

shell_capability = request_response_capability(
    name="shell",
    description="Execute a shell command on the agent",
    options={
        SingleValueOption(
            name="command",
            description="Shell command to execute.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="timeout",
            description=(
                "Time in seconds to wait for command completion before timing out."
            ),
            required=False,
            value_type=int,
            default_value=10,
        ),
        SingleValueOption(
            name="blind",
            description=(
                "Execute a command without waiting for output. Allows launching "
                "long-running processes without blocking the agent. Timeout option "
                "will be ignored."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="shell",
            description=(
                "Path to the shell executable binary. Uses system default if not "
                "specified."
            ),
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Expand environment variables in paths. Applies when changing "
                "directories."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
    },
    authors=authors,
)


class AgentType(BaseAgentType):
    name = "eula_multi"
    agent_capabilities = {
        disconnect_capability,
        kill_capability,
        delay_capability,
        sleep_capability,
        ping_capability,
        shell_capability,
    }
