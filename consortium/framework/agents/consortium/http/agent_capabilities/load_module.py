from consortium.framework.base_agent_capability import BaseAgentCapability
from consortium.server.models.agent_models import AgentResultModel, AgentResultState
from consortium.server.objects.agent_objects import Agent


class LoadModuleCapability(BaseAgentCapability):
    def __init__(
        self,
    ):
        name = "Load Module"
        description = "Load a module into the agent."
        command = "load_module"
        super().__init__(
            name=name,
            description=description,
            command=command,
        )

    def process_task(self, agent: Agent, data: dict):
        #     def run_capability(self, agent: Agent, data: dict):
        try:
            module_name = data["module_name"]
        except KeyError:
            agent.add_result(
                AgentResultModel(
                    status=AgentResultState.ERROR,
                    message="Module name not provided.",
                ),
            )
            return
        try:
            module_source_code = data["module_source_code"]
        except KeyError:
            agent.add_result(
                AgentResultModel(
                    status=AgentResultState.ERROR,
                    message="Module source code not provided.",
                ),
            )
            return
        return agent.load_module(module_name, module_source_code)
