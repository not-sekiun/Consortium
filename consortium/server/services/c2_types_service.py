from loguru import logger

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.service_exceptions.c2_types_service_exceptions import (
    AgentTypeNotFoundError,
    ListenerTypeNotFoundError,
)
from consortium.server.server_logging import LoggerType
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.services.listener_profiles_service import ListenerProfilesService


class C2TypesService:
    def __init__(
        self,
        listener_profiles_service: ListenerProfilesService,
        agent_profiles_service: AgentProfilesService,
    ):
        self._listener_profiles_service = listener_profiles_service
        self._agent_profiles_service = agent_profiles_service
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "C2 Types Service"

    def __repr__(self) -> str:
        return (
            f"C2TypesService("
            f"listener_profiles_service={self._listener_profiles_service!r}, "
            f"agent_profiles_service={self._agent_profiles_service!r}"
            f")"
        )

    def get_all_listener_types(self) -> list[BaseListenerType]:
        listener_types = []
        for (
            listener_profile
        ) in self._listener_profiles_service.get_all_listener_profiles():
            if listener_profile.listener_type not in listener_types:
                listener_types.append(listener_profile.listener_type)
        self._logger.debug(
            "Retrieved all listener types ({} listener type(s) retrieved).",
            len(listener_types),
        )
        return listener_types

    def get_listener_type_by_name(self, listener_type_name: str) -> BaseListenerType:
        for listener_type in self.get_all_listener_types():
            if str(listener_type.name) == listener_type_name:
                self._logger.debug(
                    "Retrieved listener type: {!r}",
                    listener_type,
                )
                return listener_type
        raise ListenerTypeNotFoundError(listener_type_name=listener_type_name)

    def get_all_agent_types(self) -> list[BaseAgentType]:
        agent_types = []
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            if agent_profile.agent_type not in agent_types:
                agent_types.append(agent_profile.agent_type)
        self._logger.debug(
            "Retrieved all agent types ({} agent type(s) retrieved).",
            len(agent_types),
        )
        return agent_types

    def get_agent_type_by_name(self, agent_type_name: str) -> BaseAgentType:
        for agent_type in self.get_all_agent_types():
            if str(agent_type.name) == agent_type_name:
                self._logger.debug(
                    "Retrieved agent type: {!r}",
                    agent_type,
                )
                return agent_type
        raise AgentTypeNotFoundError(agent_type_name=agent_type_name)

    def get_compatible_listener_types_from_agent_type_name(
        self, agent_type_name: str
    ) -> list[str]:
        compatible_listener_types = []
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            if str(agent_profile.agent_type.name) == agent_type_name:
                for listener_type in agent_profile.agent_type.compatible_listener_types:
                    if listener_type not in compatible_listener_types:
                        compatible_listener_types.append(listener_type)
        self._logger.debug(
            "Retrieved compatible listener types from agent type '{}'"
            " ({} compatible listener type(s) retrieved).",
            agent_type_name,
            len(compatible_listener_types),
        )
        return compatible_listener_types

    def get_registered_compatible_agent_types_from_listener_type_name(
        self, listener_type_name: str
    ) -> list[str]:
        compatible_agent_types = []
        for (
            listener_profile
        ) in self._listener_profiles_service.get_all_listener_profiles():
            if str(listener_profile.listener_type.name) == listener_type_name:
                for (
                    agent_type
                ) in listener_profile.listener_type.registered_compatible_agent_types:
                    if agent_type not in compatible_agent_types:
                        compatible_agent_types.append(agent_type)
        self._logger.debug(
            "Retrieved registered compatible agent types from listener type '{}'"
            " ({} compatible agent type(s) retrieved).",
            listener_type_name,
            len(compatible_agent_types),
        )
        return compatible_agent_types

    def is_agent_type_registered(self, agent_type_name: str) -> bool:
        for agent_type in self.get_all_agent_types():
            if str(agent_type.name) == agent_type_name:
                self._logger.debug(
                    "Checked that agent type '{}' is registered.",
                    agent_type_name,
                )
                return True
        self._logger.debug(
            "Checked that agent type '{}' is not registered.",
            agent_type_name,
        )
        return False

    def is_listener_type_registered(self, listener_type_name: str) -> bool:
        for listener_type in self.get_all_listener_types():
            if str(listener_type.name) == listener_type_name:
                self._logger.debug(
                    "Checked that listener type '{}' is registered.",
                    listener_type_name,
                )
                return True
        self._logger.debug(
            "Checked that listener type '{}' is not registered.",
            listener_type_name,
        )
        return False

    def are_c2_types_compatible(
        self,
        agent_type_name: str,
        listener_type_name: str,
    ) -> bool:
        agent_type = self.get_agent_type_by_name(agent_type_name)
        listener_type = self.get_listener_type_by_name(listener_type_name)

        if listener_type in agent_type.compatible_listener_types:
            self._logger.debug(
                "Checked that agent type '{}' and listener type '{}' are compatible.",
                agent_type_name,
                listener_type_name,
            )
            return True
        else:
            self._logger.debug(
                "Checked that agent type '{}' and listener type '{}' are not compatible.",
                agent_type_name,
                listener_type_name,
            )
            return False

    def resolve_registered_compatible_agent_types_for_listener_types(self):
        # for agent_type in self.get_all_agent_types():
        #     for listener_type_name in agent_type.compatible_listener_types:
        #         if self.is_listener_type_registered(listener_type_name):
        #             self._logger.debug(
        #                 "Resolved compatible listener type '{}' for agent type '{}'.",
        #                 listener_type_name,
        #                 agent_type.name,
        #             )
        #             listener_type = self.get_listener_type_by_name(listener_type_name)
        #             listener_type.registered_compatible_agent_types.add(agent_type.name)
        #             continue
        #         else:
        #             self._logger.debug(
        #                 "Could not resolve compatible listener type '{}' for agent type '{}' "
        #                 "because the listener type is not registered.",
        #                 listener_type_name,
        #                 agent_type.name,
        #             )
        # self._logger.debug(
        #     "Resolved all registered compatible agent types for all listener types."
        # )
        pass
