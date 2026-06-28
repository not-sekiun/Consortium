import sys
from collections.abc import Callable
from enum import StrEnum
from inspect import signature
from typing import TYPE_CHECKING, Any, get_type_hints

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

import consortium.server.server_singletons as server_singletons
from consortium.framework._utils import format_docstring_to_single_line
from consortium.framework.agents._agent_communicator import _AgentCommunicator
from consortium.framework.agents.agent_message_models import (
    TaskLaunchMessageModel,
)
from consortium.framework.agents.agent_outcomes import Failure, Success
from consortium.framework.options import (
    ChoiceValueOption,
    DictionaryValueOption,
    ListValueOption,
    SingleValueOption,
    ToggleableChoicesValueOption,
)
from consortium.server.exceptions.consortium_exceptions.agent_capabilities_consortium_exceptions import (
    DuplicateAgentCapabilityOptionNameError,
    EmptyAgentCapabilityNameError,
    InvalidAgentCapabilityConfigurationParameterTypeError,
    MissingAgentCapabilityConfigurationParameterError,
)
from consortium.server.models.agent_task_models import AgentTaskEventType
from consortium.server.objects.mitre_attack_objects import (
    # MitreAttackTechniqueID,
    resolve_mitre_attack_technique_id,
)
from consortium.server.utils import construct_services_namespace_object

if TYPE_CHECKING:
    from consortium.server.objects.agent_objects import Agent
    from consortium.server.objects.agent_task_objects import AgentTask


class SupportedOS(StrEnum):
    WINDOWS = "WINDOWS"
    LINUX = "LINUX"
    MACOS = "MACOS"
    ANDROID = "ANDROID"
    IOS = "IOS"
    ANY = "ANY"

    # Add type hinting here for IDE autocompletion support.
    DESKTOP: set[SupportedOS]
    MOBILE: set[SupportedOS]


# Add convenience groupings of supported OSes as class attributes after enum creation.
SupportedOS.DESKTOP = {SupportedOS.WINDOWS, SupportedOS.LINUX, SupportedOS.MACOS}
SupportedOS.MOBILE = {SupportedOS.ANDROID, SupportedOS.IOS}


class AgentLifecycle(StrEnum):
    ON_REGISTERED = "ON_REGISTERED"
    ON_CHECKED_IN = "ON_CHECKED_IN"


class _BaseAgentCapabilityModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    authors: set[str]
    requires_admin: bool
    supported_oses: set[SupportedOS | str]
    # Note: `is_atomic` is deliberately excluded from the output of `to_json()` because
    # it's an internal implementation detail that while part of the developer framework
    # API is not of concern to REST API consumers.
    is_atomic: bool
    options: set[
        SingleValueOption
        | ListValueOption
        | DictionaryValueOption
        | ChoiceValueOption
        | ToggleableChoicesValueOption
    ]
    mitre_attack_techniques: set[str]  # set[MitreAttackTechniqueID]
    validating_function: Callable[[dict[str, JsonValue]], None] | None


class Drop:
    pass


class Deny:
    def __init__(self, reason: str = ""):
        self.reason = reason


class BaseAgentCapability(_AgentCommunicator):
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
    mitre_attack_techniques: set[str] | None = None  # set[MitreAttackTechniqueID]
    validating_function: Callable[[dict[str, JsonValue]], None] | None = None
    launch_message: TaskLaunchMessageModel | None = None

    def __init__(self, agent: Agent, task: AgentTask):
        super().__init__(agent=agent, task=task)

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
        cls.services = construct_services_namespace_object(
            server_singletons=server_singletons
        )
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
            raise InvalidAgentCapabilityConfigurationParameterTypeError(
                agent_capability_str=sys.modules[cls.__module__].__file__,
                parameter_name=exc.errors()[0]["loc"][0],
                parameter_type=get_type_hints(_BaseAgentCapabilityModel)[
                    exc.errors()[0]["loc"][0]
                ],
            ) from None

        if not cls.name:
            raise EmptyAgentCapabilityNameError(
                agent_capability_filepath=sys.modules[cls.__module__].__file__,
            )
        # Normalize supported OSes to enum values if any valid supported OSes are
        # provided as strings. Otherwise, leave as is to allow for declaration of
        # custom/niche OSes.
        for os in cls.supported_oses:
            if isinstance(os, str):
                if os.lower() in SupportedOS:
                    cls.supported_oses.remove(os)
                    cls.supported_oses.add(SupportedOS(os.lower()))
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

    def update_progress(
        self,
        percent_complete: float = 0,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        self.task.update_progress(
            percent_complete=percent_complete, message=message, data=data
        )

    def emit_success(self, message: str, data: dict[str, Any] | None = None):
        self.task.append_event(
            event_type=AgentTaskEventType.SUCCESS, message=message, data=data or {}
        )

    def emit_info(self, message: str, data: dict[str, Any] | None = None):
        self.task.append_event(
            event_type=AgentTaskEventType.INFO, message=message, data=data or {}
        )

    def emit_failure(self, message: str, data: dict[str, Any] | None = None):
        self.task.append_event(
            event_type=AgentTaskEventType.FAILURE, message=message, data=data or {}
        )

    def emit_artifact(self, message: str, data: dict[str, Any] | None = None):
        self.task.append_event(
            event_type=AgentTaskEventType.ARTIFACT, message=message, data=data or {}
        )

    async def on_launch(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> TaskLaunchMessageModel | Drop | Deny:
        return task_message

    async def on_execute(self) -> Success | Failure | None:
        task_output_message = await self.recv_from_agent()
        return (
            Success(task_output_message=task_output_message)
            if task_output_message.success
            else Failure(task_output_message=task_output_message)
        )

    async def execute(
        self,
        task_message: TaskLaunchMessageModel,
    ) -> Success | Failure | None:
        result = await self.on_launch(task_message)
        if isinstance(result, Drop):
            return None
        if isinstance(result, Deny):
            return Failure(message=result.reason)
        self.launch_message = result
        await self.agent.send_task_message(task_message=self.launch_message)
        return await self.on_execute()

    @classmethod
    def to_json(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description,
            "authors": list(cls.authors),
            "requires_admin": cls.requires_admin,
            "supported_oses": [str(os) for os in cls.supported_oses],
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
