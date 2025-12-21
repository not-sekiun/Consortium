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
    description="Disconnect the agent.",
    options={
        SingleValueOption(
            name="duration",
            description=(
                "The amount of time the agent should wait for in seconds before "
                "attempting to reconnect."
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
    name="kill", description="Terminate the agent process.", authors=authors
)

delay_capability = request_response_capability(
    name="delay",
    description="Adjust the delay between agent check-ins.",
    options={
        SingleValueOption(
            name="duration",
            description=(
                "The duration in seconds that the agent should delay itself by between "
                "check-ins."
            ),
            required=True,
            value_type=float,
            default_value=1.0,
            greater_than_or_equal_to=0,
        ),
        SingleValueOption(
            name="jitter",
            description=(
                "The jitter as a percentage of the duration that the agent should "
                "randomly delay itself by between check-ins."
            ),
            required=False,
            value_type=float,
            default_value=0.0,
            greater_than_or_equal_to=0,
        ),
    },
    authors=authors,
)

sleep_capability = request_response_capability(
    name="sleep",
    description="Put the agent to sleep for a specified duration.",
    options={
        SingleValueOption(
            name="duration",
            description="The amount of time in seconds for the agent to sleep.",
            required=True,
            value_type=float,
            default_value=1.0,
            greater_than_or_equal_to=0,
        ),
    },
    authors=authors,
)


def ping_task_handler(task_message, context):
    context.task_id = task_message.task_id
    context.start = datetime.now()
    task_message = remove_task_message_arguments(task_message, ["timeout"])
    return task_message


def ping_result_handler(result_message, context):
    end = datetime.now()
    delta = end - context.start
    result_message.message = (
        f"Agent returned ping response. Latency: {delta.total_seconds():.3f} seconds"
    )
    return result_message


def ping_timeout_handler(context):
    result_message = AgentResultMessageModel(
        task_id=context.task_id,
        success=False,
        message="Ping request timed out.",
        data={},
    )
    return result_message


ping_capability = request_response_capability(
    name="ping",
    description="Ping the agent to check its responsiveness.",
    authors=authors,
    options={
        SingleValueOption(
            name="timeout",
            description=(
                "The duration of time in seconds to wait before considering the ping "
                "to have timed out."
            ),
            required=False,
            default_value=5.0,
            value_type=float,
            greater_than=0,
        )
    },
    resolve_timeout=lambda task_message, context: task_message.arguments["timeout"],
    task_handler=ping_task_handler,
    result_handler=ping_result_handler,
    timeout_handler=ping_timeout_handler,
)

shell_capability = request_response_capability(
    name="shell",
    description="Execute a command using the system shell on the agent.",
    options={
        SingleValueOption(
            name="command",
            description="The command to execute on the agent.",
            required=True,
            value_type=str,
        ),
        SingleValueOption(
            name="timeout",
            description=(
                "The amount of time to wait for the command to complete before timing "
                "out."
            ),
            required=False,
            value_type=int,
            default_value=10,
        ),
        SingleValueOption(
            name="blind",
            description=(
                "Execute the command blind without checking the output. This allows "
                "the launching of long running executables without blocking the agent."
                "The timeout option will not apply when this option is set."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
        SingleValueOption(
            name="shell",
            description=(
                "The filepath to the binary executable of the shell to use to execute "
                "the provided command."
            ),
            required=False,
            value_type=str,
        ),
        SingleValueOption(
            name="expand",
            description=(
                "Attempt to expand environment variables when provided while changing "
                "directories. By default, this is disabled."
            ),
            required=False,
            value_type=bool,
            default_value=False,
        ),
    },
    authors=authors,
)


class AgentType(BaseAgentType):
    name = "consortium_http/consortium_python"
    agent_capabilities = {
        disconnect_capability,
        kill_capability,
        delay_capability,
        sleep_capability,
        ping_capability,
        shell_capability,
    }
