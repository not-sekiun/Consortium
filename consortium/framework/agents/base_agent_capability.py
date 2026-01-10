import asyncio
import sys
from collections.abc import Callable
from enum import Enum, StrEnum
from inspect import signature
from typing import TYPE_CHECKING, Any, get_type_hints

from pydantic import BaseModel, ConfigDict, ValidationError

from consortium.framework._utils import format_docstring_to_single_line
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
from consortium.server.exceptions.consortium_exceptions.agent_capabilities_consortium_exceptions import (
    CustomOSStringAlreadyRegisteredError,
    DuplicateAgentCapabilityOptionNameError,
    EmptyAgentCapabilityNameError,
    InvalidAgentCapabilityConfigurationParameterTypeError,
    MissingAgentCapabilityConfigurationParameterError,
)
from consortium.server.models.agent_task_and_result_models import (
    AgentTaskCurrentProgressModel,
    AgentTaskModel,
    AgentTaskProgressLogModel,
    AgentTaskProgressStatus,
)
from consortium.server.objects.mitre_attack_objects import (
    MitreAttackTechniqueID,
    resolve_mitre_attack_technique_id,
)

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent


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
    is_atomic: bool
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ]
    mitre_attack_techniques: set[MitreAttackTechniqueID]
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    )


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
    mitre_attack_techniques: set[MitreAttackTechniqueID] | None = None
    validating_function: (
        Callable[[dict[str, Primitive | PrimitiveCollection]], None] | None
    ) = None

    # TODO: Deprecate global task messages queue in favor of per capability queues.
    def __init__(
        self, agent: Agent, task: AgentTaskModel, task_messages_queue: asyncio.Queue
    ):
        self.agent = agent
        # The agent task associated with this capability execution. Used for partial
        # task updates
        self._task = task
        # Sequence number to keep track of task progress updates
        self._task_progress_sequence_number = 1
        # The task messages queue is the overall agent task messages aggregating queue
        # that comes from the framework to be pulled by listeners and sent out to the
        # wire. All agent capabilities share this queue.
        self._task_messages_queue = task_messages_queue
        # The agent result messages queue is per agent capability and serves
        # essentially to allow us to demultiplex messages coming in over the wire from
        # the listener.
        self.result_messages_queue = asyncio.Queue()

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
        cls.mitre_attack_techniques = cls.mitre_attack_techniques or set()

        try:
            _BaseAgentCapabilityModel(
                name=cls.name,
                description=cls.description,
                options=cls.options,
                authors=cls.authors,
                requires_admin=cls.requires_admin,
                supported_oses=cls.supported_oses,
                is_atomic=cls.is_atomic,
                mitre_attack_techniques=cls.mitre_attack_techniques,
                validating_function=cls.validating_function,
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

        # Convert mitre attack technique IDs to a list of resolved
        # `MitreAttackTechnique` objects
        cls.mitre_attack_techniques = [
            resolve_mitre_attack_technique_id(mitre_attack_technique_id=technique_id)
            for technique_id in cls.mitre_attack_techniques
        ]

        super().__init_subclass__(**kwargs)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return (
            f"AgentCapability("
            f"name={self.name!r}, "
            f"description={self.description!r}, "
            f"authors={self.authors!r}, "
            f"requires_admin={self.requires_admin!r}, "
            f"supported_oses={self.supported_oses!r}, "
            f"mitre_attack_techniques={self.mitre_attack_techniques!r}, "
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

    def update_task_progress(
        self,
        success: bool = True,
        message: str = "",
        data: dict[str, Any] | None = None,
        percent_complete: int | float = 0,
        log_progress: bool = False,
    ) -> None:
        agent_task_progress = AgentTaskCurrentProgressModel(
            message=message,
            data=data or {},
            status=(
                AgentTaskProgressStatus.SUCCESS
                if success
                else AgentTaskProgressStatus.FAILURE
            ),
            percent_complete=percent_complete,
        )
        self._task.current_progress = agent_task_progress

        if log_progress:
            agent_task_progress_log = AgentTaskProgressLogModel(
                sequence=self._task_progress_sequence_number,
                message=message,
                data=data or {},
                status=(
                    AgentTaskProgressStatus.SUCCESS
                    if success
                    else AgentTaskProgressStatus.FAILURE
                ),
                percent_complete=percent_complete,
            )
            self._task.progress_log.append(agent_task_progress_log)
            self._task_progress_sequence_number += 1

    async def execute(
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
            "mitre_attack_techniques": [
                technique.model_dump(mode="json")
                for technique in cls.mitre_attack_techniques
            ],
            "options": {
                option_name: option.to_json()
                for option_name, option in cls.options.items()
            },
            "validating_function": format_docstring_to_single_line(
                cls.validating_function.__doc__,
            )
            if cls.validating_function and cls.validating_function.__doc__
            else None,
        }
