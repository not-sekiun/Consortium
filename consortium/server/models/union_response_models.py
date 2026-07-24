# Named response models for endpoints whose error responses may be one of several error
# shapes. Passing a bare union (`A | B`) as a route's response `model` leaves the union
# anonymous, so OpenAPI client generators invent ugly names like
# `Response404GetAgentTasksByAgentIdAndTaskId`. Each model below wraps its union in a
# single named RootModel (via `create_union_response_model`) so the generated schema
# component, and therefore the generated client model, has a stable, readable name.
#
# The representative exception instances constructed here exist only to resolve each
# member's cached pydantic model (and its example) through `to_pydantic_model()`. They
# mirror the placeholder instances the API modules use, and because `to_pydantic_model()`
# caches by exception class, the union members line up with the same components the rest
# of the schema references.
from consortium.framework._core.framework_exceptions import (
    agent_generators_framework_exceptions,
    agent_templates_framework_exceptions,
    listener_templates_framework_exceptions,
    listeners_framework_exceptions,
)
from consortium.server.exceptions.api_exceptions import (
    agent_generators_api_exceptions,
    agent_templates_api_exceptions,
    agents_api_exceptions,
    listener_templates_api_exceptions,
    listeners_api_exceptions,
    repository_api_exceptions,
    user_accounts_api_exceptions,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.object_exceptions import agent_object_exceptions
from consortium.server.exceptions.service_exceptions import (
    agent_generators_service_exceptions,
    agents_service_exceptions,
    listeners_service_exceptions,
    user_accounts_service_exceptions,
)
from consortium.server.utils import create_union_response_model

# Shared request-validation members. A malformed UUID path parameter and a failed
# Pydantic body validation are the two ways almost every endpoint can reject a request.
_invalid_uuid_error = InvalidUUIDError(
    resource_name="resource", uuid_value="<uuid_value>"
)
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
)

# Agents.
_agent_not_found_error = (
    agents_api_exceptions.AgentNotFoundError.from_consortium_exception(
        consortium_exception=agents_service_exceptions.AgentNotFoundError(
            agent_id="string"
        ),
    )
)
_agent_task_not_found_error = (
    agents_api_exceptions.AgentTaskNotFoundError.from_consortium_exception(
        consortium_exception=agent_object_exceptions.AgentTaskNotFoundError(
            task_id="string"
        ),
    )
)
_agent_capability_option_value_validation_error = agents_api_exceptions.AgentCapabilityOptionValueValidationError.from_consortium_exception(
    consortium_exception=agent_object_exceptions.AgentCapabilityOptionValueValidationError(
        agent_str="<agent_str>",
        option_name="<option_str>",
        option_value="<option_value>",
        error_message="<error_message>",
    ),
)
_agent_capability_option_not_found_error = (
    agents_api_exceptions.AgentCapabilityOptionNotFoundError.from_consortium_exception(
        consortium_exception=agent_object_exceptions.AgentCapabilityOptionNotFoundError(
            agent_str="<agent_str>",
            option_name="<option_str>",
            command="<command>",
            agent_type_str="<agent_type_str>",
        ),
    )
)
_missing_required_agent_capability_option_error = agents_api_exceptions.MissingRequiredAgentCapabilityOptionError.from_consortium_exception(
    consortium_exception=agent_object_exceptions.MissingRequiredAgentCapabilityOptionError(
        agent_str="<agent_str>",
        option_name="<option_str>",
        agent_capability_name="<agent_capability_name>",
    ),
)
_agent_capability_not_found_error = (
    agents_api_exceptions.AgentCapabilityNotFoundError.from_consortium_exception(
        consortium_exception=agent_object_exceptions.AgentCapabilityNotFoundError(
            command="<command>",
            agent_str="<agent_str>",
            agent_type_str="<agent_type_str>",
        ),
    )
)

