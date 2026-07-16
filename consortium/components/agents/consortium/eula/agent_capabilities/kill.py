from consortium.framework.agents import RequestResponseCapability


class KillCapability(RequestResponseCapability):
    name = "kill"
    description = "Terminate the agent process immediately"
    authors = {"Sekiun (github.com/not-sekiun)"}

    async def on_response(self, result_message):
        self.agent.mark_as_inactive()
        return result_message
