from loguru import logger

from consortium.framework.agents.base_agent_type import BaseAgentType
from consortium.framework.listeners.base_listener_type import BaseListenerType
from consortium.server.exceptions.consortium_exceptions.c2_types_consortium_exceptions import (
    AgentTypeNotFoundError,
    DuplicateAgentTypeNameError,
    ListenerTypeNotFoundError,
    UnresolvableAgentTypeReferenceError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.c2_profile_objects import ListenerProfile
from consortium.server.services.agent_profiles_service import AgentProfilesService
from consortium.server.services.listener_profiles_service import ListenerProfilesService
from consortium.server.utils import log_and_propagate_error_on_service_method


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

    @log_and_propagate_error_on_service_method
    def get_all_listener_types(self) -> list[BaseListenerType]:
        """Returns all unique listener types across all loaded listener profiles.

        Returns:
            A deduplicated list of all listener types. Empty if no listener profiles
            are loaded.
        """
        listener_types = []
        for (
            listener_profile
        ) in self._listener_profiles_service.get_all_listener_profiles():
            if listener_profile.listener_type not in listener_types:
                listener_types.append(listener_profile.listener_type)
        self._logger.debug(
            "Retrieved all listener types ({} listener type(s) retrieved)",
            len(listener_types),
        )
        return listener_types

    @log_and_propagate_error_on_service_method
    def get_listener_type_by_name(self, listener_type_name: str) -> BaseListenerType:
        """Returns a listener type by its name.

        Args:
            listener_type_name: The name of the listener type to retrieve.

        Returns:
            The matching listener type.

        Raises:
            ListenerTypeNotFoundError: If no listener type with the given name is
                registered.
        """
        for listener_type in self.get_all_listener_types():
            if str(listener_type.name) == listener_type_name:
                self._logger.debug(
                    "Retrieved listener type: {!r}",
                    listener_type,
                )
                return listener_type
        raise ListenerTypeNotFoundError(listener_type_name=listener_type_name)

    @log_and_propagate_error_on_service_method
    def get_all_agent_types(self) -> list[BaseAgentType]:
        """Returns all unique agent types across all loaded agent profiles.

        Returns:
            A deduplicated list of all agent types. Empty if no agent profiles are
            loaded.
        """
        agent_types = []
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            if agent_profile.agent_type not in agent_types:
                agent_types.append(agent_profile.agent_type)
        self._logger.debug(
            "Retrieved all agent types ({} agent type(s) retrieved)",
            len(agent_types),
        )
        return agent_types

    @log_and_propagate_error_on_service_method
    def get_agent_type_by_name(self, agent_type_name: str) -> BaseAgentType:
        """Returns an agent type by its name.

        Args:
            agent_type_name: The name of the agent type to retrieve.

        Returns:
            The matching agent type.

        Raises:
            AgentTypeNotFoundError: If no agent type with the given name is registered.
        """
        for agent_type in self.get_all_agent_types():
            if str(agent_type.name) == agent_type_name:
                self._logger.debug(
                    "Retrieved agent type: {!r}",
                    agent_type,
                )
                return agent_type
        raise AgentTypeNotFoundError(agent_type_name=agent_type_name)

    @log_and_propagate_error_on_service_method
    def get_compatible_listener_types_from_agent_type_name(
        self, agent_type_name: str
    ) -> list[str]:
        """Returns the names of all listener types compatible with the specified
        agent type.

        Compatibility is determined by the `compatible_listener_types` attribute of the
        agent type.

        Args:
            agent_type_name: The name of the agent type to look up.

        Returns:
            A deduplicated list of compatible listener type names. Empty if the agent
            type is not registered or has no compatible listener types.
        """
        compatible_listener_types = []
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            if str(agent_profile.agent_type.name) == agent_type_name:
                for listener_type in agent_profile.agent_type.compatible_listener_types:
                    if listener_type not in compatible_listener_types:
                        compatible_listener_types.append(listener_type)
        self._logger.debug(
            "Retrieved compatible listener types from agent type '{}'"
            " ({} compatible listener type(s) retrieved)",
            agent_type_name,
            len(compatible_listener_types),
        )
        return compatible_listener_types

    @log_and_propagate_error_on_service_method
    def get_registered_compatible_agent_types_from_listener_type_name(
        self, listener_type_name: str
    ) -> list[str]:
        """Returns the names of all registered agent types compatible with the
        specified listener type.

        This is the reverse index of
        `get_compatible_listener_types_from_agent_type_name` and reflects which
        agent types have declared compatibility with the given listener type and
        are currently registered.

        Args:
            listener_type_name: The name of the listener type to look up.

        Returns:
            A deduplicated list of compatible registered agent type names. Empty if
            the listener type is not registered or has no compatible agent types
            registered.
        """
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
            " ({} compatible agent type(s) retrieved)",
            listener_type_name,
            len(compatible_agent_types),
        )
        return compatible_agent_types

    @log_and_propagate_error_on_service_method
    def is_agent_type_registered(self, agent_type_name: str) -> bool:
        """Returns whether an agent type with the given name is currently registered.

        Args:
            agent_type_name: The name of the agent type to check.

        Returns:
            `True` if an agent type with the given name is registered, `False`
            otherwise.
        """
        for agent_type in self.get_all_agent_types():
            if str(agent_type.name) == agent_type_name:
                self._logger.debug(
                    "Checked that agent type '{}' is registered",
                    agent_type_name,
                )
                return True
        self._logger.debug(
            "Checked that agent type '{}' is not registered",
            agent_type_name,
        )
        return False

    @log_and_propagate_error_on_service_method
    def is_listener_type_registered(self, listener_type_name: str) -> bool:
        """Returns whether a listener type with the given name is currently registered.

        Args:
            listener_type_name: The name of the listener type to check.

        Returns:
            `True` if a listener type with the given name is registered, `False`
            otherwise.
        """
        for listener_type in self.get_all_listener_types():
            if str(listener_type.name) == listener_type_name:
                self._logger.debug(
                    "Checked that listener type '{}' is registered",
                    listener_type_name,
                )
                return True
        self._logger.debug(
            "Checked that listener type '{}' is not registered",
            listener_type_name,
        )
        return False

    @log_and_propagate_error_on_service_method
    def are_c2_types_compatible(
        self,
        agent_type_name: str,
        listener_type_name: str,
    ) -> bool:
        """Returns whether the specified agent type and listener type are compatible.

        Args:
            agent_type_name: The name of the agent type to check.
            listener_type_name: The name of the listener type to check.

        Returns:
            `True` if the agent type declares the listener type as compatible,
            `False` otherwise.

        Raises:
            AgentTypeNotFoundError: If no agent type with the given name is registered.
            ListenerTypeNotFoundError: If no listener type with the given name is
                registered.
        """
        agent_type = self.get_agent_type_by_name(agent_type_name)
        listener_type = self.get_listener_type_by_name(listener_type_name)

        if listener_type in agent_type.compatible_listener_types:
            self._logger.debug(
                "Checked that agent type '{}' and listener type '{}' are compatible",
                agent_type_name,
                listener_type_name,
            )
            return True
        else:
            self._logger.debug(
                "Checked that agent type '{}' and listener type '{}' are not compatible",
                agent_type_name,
                listener_type_name,
            )
            return False

    def _resolve_registered_compatible_agent_types_for_listener_profiles(
        self, *listener_profiles: ListenerProfile
    ) -> None:
        if not listener_profiles:
            listener_profiles = (
                self._listener_profiles_service.get_all_listener_profiles()
            )

        # `registered_compatible_agent_types` for each listener type is a reverse index
        # of the `compatible_listener_types` for each agent type.
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            for listener_profile in listener_profiles:
                if (
                    listener_profile.listener_type.name
                    in agent_profile.agent_template.compatible_listener_types
                ):
                    listener_profile.listener_type.registered_compatible_agent_types.add(
                        agent_profile.agent_type.name
                    )

    def _resolve_agent_type_references(self) -> None:
        agent_type_name_to_agent_profile_map = {}
        # Construct a mapping of agent type names to agent profiles for reference
        # resolution. While constructing, check for duplicate agent type names mapped to
        # different agent type classes.
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            agent_type = agent_profile.agent_type
            # At this point agent type could be a string indicating an agent type
            # reference.
            if isinstance(agent_type, BaseAgentType):
                if agent_type.name not in agent_type_name_to_agent_profile_map:
                    agent_type_name_to_agent_profile_map[agent_type.name] = (
                        agent_profile
                    )
                elif (
                    agent_type.__class__
                    is not agent_type_name_to_agent_profile_map[
                        agent_type.name
                    ].agent_type.__class__
                ):
                    raise DuplicateAgentTypeNameError(
                        agent_template_str=str(agent_profile.agent_template),
                        conflicting_agent_template_str=str(
                            agent_type_name_to_agent_profile_map[
                                agent_type.name
                            ].agent_template
                        ),
                        agent_type_name=agent_type.name,
                    )

        # Resolve agent type references in agent profiles.
        for agent_profile in self._agent_profiles_service.get_all_agent_profiles():
            agent_type = agent_profile.agent_type
            if isinstance(agent_type, str):
                if agent_type in agent_type_name_to_agent_profile_map:
                    # Agent types need to be instances of the class
                    agent_profile.agent_type = agent_type_name_to_agent_profile_map[
                        agent_type
                    ]()
                else:
                    raise UnresolvableAgentTypeReferenceError(
                        agent_template_str=str(agent_profile.agent_template),
                        agent_type_name=agent_type,
                    )
