import asyncio
import sys
from abc import ABC, abstractmethod
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

import consortium.server.server_singletons as server_singletons
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
    DuplicateAgentCapabilityOptionNameError,
    EmptyAgentCapabilityNameError,
    MissingAgentCapabilityConfigurationParameterError,
)
from consortium.server.models.agent_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)


class AgentFileManager:
    def __init__(self):
        # Assets service consists of all uploaded files onto the server that are meant
        # to be read only by agents.
        self._assets_service = server_singletons.assets_service
        self._artifacts_service = server_singletons.artifacts_service

    def get_all_assets(self) -> list[RepositoryFile | RepositoryDirectory]:
        return self._assets_service.get_all_repository_resources()

    def get_asset_by_asset_id(
        self,
        asset_id: str,
    ) -> RepositoryFile | RepositoryDirectory:
        return self._assets_service.get_repository_resource_by_resource_id(
            resource_id=asset_id,
        )

    def get_all_artifacts(self) -> list[RepositoryFile | RepositoryDirectory]:
        return self._artifacts_service.get_all_repository_resources()

    def get_artifact_by_artifact_id(
        self,
        artifact_id: str,
    ) -> RepositoryFile | RepositoryDirectory:
        return self._artifacts_service.get_repository_resource_by_resource_id(
            resource_id=artifact_id,
        )

    def read_asset_by_asset_id(self, asset_id: str) -> bytes:
        asset = self.get_asset_by_asset_id(asset_id)
        return asset.read()

    def write_artifact_by_artifact_id(self, artifact_id: str, data: bytes) -> None:
        artifact = self.get_artifact_by_artifact_id(artifact_id)
        artifact.write(data)


class SupportedOS(StrEnum):
    WINDOWS = "WINDOWS"
    LINUX = "LINUX"
    DARWIN = "DARWIN"
    ANY = "ANY"

    @classmethod
    def custom_os(cls, custom_os_string: str) -> Enum:
        if custom_os_string.upper() in list(SupportedOS):
            raise CustomOSStringAlreadyRegisteredError(
                custom_os_str=custom_os_string,
            )

        return Enum(
            "SupportedOS",
            {custom_os_string.upper(): custom_os_string.upper()},
            type=str,
        )[custom_os_string.upper()]


class _BaseAgentCapabilityModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ]
    authors: set[str]
    requires_admin: bool
    supported_oses: set[SupportedOS]


class BaseAgentCapability(ABC):
    name: str
    description: str = ""
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ] = None
    authors: set[str] = None
    requires_admin: bool = False
    supported_oses: set[SupportedOS] = None

    def __init__(self, agent_task_messages_queue: asyncio.Queue):
        # The task messages queue is the overall agent task messages aggregating queue
        # that comes from the agent. All agent capabilities share this queue.
        self._agent_task_messages_queue = agent_task_messages_queue
        # The agent result messages queue is per agent capability and serves
        # essentially to allow us to demultiplex messages coming in over the wire from
        # the listener.
        self.agent_result_messages_queue = asyncio.Queue()
        self.file_manager = AgentFileManager

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "name"):
            raise MissingAgentCapabilityConfigurationParameterError(
                parameter_name="name",
                # Since the agent template cannot be identified by name we identify
                # it by the filepath it was declared in.
                agent_capability_filepath=sys.modules[cls.__module__].__file__,
            )

        cls.options = cls.options or set()
        cls.supported_oses = cls.supported_oses or {SupportedOS.ANY}
        cls.authors = cls.authors or set()

        try:
            _BaseAgentCapabilityModel(
                name=cls.name,
                description=cls.description,
                options=cls.options,
                authors=cls.authors,
                requires_admin=cls.requires_admin,
                supported_oses=cls.supported_oses,
            )
        except ValidationError as exc:
            for err in exc.errors():
                raise AgentCapabilityConfigurationParameterTypeError(
                    agent_capability_filepath=sys.modules[cls.__module__].__file__,
                    parameter_name=err["loc"][0],
                    parameter_type="list[BaseAgentGeneratorBuildStep]",
                ) from None

        if not cls.name:
            raise EmptyAgentCapabilityNameError(
                agent_capability_filepath=sys.modules[cls.__module__].__file__,
            )
        argument_names = []
        for argument in cls.options:
            if argument.name in argument_names:
                raise DuplicateAgentCapabilityOptionNameError(
                    argument_name=argument.name,
                    agent_capability_filepath=cls.name,
                )
            argument_names.append(argument.name)

        # For convenience purposes when providing the arguments of a particular
        # capability they are declared at the class level in a set (which also
        # implicitly helps prevent duplicate arguments). But when we want to interact
        # programmatically with the capability it is better to provide a dict like
        # interface hence the redeclaration of the class argument here.
        # TODO: Find some way to redeclare the typing of this to allow it to play nice
        #  with IDE type suggestions.
        options = {}
        for option in cls.options:
            options[option.name] = option
        cls.options = options

        super().__init_subclass__(**kwargs)

    async def send_agent_task_message(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> None:
        await self._agent_task_messages_queue.put(agent_task_message)

    async def recv_agent_result_message(
        self,
        timeout: int | float | None = None,
    ) -> AgentResultMessageModel:
        if timeout is None:
            return await self.agent_result_messages_queue.get()
        return await asyncio.wait_for(
            self.agent_result_messages_queue.get(),
            timeout=timeout,
        )

    async def send_agent_task_message_and_recv_agent_result_message(
        self,
        agent_task_message: AgentTaskMessageModel,
        timeout: int | float | None = None,
    ) -> AgentResultMessageModel:
        await self.send_agent_task_message(agent_task_message)
        return await self.recv_agent_result_message(timeout=timeout)

    @abstractmethod
    async def run_agent_capability(
        self,
        agent_task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel: ...

    @classmethod
    def to_json(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description,
            "options": {
                option.name: option.to_json() for option in cls.options.values()
            },
            "authors": list(cls.authors),
            "requires_admin": cls.requires_admin,
            "supported_oses": [str(os) for os in cls.supported_oses],
        }