# Listeners.
_listener_already_running_error = (
    listeners_api_exceptions.ListenerAlreadyRunningError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerAlreadyRunningError(
            listener_str="<listener_string>",
        ),
    )
)
_listener_start_error = (
    listeners_api_exceptions.ListenerStartError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerStartError(
            listener_str="<listener_string>",
            error_message="<error_message>",
            detail={"<key>": "<value>"},
        ),
    )
)
_listener_not_running_error = (
    listeners_api_exceptions.ListenerNotRunningError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerNotRunningError(
            listener_str="<listener_string>",
        ),
    )
)
_listener_stop_error = (
    listeners_api_exceptions.ListenerStopError.from_consortium_exception(
        consortium_exception=listeners_framework_exceptions.ListenerStopError(
            listener_str="<listener_string>",
            error_message="<error_message>",
            detail={"<key>": "<value>"},
        ),
    )
)
_invalid_listener_parameter_name_error = listeners_api_exceptions.InvalidListenerParameterNameError.from_consortium_exception(
    consortium_exception=listeners_service_exceptions.InvalidListenerParameterNameError(
        listener_str="<listener_str>",
        parameter_name="<parameter_name>",
    ),
)
_invalid_listener_parameter_value_error = listeners_api_exceptions.InvalidListenerParameterValueError.from_consortium_exception(
    consortium_exception=listeners_service_exceptions.InvalidListenerParameterValueError(
        listener_str="<listener_str>",
        parameter_name="<parameter_name>",
        parameter_value="<parameter_value>",
        error_message="<error_message>",
    ),
)

# Agent generators.
_agent_generator_already_running_error = agent_generators_api_exceptions.AgentGeneratorAlreadyRunningError.from_consortium_exception(
    consortium_exception=agent_generators_framework_exceptions.AgentGeneratorAlreadyRunningError(
        agent_generator_str="<agent_generator_str>",
    ),
)
_agent_generator_start_error = agent_generators_api_exceptions.AgentGeneratorStartError.from_consortium_exception(
    consortium_exception=agent_generators_framework_exceptions.AgentGeneratorStartError(
        agent_generator_str="<agent_generator_str>",
        error_message="<error_message>",
        detail={"<key>": "<value>"},
    ),
)
_agent_generator_not_running_error = agent_generators_api_exceptions.AgentGeneratorNotRunningError.from_consortium_exception(
    consortium_exception=agent_generators_framework_exceptions.AgentGeneratorNotRunningError(
        agent_generator_str="<agent_generator_str>",
    ),
)
_agent_generator_stop_error = agent_generators_api_exceptions.AgentGeneratorStopError.from_consortium_exception(
    consortium_exception=agent_generators_framework_exceptions.AgentGeneratorStopError(
        agent_generator_str="<agent_generator_str>",
        error_message="<error_message>",
        detail={"<key>": "<value>"},
    ),
)
_invalid_agent_generator_parameter_name_error = agent_generators_api_exceptions.InvalidAgentGeneratorParameterNameError.from_consortium_exception(
    consortium_exception=agent_generators_service_exceptions.InvalidAgentGeneratorParameterNameError(
        parameter_name="<parameter_name>",
        agent_generator_str="<agent_generator>",
    ),
)
_invalid_agent_generator_parameter_value_error = agent_generators_api_exceptions.InvalidAgentGeneratorParameterValueError.from_consortium_exception(
    consortium_exception=agent_generators_service_exceptions.InvalidAgentGeneratorParameterValueError(
        agent_generator_str="<agent_generator>",
        parameter_name="<parameter_name>",
        parameter_value="<parameter_value>",
        error_message="<error_message>",
    ),
)

# Agent templates.
_agent_template_option_value_error = agent_templates_api_exceptions.AgentTemplateOptionValueValidationError.from_consortium_exception(
    consortium_exception=agent_templates_framework_exceptions.AgentTemplateOptionValueValidationError(
        agent_template_str="<agent_template>",
        option_name="<option_str>",
        option_value="<option_value>",
        error_message="<error_message>",
    ),
)
_agent_template_option_not_found_error = agent_templates_api_exceptions.AgentTemplateOptionNotFoundError.from_consortium_exception(
    consortium_exception=agent_templates_framework_exceptions.AgentTemplateOptionNotFoundError(
        agent_template_str="<agent_template>",
        option_name="<option_str>",
    ),
)
_missing_required_agent_template_option_error = agent_templates_api_exceptions.MissingRequiredAgentTemplateOptionError.from_consortium_exception(
    consortium_exception=agent_templates_framework_exceptions.MissingRequiredAgentTemplateOptionError(
        agent_template_str="<agent_template>",
        option_name="<option_str>",
    ),
)

