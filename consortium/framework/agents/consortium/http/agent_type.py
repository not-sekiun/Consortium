from consortium.framework.agents.consortium.http.agent_capabilities.core import (
    delay_capability,
    disconnect_capability,
    download_capability,
    kill_capability,
    ping_capability,
    shell_capability,
    sleep_capability,
    upload_capability,
)
from consortium.framework.c2_types import BaseAgentType


class AgentType(BaseAgentType):
    name = "agents/consortium/http"
    agent_capabilities = {
        ping_capability.PingCapability,
        shell_capability.ShellCapability,
        delay_capability.DelayCapability,
        disconnect_capability.DisconnectCapability,
        kill_capability.KillCapability,
        sleep_capability.SleepCapability,
        # upload_capability.UploadCapability,
        # download_capability.DownloadCapability,
    }


AGENT_TYPE = AgentType()
