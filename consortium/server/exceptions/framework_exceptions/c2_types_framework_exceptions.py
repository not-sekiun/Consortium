# """
# Exception hierarchy for C2 types framework:
#
# - BaseFrameworkException: Base class for all framework exceptions.
#   - ListenerTypeConfigurationError: Error in the configuration of the listener type.
#   - ListenerTypeAlreadyExistsError: Listener type already exists in the set of
#   compatible listener types for the specified agent type.
#   - ListenerTypeNotFoundError: Listener type not found in the set of compatible
#   listener types for the specified agent type.
#   - AgentTypeConfigurationError: Error in the configuration of the agent type.
#   - AgentTypeAlreadyExistsError: Agent type already exists in the set of compatible
#   agent types for the specified listener type.
#   - AgentTypeNotFoundError: Agent type not found in the set of compatible agent types
#   for the specified listener type.
# """

from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


class C2TypesFrameworkError(BaseFrameworkException):
    code = "C2_TYPES_FRAMEWORK_ERROR"


class ListenerTypeConfigurationError(C2TypesFrameworkError):
    code = "LISTENER_TYPE_CONFIGURATION_ERROR"


class ListenerTypeConfigurationParameterTypeError(ListenerTypeConfigurationError):
    code = "LISTENER_TYPE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        listener_type_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        # error_message: str = "",
    ):
        super().__init__(
            message=(
                f"Failed to configure the listener type defined at "
                f"'{listener_type_filepath}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the listener type's "
                f"definition."
            ),
        )

        # if not error_message:
        #     super().__init__(
        #         message=(
        #             f"Failed to configure the listener type defined at "
        #             f"'{listener_type_filepath}'. The parameter '{parameter_name}' "
        #             f"must be of type '{parameter_type}' in the listener type's "
        #             f"definition."
        #         ),
        #     )
        # else:
        #     super().__init__(
        #         message=(
        #             f"Failed to configure the listener type defined at "
        #             f"'{listener_type_filepath}'. {error_message}"
        #         ),
        #     )


class EmptyListenerTypeNameError(ListenerTypeConfigurationError):
    code = "EMPTY_LISTENER_TYPE_NAME_ERROR"

    def __init__(self, listener_type_filepath: str):
        super().__init__(
            f"Failed to configure the listener type defined at "
            f"'{listener_type_filepath}'. The name provided in the listener type's "
            f"definition during configuration cannot be empty.",
        )


# class ListenerTypeAlreadyExistsError(C2TypesFrameworkError):
#     code = "LISTENER_TYPE_ALREADY_EXISTS_ERROR"
#
#     # Use the `ListenerType` and `AgentType` class names as strings in the type hints
#     # to avoid circular import issues.
#     def __init__(self, listener_type: "ListenerType", agent_type: "AgentType"):
#         super().__init__(
#             f"Listener type '{listener_type}' already exists in the set of compatible "
#             f"listener types for agent type: {agent_type}",
#         )
#

# class ListenerTypeNotFoundError(C2TypesFrameworkError):
#     code = "LISTENER_TYPE_NOT_FOUND_ERROR"
#
#     def __init__(self, listener_type: "ListenerType", agent_type: "AgentType"):
#         super().__init__(
#             f"Listener type '{listener_type}' not found in the set of compatible "
#             f"listener types for agent type: {agent_type}",
#         )


class AgentTypeConfigurationError(C2TypesFrameworkError):
    code = "AGENT_TYPE_CONFIGURATION_ERROR"


class AgentTypeConfigurationParameterTypeError(AgentTypeConfigurationError):
    code = "AGENT_TYPE_CONFIGURATION_PARAMETER_TYPE_ERROR"

    def __init__(
        self,
        agent_type_filepath: str,
        parameter_name: str | None = None,
        parameter_type: str | None = None,
        # error_message: str = "",
    ):
        super().__init__(
            message=(
                f"Failed to configure the agent type defined at "
                f"'{agent_type_filepath}'. The parameter '{parameter_name}' "
                f"must be of type '{parameter_type}' in the agent type's "
                f"definition."
            ),
        )

        # if not error_message:
        #     super().__init__(
        #         message=(
        #             f"Failed to configure the agent type defined at "
        #             f"'{agent_type_filepath}'. The parameter '{parameter_name}' "
        #             f"must be of type '{parameter_type}' in the listener type's "
        #             f"definition."
        #         ),
        #     )
        # else:
        #     super().__init__(
        #         message=(
        #             f"Failed to configure the agent type defined at "
        #             f"'{agent_type_filepath}'. {error_message}"
        #         ),
        #     )


class EmptyAgentTypeNameError(AgentTypeConfigurationError):
    code = "EMPTY_AGENT_TYPE_NAME_ERROR"

    def __init__(self, agent_type_filepath: str):
        super().__init__(
            f"Failed to configure the agent type defined at "
            f"'{agent_type_filepath}'. The name provided in the agent type's "
            f"definition during configuration cannot be empty.",
        )


# class AgentTypeAlreadyExistsError(C2TypesFrameworkError):
#     code = "AGENT_TYPE_ALREADY_EXISTS_ERROR"
#
#     def __init__(self, agent_type: "AgentType", listener_type: "ListenerType"):
#         super().__init__(
#             f"Agent type '{agent_type}' already exists in the set of compatible agent "
#             f"types for listener type: {listener_type}",
#         )
#
#
# class AgentTypeNotFoundError(C2TypesFrameworkError):
#     code = "AGENT_TYPE_NOT_FOUND_ERROR"
#
#     def __init__(self, agent_type_name: str):
#         super().__init__(
#             f"Failed to find agent type '{agent_type_name}'. Check that the agent "
#             f"profile configured with this agent type exists and that the agent type "
#             f"name is correct.",
#         )

# def __init__(self, agent_type: "AgentType", listener_type: "ListenerType"):
#     super().__init__(
#         f"Agent type '{agent_type}' not found in the set of compatible agent "
#         f"types for listener type: {listener_type}",
#     )
