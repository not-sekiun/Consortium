import asyncio
import sys
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from enum import Enum, StrEnum
from typing import Any

from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.server.exceptions.framework_exceptions.agent_capabilities_framework_exceptions import (
    AgentCapabilityConfigurationParameterTypeError,
    CustomOSStringAlreadyRegisteredError,
    DuplicateAgentCapabilityArgumentNameError,
    EmptyAgentCapabilityNameError,
    RequiredAgentCapabilityConfigurationParameterNotDeclaredError,
)
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)


class SupportedOS(StrEnum):
    WINDOWS = "WINDOWS"
    LINUX = "LINUX"
    DARWIN = "DARWIN"
    ANY = "ANY"

    @classmethod
    def custom_os(cls, custom_os_string: str) -> Enum:
        if custom_os_string.upper() in list(SupportedOS):
            raise CustomOSStringAlreadyRegisteredError(
                custom_os_string=custom_os_string,
            )

        return Enum(
            "SupportedOS",
            {custom_os_string.upper(): custom_os_string.upper()},
            type=str,
        )[custom_os_string.upper()]


class BaseAgentCapability(ABC):
    name: str
    description: str = ""
    arguments: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ] = None
    requires_admin = False
    supported_oses: set[SupportedOS] = {SupportedOS.ANY}
    authors: set[str] = None

    def __init__(self):
        self.environment = {}
        self.send_agent_task_message_queue = asyncio.Queue()
        self.recv_agent_result_message_queue = asyncio.Queue()

    def __init_subclass__(cls, **kwargs):
        # Check the existence of a provided agent capability name first so that we can
        # reference the agent template name for every other error message.
        if not hasattr(cls, "name"):
            raise RequiredAgentCapabilityConfigurationParameterNotDeclaredError(
                parameter_name="name",
                # Since the agent template cannot be identified by name we identify
                # it by the filepath it was declared in.
                agent_capability=sys.modules[cls.__module__].__file__,
            )
        if not isinstance(cls.name, str):
            raise AgentCapabilityConfigurationParameterTypeError(
                agent_capability=sys.modules[cls.__module__].__file__,
                parameter_name="name",
                parameter_type="str",
            )
        if not cls.name:
            raise EmptyAgentCapabilityNameError(
                agent_capability_filepath=sys.modules[cls.__module__].__file__,
            )

        if not hasattr(cls, "description"):
            raise RequiredAgentCapabilityConfigurationParameterNotDeclaredError(
                parameter_name="agent_generator",
                agent_capability=cls.name,
            )

        if cls.arguments is None:
            cls.arguments = set()
        if cls.supported_oses is None:
            cls.supported_oses = set()
        if cls.authors is None:
            cls.authors = set()

        argument_names = []
        for argument in cls.arguments:
            if not isinstance(
                argument,
                (
                    SingleValueOption,
                    ChoiceValueOption,
                    ListValueOption,
                    DictionaryValueOption,
                    ToggleableChoicesValueOption,
                ),
            ):
                raise AgentCapabilityConfigurationParameterTypeError(
                    error_message=(
                        "The elements of the options set provided must be option "
                        f"objects for agent template '{cls.name}'."
                    ),
                )
            if argument.name in argument_names:
                raise DuplicateAgentCapabilityArgumentNameError(
                    argument_name=argument.name,
                    agent_capability=cls.name,
                )
            argument_names.append(argument.name)

        if not isinstance(cls.description, str):
            raise AgentCapabilityConfigurationParameterTypeError(
                agent_capability=cls.name,
                parameter_name="description",
                parameter_type="str",
            )
        if not isinstance(cls.requires_admin, bool):
            raise AgentCapabilityConfigurationParameterTypeError(
                agent_capability=cls.name,
                parameter_name="requires_admin",
                parameter_type="bool",
            )
        if not isinstance(cls.supported_oses, set):
            raise AgentCapabilityConfigurationParameterTypeError(
                agent_capability=cls.name,
                parameter_name="supported_os",
                parameter_type="set",
            )
        for os in cls.supported_oses:
            if not isinstance(os, Enum):
                raise AgentCapabilityConfigurationParameterTypeError(
                    error_message=(
                        "The elements in the supported operating systems set must be "
                        f"supported operating system enums for agent capability "
                        f"'{cls.name}'."
                    ),
                )

        # For convenience purposes when providing the arguments of a particular
        # capability they are declared at the class level in a set (which also
        # implicitly helps prevent duplicate arguments). But when we want to interact
        # programmatically with the capability it is better to provide a dict like
        # interface hence the redeclaration of the class argument here.
        # TODO: Find some way to redeclare the typing of this to allow it to play nice
        #  with IDE type suggestions.
        arguments = {}
        for agent_capability in cls.arguments:
            arguments[agent_capability.name] = agent_capability
        cls.arguments = arguments

        super().__init_subclass__(**kwargs)

    async def send_agent_task_message(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> None:
        await self.send_agent_task_message_queue.put(agent_task_message)

    async def recv_agent_result_message(
        self,
        timeout: int | float | None = None,
    ) -> AgentResultMessageModel:
        if timeout is None:
            return await self.recv_agent_result_message_queue.get()
        return await asyncio.wait_for(
            self.recv_agent_result_message_queue.get(),
            timeout=timeout,
        )

    async def run_agent_capability(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel: ...

    @abstractmethod
    async def handle_sending_agent_task_messages(
        self,
        agent_message: AgentTaskMessageModel,
    ) -> AsyncGenerator[AgentTaskMessageModel]: ...

    @abstractmethod
    async def handle_receiving_agent_response_messages(
        self,
    ) -> AsyncGenerator[AgentResultMessageModel]: ...

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": {
                argument.name: argument.to_json()
                for argument in self.arguments.values()
            },
            "requires_admin": self.requires_admin,
            "supported_oses": [str(os) for os in self.supported_oses],
            "authors": list(self.authors),
        }
