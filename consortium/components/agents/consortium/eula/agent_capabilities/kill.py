from consortium.framework.agents import BaseAgentCapability


class KillCapability(BaseAgentCapability):
    name = "kill"
    description = "Terminate the agent process immediately"
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def on_execute(self):
        kill_response = (await self.recv_from_agent()).to_outcome()
        self.agent.mark_as_inactive()
        return kill_response