# Listener templates.
_listener_template_option_value_validation_error = listener_templates_api_exceptions.ListenerTemplateOptionValueValidationError.from_consortium_exception(
    consortium_exception=listener_templates_framework_exceptions.ListenerTemplateOptionValueValidationError(
        listener_template_str="<listener_template_str>",
        option_name="<option_str>",
        option_value="<option_value>",
        error_message="<error_message>",
    ),
)
_listener_template_option_not_found_error = listener_templates_api_exceptions.ListenerTemplateOptionNotFoundError.from_consortium_exception(
    consortium_exception=listener_templates_framework_exceptions.ListenerTemplateOptionNotFoundError(
        listener_template_str="<listener_template>",
        option_name="<option_str>",
    ),
)
_missing_required_listener_template_option_error = listener_templates_api_exceptions.MissingRequiredListenerTemplateOptionError.from_consortium_exception(
    consortium_exception=listener_templates_framework_exceptions.MissingRequiredListenerTemplateOptionError(
        listener_template_str="<listener_template>",
        option_name="<option_str>",
    ),
)

# User accounts. Creation and modification variants of each exception resolve to the same
# cached model, so the modification variants stand in for both here.
_user_account_username_already_exists_error = user_accounts_api_exceptions.UserAccountUsernameAlreadyExistsError.from_consortium_exception(
    consortium_exception=user_accounts_service_exceptions.UserAccountUsernameAlreadyExistsError._during_user_account_modification(
        username="<username>",
        user_account_str="<user_account>",
    ),
)
_empty_user_account_username_error = user_accounts_api_exceptions.EmptyUserAccountUsernameError.from_consortium_exception(
    consortium_exception=user_accounts_service_exceptions.EmptyUserAccountUsernameError()._during_user_account_modification(
        user_account_str="<user_account>",
    ),
)
_empty_user_account_password_error = user_accounts_api_exceptions.EmptyUserAccountPasswordError.from_consortium_exception(
    consortium_exception=user_accounts_service_exceptions.EmptyUserAccountPasswordError()._during_user_account_modification(
        user_account_str="<user_account>",
    ),
)
_invalid_user_account_role_error = user_accounts_api_exceptions.InvalidUserAccountRoleError.from_consortium_exception(
    consortium_exception=user_accounts_service_exceptions.InvalidUserAccountRoleError._during_user_account_modification(
        user_account_str="<user_account>",
        role="<role>",
    ),
)

# Assets (directory upload archive validation).
_archive_file_format_not_specified_error = (
    repository_api_exceptions.RepositoryDirectoryArchiveFileFormatNotSpecifiedError()
)
_invalid_archive_file_format_error = (
    repository_api_exceptions.InvalidRepositoryDirectoryArchiveFileFormatError()
)
_directory_file_not_archive_file_error = (
    repository_api_exceptions.RepositoryDirectoryFileNotArchiveFileError()
)


# Shared: a malformed UUID path parameter or an unprocessable request body. Declared on
# nearly every read/update/delete/lifecycle endpoint that takes a UUID path parameter.
RequestValidationErrorResponse = create_union_response_model(
    "RequestValidationErrorResponse",
    (_invalid_uuid_error, _unprocessable_entity_error),
)

# Shared: the agent, the task, or both could not be found.
AgentOrAgentTaskNotFoundErrorResponse = create_union_response_model(
    "AgentOrAgentTaskNotFoundErrorResponse",
    (_agent_not_found_error, _agent_task_not_found_error),
)

# Tasking an agent: capability and option validation on top of the shared request errors.
AgentTaskingValidationErrorResponse = create_union_response_model(
    "AgentTaskingValidationErrorResponse",
    (
        _invalid_uuid_error,
        _agent_capability_option_value_validation_error,
        _missing_required_agent_capability_option_error,
        _agent_capability_option_not_found_error,
        _agent_capability_not_found_error,
        _unprocessable_entity_error,
    ),
)

