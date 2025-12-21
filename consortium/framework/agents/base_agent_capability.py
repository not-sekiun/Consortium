import asyncio
import sys
from collections.abc import Callable
from enum import Enum, StrEnum
from inspect import signature
from typing import Any, get_type_hints

from pydantic import BaseModel, ConfigDict, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework.agent_message_models import (
    AgentResultMessageModel,
    AgentTaskMessageModel,
)
from consortium.framework.framework_types import Primitive, PrimitiveCollection
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.framework.utils.formatter_utils import format_docstring_to_single_line
from consortium.server.exceptions.consortium_exceptions.agent_capabilities_consortium_exceptions import (
    CustomOSStringAlreadyRegisteredError,
    DuplicateAgentCapabilityOptionNameError,
    EmptyAgentCapabilityNameError,
    InvalidAgentCapabilityConfigurationParameterTypeError,
    MissingAgentCapabilityConfigurationParameterError,
)
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)


class AgentFileManagerService:
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
        raise NotImplementedError
        # asset = self.get_asset_by_asset_id(asset_id)
        # return asset.read()

    def write_artifact_by_artifact_id(self, artifact_id: str, data: bytes) -> None:
        raise NotImplementedError
        # artifact = self.get_artifact_by_artifact_id(artifact_id)
        # artifact.write(data)


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
    authors: set[str]
    requires_admin: bool
    supported_oses: set[SupportedOS]
    is_atomic: bool = False
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ]
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    ) = None


class BaseAgentCapability:
    name: str
    description: str = ""
    authors: set[str] = None
    requires_admin: bool = False
    supported_oses: set[SupportedOS] = None
    is_atomic: bool = False
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ] = None
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    ) = None

    def __init__(self, task_messages_queue: asyncio.Queue):
        # The task messages queue is the overall agent task messages aggregating queue
        # that comes from the framework to be pulled by listeners and sent out to the
        # wire. All agent capabilities share this queue.
        self._task_messages_queue = task_messages_queue
        # The agent result messages queue is per agent capability and serves
        # essentially to allow us to demultiplex messages coming in over the wire from
        # the listener.
        self.result_messages_queue = asyncio.Queue()
        self.file_manager = AgentFileManagerService

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
                raise InvalidAgentCapabilityConfigurationParameterTypeError(
                    agent_capability_str=sys.modules[cls.__module__].__file__,
                    parameter_name=err["loc"][0],
                    parameter_type="list[BaseAgentGeneratorBuildStep]",
                ) from None

        if not cls.name:
            raise EmptyAgentCapabilityNameError(
                agent_capability_filepath=sys.modules[cls.__module__].__file__,
            )
        option_names = []
        for option in cls.options:
            if option.name in option_names:
                raise DuplicateAgentCapabilityOptionNameError(
                    option_name=option.name,
                    agent_capability_name=cls.name,
                )
            option_names.append(option.name)
        # Check that signature of function is minimally valid.
        if cls.validating_function:
            function_signature = signature(cls.validating_function)
            if len(function_signature.parameters) != 1:
                raise InvalidAgentCapabilityConfigurationParameterTypeError(
                    agent_capability_str=cls.name,
                    parameter_name="validating_function",
                    parameter_type=get_type_hints(cls)["validating_function"],
                )
            # We need to convert the validating function to a static method so that the
            # validating function class attribute is considered as just an ordinary
            # function rather than an actual method of the listener template.
            cls.validating_function = staticmethod(cls.validating_function)

        # For convenience purposes when providing the arguments of a particular
        # capability they are declared at the class level in a set (which also
        # implicitly helps prevent duplicate arguments). But when we want to interact
        # programmatically with the capability it is better to provide a dict like
        # interface hence the redeclaration of the class option here.
        # TODO: Find some way to redeclare the typing of this to allow it to play nice
        #  with IDE type suggestions.
        options = {}
        for option in cls.options:
            options[option.name] = option
        cls.options = options

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return (
            f"AgentCapability("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}, "
            f"requires_admin={self.requires_admin!r}, "
            f"supported_oses={self.supported_oses!r}, "
            f"is_atomic={self.is_atomic!r}, "
            f"options={self.options!r}, "
            f"validating_function={self.validating_function!r}"
            f")"
        )

    async def send_to_agent(
        self,
        task_message: AgentTaskMessageModel,
        timeout: int | float | None = None,
    ) -> None:
        if timeout is None:
            await self._task_messages_queue.put(task_message)
        else:
            await asyncio.wait_for(
                self._task_messages_queue.put(task_message),
                timeout=timeout,
            )

    async def recv_from_agent(
        self,
        timeout: int | float | None = None,
    ) -> AgentResultMessageModel:
        if timeout is None:
            return await self.result_messages_queue.get()
        return await asyncio.wait_for(
            self.result_messages_queue.get(),
            timeout=timeout,
        )

    async def send_and_recv_from_agent(
        self,
        task_message: AgentTaskMessageModel,
        timeout: int | float | None = None,
    ) -> AgentResultMessageModel:
        if timeout is None:
            await self.send_to_agent(task_message)
            return await self.recv_from_agent()
        else:
            async with asyncio.timeout(timeout):
                await self.send_to_agent(task_message)
                return await self.recv_from_agent()

    async def run(
        self,
        task_message: AgentTaskMessageModel,
    ) -> AgentResultMessageModel:
        return await self.send_and_recv_from_agent(
            task_message=task_message,
        )

    @classmethod
    def to_json(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description,
            "authors": list(cls.authors),
            "requires_admin": cls.requires_admin,
            "supported_oses": [str(os) for os in cls.supported_oses],
            "is_atomic": cls.is_atomic,
            "options": {
                option.name: option.to_json() for option in cls.options.values()
            },
            "validating_function": format_docstring_to_single_line(
                cls.validating_function.__doc__,
            )
            if cls.validating_function and cls.validating_function.__doc__
            else None,
        }
