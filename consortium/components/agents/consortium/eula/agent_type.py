from consortium.framework.agents import BaseAgentType

from .agent_capabilities.cat import CatCapability
from .agent_capabilities.cd import CdCapability
from .agent_capabilities.cp import CpCapability
from .agent_capabilities.delay import DelayCapability
from .agent_capabilities.disconnect import DisconnectCapability
from .agent_capabilities.download import DownloadCapability
from .agent_capabilities.kill import KillCapability
from .agent_capabilities.ls import LsCapability
from .agent_capabilities.ping import PingCapability
from .agent_capabilities.pwd import PwdCapability
from .agent_capabilities.shell import ShellCapability
from .agent_capabilities.sleep import SleepCapability
from .agent_capabilities.upload import UploadCapability


class AgentType(BaseAgentType):
    name = "eula"
    agent_capabilities = {
        DisconnectCapability,
        KillCapability,
        DelayCapability,
        SleepCapability,
        PingCapability,
        ShellCapability,
        DownloadCapability,
        UploadCapability,
        CdCapability,
        CatCapability,
        PwdCapability,
        LsCapability,
        CpCapability,
    }
