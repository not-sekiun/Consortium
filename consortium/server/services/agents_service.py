from typing import Any

from loguru import logger

from consortium.server.exceptions.framework_exceptions.agents_framework_exceptions import (
    AgentTaskNotFoundError as AgentTaskNotFoundFrameworkError,
)
from consortium.server.exceptions.service_exceptions.agents_service_exceptions import (
    AgentNotFoundError,
    AgentResultNotFoundError,
    AgentTaskNotFoundError,
)
from consortium.server.models.agent_models import AgentResultModel, AgentTaskModel
from consortium.server.objects.agent_objects import Agent


class AgentsService:
    def __init__(self):
        self._agents = {}
        self.agents_service_logger = logger.bind(
            logger_name=str(self),
        )

    def __str__(self) -> str:
        return "Consortium Agents Service"

    def __repr__(self) -> str:
        return "AgentsService()"

    def create_and_add_agent(self, *args, **kwargs) -> Agent:
        agent = Agent(*args, **kwargs)
        self._agents[str(agent.agent_id)] = agent
        self.agents_service_logger.info(f"Created and added agent: {agent}")
        self.agents_service_logger.debug(f"Created and added agent: {agent!r}")
        return agent

    def remove_agent_by_agent_id(self, agent_id: str) -> None:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        del self._agents[agent_id]
        self.agents_service_logger.info(f"Removed agent: {agent}")
        self.agents_service_logger.debug(f"Removed agent: {agent!r}")

    def get_agent_by_agent_id(self, agent_id: str) -> Agent:
        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(agent_id=agent_id)

        self.agents_service_logger.debug(f"Retrieved agent: {agent!r}")
        return agent

    def get_all_agents(self) -> list[Agent]:
        all_agents = list(self._agents.values())
        self.agents_service_logger.debug(
            f"Retrieved all agents ({len(all_agents)} retrieved)",
        )
        return all_agents

    def get_all_agent_tasks_by_agent_id(self, agent_id: str) -> list[AgentTaskModel]:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        all_tasks = agent.get_all_tasks()
        self.agents_service_logger.debug(
            f"Retrieved all agent tasks from agent {agent} ({len(all_tasks)} "
            f"retrieved)",
        )
        return all_tasks

    def get_all_queued_tasks_by_agent_id(self, agent_id: str) -> list[AgentTaskModel]:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        queued_tasks = agent.get_all_queued_tasks()
        self.agents_service_logger.debug(
            f"Retrieved queued tasks from agent {agent_id} ({len(queued_tasks)} "
            f"retrieved)",
        )
        return queued_tasks

    def get_all_running_tasks_by_agent_id(self, agent_id: str) -> list[AgentTaskModel]:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        running_tasks = agent.get_all_running_tasks()
        self.agents_service_logger.debug(
            f"Retrieved running tasks from agent {agent_id} ({len(running_tasks)} "
            f"retrieved)",
        )
        return running_tasks

    def get_all_completed_tasks_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentTaskModel]:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        completed_tasks = agent.get_all_completed_tasks()
        self.agents_service_logger.debug(
            f"Retrieved completed tasks from agent {agent_id} ({len(completed_tasks)} "
            f"retrieved)",
        )
        return completed_tasks

    def get_agent_task_by_agent_id_and_task_id(
        self,
        agent_id: str,
        task_id: str,
    ) -> AgentTaskModel:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        try:
            task = agent.get_task_by_task_id(task_id=task_id)
        except AgentTaskNotFoundFrameworkError:
            raise AgentTaskNotFoundError(task_id=task_id)

        self.agents_service_logger.debug(
            f"Retrieved task {task_id} from agent {agent}",
        )

        return task

    def get_all_agent_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentResultModel]:
        agent = self.get_agent_by_agent_id(agent_id)
        all_results = agent.get_all_results()
        self.agents_service_logger.debug(
            f"Retrieved all agent results from agent {agent} ({len(all_results)} "
            f"retrieved)",
        )
        return all_results

    def get_all_successful_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentResultModel]:
        agent = self.get_agent_by_agent_id(agent_id)
        successful_results = agent.get_all_successful_results()
        self.agents_service_logger.debug(
            f"Retrieved successful results from agent {agent_id} "
            f"({len(successful_results)} retrieved)",
        )
        return successful_results

    def get_all_failed_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentResultModel]:
        agent = self.get_agent_by_agent_id(agent_id)
        failed_results = agent.get_all_failed_results()
        self.agents_service_logger.debug(
            f"Retrieved failed results from agent {agent_id} ({len(failed_results)} "
            f"retrieved)",
        )
        return failed_results

    def get_all_errored_results_by_agent_id(
        self,
        agent_id: str,
    ) -> list[AgentResultModel]:
        agent = self.get_agent_by_agent_id(agent_id)
        errored_results = agent.get_all_errored_results()
        self.agents_service_logger.debug(
            f"Retrieved errored results from agent {agent_id} ({len(errored_results)} "
            f"retrieved)",
        )
        return errored_results

    def get_agent_result_by_agent_id_and_result_id(
        self,
        agent_id: str,
        result_id: str,
    ) -> AgentResultModel:
        all_results = self.get_all_agent_results_by_agent_id(agent_id)
        for result in all_results:
            if result.result_id == result_id:
                self.agents_service_logger.debug(
                    f"Retrieved result {result_id} from agent {agent_id}",
                )
                return result
        raise AgentResultNotFoundError(result_id=result_id)

    def task_agent_by_agent_id(
        self,
        agent_id: str,
        command: str,
        arguments: dict[str, Any] | list,
    ) -> AgentTaskModel:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        task = AgentTaskModel(command=command, arguments=arguments)
        agent.add_task(task=task)
        return task

    def delete_queued_agent_task_by_task_id(self, agent_id: str, task_id: str):
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        try:
            agent.delete_queued_task_by_task_id(task_id=task_id)
        except AgentTaskNotFoundFrameworkError:
            raise AgentTaskNotFoundError(task_id=task_id)