# Listener lifecycle conflicts.
ListenerStartConflictErrorResponse = create_union_response_model(
    "ListenerStartConflictErrorResponse",
    (_listener_already_running_error, _listener_start_error),
)
ListenerStopConflictErrorResponse = create_union_response_model(
    "ListenerStopConflictErrorResponse",
    (_listener_not_running_error, _listener_stop_error),
)

# Updating a listener: parameter validation on top of the shared request errors.
ListenerUpdateValidationErrorResponse = create_union_response_model(
    "ListenerUpdateValidationErrorResponse",
    (
        _invalid_uuid_error,
        _invalid_listener_parameter_name_error,
        _invalid_listener_parameter_value_error,
        _unprocessable_entity_error,
    ),
)

# Agent generator lifecycle conflicts.
AgentGeneratorStartConflictErrorResponse = create_union_response_model(
    "AgentGeneratorStartConflictErrorResponse",
    (_agent_generator_already_running_error, _agent_generator_start_error),
)
AgentGeneratorStopConflictErrorResponse = create_union_response_model(
    "AgentGeneratorStopConflictErrorResponse",
    (_agent_generator_not_running_error, _agent_generator_stop_error),
)

# Updating an agent generator: parameter validation on top of the shared request errors.
AgentGeneratorUpdateValidationErrorResponse = create_union_response_model(
    "AgentGeneratorUpdateValidationErrorResponse",
    (
        _invalid_uuid_error,
        _invalid_agent_generator_parameter_name_error,
        _invalid_agent_generator_parameter_value_error,
        _unprocessable_entity_error,
    ),
)

# Creating an agent generator from a template: template option validation.
AgentTemplateOptionsValidationErrorResponse = create_union_response_model(
    "AgentTemplateOptionsValidationErrorResponse",
    (
        _invalid_uuid_error,
        _agent_template_option_value_error,
        _agent_template_option_not_found_error,
        _missing_required_agent_template_option_error,
        _unprocessable_entity_error,
    ),
)

# Creating a listener from a template: template option validation.
ListenerTemplateOptionsValidationErrorResponse = create_union_response_model(
    "ListenerTemplateOptionsValidationErrorResponse",
    (
        _invalid_uuid_error,
        _listener_template_option_value_validation_error,
        _listener_template_option_not_found_error,
        _missing_required_listener_template_option_error,
        _unprocessable_entity_error,
    ),
)

# Creating a user account: username, password, and role validation.
UserAccountCreationValidationErrorResponse = create_union_response_model(
    "UserAccountCreationValidationErrorResponse",
    (
        _empty_user_account_username_error,
        _empty_user_account_password_error,
        _invalid_user_account_role_error,
        _unprocessable_entity_error,
    ),
)

# Updating one's own user account: no role change and no UUID path parameter.
OwnUserAccountUpdateValidationErrorResponse = create_union_response_model(
    "OwnUserAccountUpdateValidationErrorResponse",
    (
        _user_account_username_already_exists_error,
        _empty_user_account_username_error,
        _empty_user_account_password_error,
        _unprocessable_entity_error,
    ),
)

# Updating a user account by id: adds role validation and the UUID path parameter.
UserAccountUpdateValidationErrorResponse = create_union_response_model(
    "UserAccountUpdateValidationErrorResponse",
    (
        _user_account_username_already_exists_error,
        _empty_user_account_username_error,
        _empty_user_account_password_error,
        _invalid_user_account_role_error,
        _invalid_uuid_error,
        _unprocessable_entity_error,
    ),
)

# Uploading an asset directory: the archive file format could not be resolved or is not a
# supported archive.
AssetUploadArchiveFormatErrorResponse = create_union_response_model(
    "AssetUploadArchiveFormatErrorResponse",
    (
        _archive_file_format_not_specified_error,
        _invalid_archive_file_format_error,
        _directory_file_not_archive_file_error,
    ),
)
