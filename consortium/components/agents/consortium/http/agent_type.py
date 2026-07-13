from datetime import datetime

from consortium.framework.agents import (
    BaseAgentType,
    SupportedOS,
    request_response_capability,
)
from consortium.framework.agents.agent_message_models import TaskOutputMessageModel
from consortium.framework.options import SingleValueOption

from .agent_capabilities.cat import CatCapability
from .agent_capabilities.cd import CdCapability
from .agent_capabilities.cp import CpCapability
from .agent_capabilities.download import DownloadCapability
from .agent_capabilities.ls import LsCapability
from .agent_capabilities.pwd import PwdCapability
from .agent_capabilities.upload import UploadCapability

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
    result_handler=lambda agent, result_message, context: (
        agent.mark_as_inactive(),
        result_message,
    )[1],
)

kill_capability = request_response_capability(
    name="kill",
    description="Terminate the agent process immediately",
    authors=authors,
    result_handler=lambda agent, result_message, context: (
        agent.mark_as_inactive(),
        result_message,
    )[1],
)

delay_capability = request_response_capability(
    name="delay",
    description="Configure the delay between agent check-ins",
    options={
        SingleValueOption(
            name="duration",
            description="Time in seconds between check-ins.",
            required=False,
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
            greater_than_or_equal_to=0,
        ),
    },
    authors=authors,
    result_handler=lambda agent, result_message, context: (
        agent.mark_as_inactive(),
        result_message,
    )[1],
)


def ping_task_handler(agent, task_message, context):
    context.task_id = task_message.task_id
    context.run = datetime.now()
    task_message.arguments.pop("timeout")
    return task_message


def ping_result_handler(agent, result_message, context):
    delta = datetime.now() - context.run
    result_message.message = (
        f"Agent returned ping response. Latency: {delta.total_seconds():.3f} seconds"
    )
    return result_message


def ping_timeout_handler(agent, context):
    delta = datetime.now() - context.run
    result_message = TaskOutputMessageModel(
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
    resolve_timeout=lambda task_message, context: task_message.arguments["timeout"],
    task_handler=ping_task_handler,
    result_handler=ping_result_handler,
    timeout_handler=ping_timeout_handler,
)

shell_capability = request_response_capability(
    name="shell",
    description="Execute a shell command on the agent",
    supported_oses=SupportedOS.DESKTOP,
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
    mitre_attack_techniques={"T1059.001", "T1059.003", "T1059.004"},
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
        DownloadCapability,
        UploadCapability,
        CdCapability,
        CatCapability,
        PwdCapability,
        LsCapability,
        CpCapability,
    }
