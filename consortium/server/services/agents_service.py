import asyncio
import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from consortium.framework.event_hooks._event import Event
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.consortium_exceptions.agents_consortium_exceptions import (
    AgentNotFoundError,
    AgentResultIDNotFoundError,
    AgentTaskNotFoundError,
)
from consortium.server.models.agent_models import (
    AgentResultModel,
    AgentResultStatus,
    AgentTaskModel,
    AgentTaskStatus,
)
from consortium.server.objects.agent_objects import Agent
from consortium.server.server_logging import LoggerType
from consortium.server.services.events_service import EventsService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class AgentsService:
    def __init__(self, events_service: EventsService):
        self._events_service = events_service
        self._agents = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )

    def __str__(self) -> str:
        return "Agents Service"

    def __repr__(self) -> str:
        return "AgentsService()"

    @log_and_propagate_error_on_service_method
    def register_agent(self, *args, **kwargs) -> Agent:
        agent = Agent(*args, **kwargs)
        self._agents[str(agent.agent_id)] = agent

        asyncio.create_task(
            self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.AGENT_REGISTERED,
                    data={"agent_id": str(agent.agent_id)},
                ),
            )
        )
        self._logger.info("Registered agent: {}", agent)
        self._logger.debug("- {!r}", agent)

        return agent

    @log_and_propagate_error_on_service_method
    def deregister_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        del self._agents[str(agent.agent_id)]

        asyncio.create_task(
            self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.AGENT_DEREGISTERED,
                    data={"agent_id": str(agent.agent_id)},
                ),
            )
        )
        self._logger.info("Deregistered agent: {}", agent)
        self._logger.debug("- {!r}", agent)

    @log_and_propagate_error_on_service_method
    def get_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> Agent:
        agent_id = normalize_uuid(value=agent_id)

        try:
            agent = self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(agent_id=agent_id) from None

        self._logger.debug("Retrieved agent: {!r}", agent)
        return agent

    @log_and_propagate_error_on_service_method
    def get_all_agents(self) -> list[Agent]:
        all_agents = list(self._agents.values())
        self._logger.debug(
            "Retrieved all agents ({} retrieved)",
            len(all_agents),
        )
        return all_agents

    @log_and_propagate_error_on_service_method
    def get_all_agent_tasks(
        self, status: AgentTaskStatus | None = None
    ) -> list[AgentTaskModel]:
        all_tasks = []
        for agent in self._agents.values():
            all_tasks.extend(agent.get_all_tasks(status=status))
        if status is None:
            self._logger.debug(
                "Retrieved all tasks from all agents ({} retrieved)",
                len(all_tasks),
            )
        else:
            self._logger.debug(
                "Retrieved all tasks from all agents with status {} ({} retrieved)",
                status,
                len(all_tasks),
            )
        return all_tasks

    @log_and_propagate_error_on_service_method
    def get_agent_task_by_task_id(self, task_id: str | uuid.UUID) -> AgentTaskModel:
        for agent in self._agents.values():
            try:
                task = agent.get_task_by_task_id(task_id=task_id)
                self._logger.debug(
                    "Retrieved task {} from agent {}",
                    task_id,
                    agent,
                )
                return task
            except AgentTaskNotFoundError:
                continue

        raise AgentTaskNotFoundError(task_id=task_id) from None

    @log_and_propagate_error_on_service_method
    def get_all_agent_tasks_by_agent_id(
        self, agent_id: str | uuid.UUID, status: AgentTaskStatus | None = None
    ) -> list[AgentTaskModel]:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        all_tasks = agent.get_all_tasks(status=status)
        if status is None:
            self._logger.debug(
                "Retrieved agent tasks from agent {} ({} retrieved)",
                agent,
                len(all_tasks),
            )
        else:
            self._logger.debug(
                "Retrieved agent tasks from agent {} with status {} ({} retrieved)",
                agent,
                status,
                len(all_tasks),
            )
        return all_tasks

    @log_and_propagate_error_on_service_method
    def get_agent_task_by_agent_id_and_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ) -> AgentTaskModel:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        task = agent.get_task_by_task_id(task_id=task_id)
        self._logger.debug(
            "Retrieved task {} from agent {}",
            task_id,
            agent,
        )
        return task

    @log_and_propagate_error_on_service_method
    def get_all_agent_results(
        self, status: AgentResultStatus | None = None
    ) -> list[AgentResultModel]:
        all_results = []
        for agent in self._agents.values():
            all_results.extend(agent.get_all_results(status=status))
        if status is None:
            self._logger.debug(
                "Retrieved all results from all agents ({} retrieved)",
                len(all_results),
            )
        else:
            self._logger.debug(
                "Retrieved all results from all agents with status {} ({} retrieved)",
                status,
                len(all_results),
            )
        return all_results

    @log_and_propagate_error_on_service_method
    def get_agent_result_by_result_id(
        self, result_id: str | uuid.UUID
    ) -> AgentResultModel:
        for agent in self._agents.values():
            try:
                result = agent.get_result_by_result_id(result_id=result_id)
                self._logger.debug(
                    "Retrieved result {} from agent {}",
                    result_id,
                    agent,
                )
                return result
            except AgentResultIDNotFoundError:
                continue

        raise AgentResultIDNotFoundError(result_id=result_id) from None

    @log_and_propagate_error_on_service_method
    def get_all_agent_results_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        status: AgentResultStatus | None = None,
    ) -> list[AgentResultModel]:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        all_results = agent.get_all_results(status=status)
        if status is None:
            self._logger.debug(
                "Retrieved agent results from agent {} ({} retrieved)",
                agent,
                len(all_results),
            )
        else:
            self._logger.debug(
                "Retrieved agent results from agent {} with status {} ({} retrieved)",
                agent,
                status,
                len(all_results),
            )
        return all_results

    @log_and_propagate_error_on_service_method
    def get_agent_result_by_agent_id_and_result_id(
        self,
        agent_id: str | uuid.UUID,
        result_id: str | uuid.UUID,
    ) -> AgentResultModel:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        result = agent.get_result_by_result_id(result_id=result_id)
        self._logger.debug(
            "Retrieved result {!r} from agent {!r} through result ID",
            result,
            agent,
        )
        return result

    @log_and_propagate_error_on_service_method
    def get_agent_result_by_agent_id_and_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ) -> AgentResultModel:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        result = agent.get_result_by_task_id(task_id=task_id)
        self._logger.debug(
            "Retrieved result {!r} from agent {!r} through task ID {}",
            result,
            agent,
            str(task_id),
        )
        return result

    @log_and_propagate_error_on_service_method
    async def task_agent_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        command: str,
        arguments: dict[str, Any],
    ) -> AgentTaskModel:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        task = AgentTaskModel(command=command, arguments=arguments)
        await agent.submit_task(task=task)

        await self._events_service.trigger_event(
            event=Event(
                event_type=EventType.AGENT_TASKED,
                data={"agent_id": str(agent.agent_id)},
            ),
        )
        self._logger.info("Tasked agent {} with task {}", agent, task)
        self._logger.debug("Tasked agent {!r} with task {!r}", agent, task)
        return task

    @log_and_propagate_error_on_service_method
    def check_in_agent_by_agent_id(self, agent_id: str | uuid.UUID) -> None:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        asyncio.create_task(
            self._events_service.trigger_event(
                event=Event(
                    event_type=EventType.AGENT_CHECKED_IN,
                    data={"agent_id": str(agent.agent_id)},
                ),
            )
        )
        agent.datetime_last_checked_in = datetime.now()
        self._logger.debug("Checked in agent {!r}", agent)

    @log_and_propagate_error_on_service_method
    def update_agent_by_agent_id(
        self,
        agent_id: str | uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Agent:
        agent = self.get_agent_by_agent_id(agent_id=agent_id)

        updated = {}

        if name is not None:
            old_name = agent.name
            agent.name = name
            self._logger.info(
                "Updated agent {} name from '{}' to '{}'",
                agent,
                old_name,
                agent.name,
            )
            self._logger.debug("- {!r}", agent)
            updated["name"] = {
                "old": old_name,
                "new": agent.name,
            }

        if description is not None:
            old_description = agent.description
            agent.description = description
            self._logger.debug(
                "Updated agent {} description from '{}' to '{}'",
                agent,
                old_description,
                agent.description,
            )
            self._logger.debug("- {!r}", agent)
            updated["description"] = {
                "old": old_description,
                "new": agent.description,
            }

        if updated:
            asyncio.create_task(
                self._events_service.trigger_event(
                    event=Event(
                        event_type=EventType.AGENT_UPDATED,
                        data={"agent_id": str(agent.agent_id)},
                    ),
                )
            )
        else:
            self._logger.debug(
                "No updates applied to agent {} as no changes were detected even "
                "though the update method was called.",
                agent,
            )

        return agent

    @log_and_propagate_error_on_service_method
    def delete_queued_agent_task_by_agent_id_and_task_id(
        self,
        agent_id: str | uuid.UUID,
        task_id: str | uuid.UUID,
    ):
        agent = self.get_agent_by_agent_id(agent_id=agent_id)
        agent.delete_queued_task_by_task_id(task_id=task_id)
