from loguru import logger

from consortium.framework.c2_types import AgentType, ListenerType
from consortium.server.exceptions.service_exceptions.c2_types_service_exceptions import (
    AgentTypeNotFoundError,
    ListenerTypeNotFoundError,
)
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
        self.c2_types_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.c2_types_service_logger.debug(
            f"Started {self}",
        )

    def __str__(self) -> str:
        return "Consortium C2 Types Service"

    def __repr__(self) -> str:
        return "C2TypesService()"

    def get_all_listener_types(self) -> list[ListenerType]:
        listener_types = []
        for (
            listener_profile
        ) in self._listener_profiles_service.get_all_listener_profiles():
            if listener_profile.listener_type not in listener_types:
                listener_types.append(listener_profile.listener_type)
        self.c2_types_service_logger.debug(
            f"Retrieved all listener types ({len(listener_types)} listener type(s) "
            f"retrieved).",
        )
        return listener_types

    def get_listener_type_by_listener_type_id(
        self,
        listener_type_id: str,
    ):
        for listener_type in self.get_all_listener_types():
            if str(listener_type.listener_type_id) == listener_type_id:
                self.c2_types_service_logger.debug(
                    f"Retrieved listener type: {listener_type!r}",
                )
                return listener_type
        raise ListenerTypeNotFoundError(listener_type_id=listener_type_id)

    def get_all_agent_types(self) -> list[AgentType]:
        agent_types = []
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            if agent_profile.agent_type not in agent_types:
                agent_types.append(agent_profile.agent_type)
        self.c2_types_service_logger.debug(
            f"Retrieved all agent types ({len(agent_types)} agent type(s) retrieved).",
        )
        return agent_types

    def get_agent_type_by_agent_type_id(
        self,
        agent_type_id: str,
    ):
        for agent_type in self.get_all_agent_types():
            if str(agent_type.agent_type_id) == agent_type_id:
                self.c2_types_service_logger.debug(
                    f"Retrieved agent type: {agent_type!r}",
                )
                return agent_type
        raise AgentTypeNotFoundError(agent_type_id=agent_type_id)
