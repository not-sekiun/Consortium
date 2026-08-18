# JSON schemas for the /api response bodies asserted on across this package.
#
# Everything the api tests validate against lives here rather than beside the test that
# first needed it, so a response shape has one definition and drifts in one place. The
# standard HTTP error envelopes (401, 403, 404, 405, 422 and invalid UUID) are the one
# exception and stay in `common_json_response_schemas`: they belong to the API's error
# handling rather than to any framework component.
#
# Schemas mirror the Pydantic response models in consortium/server/models. Where a
# schema and its model disagree the model is right, so anything added to a model
# belongs here too.


def error_json_schema(code: str, detail_json_schema: dict | None = None) -> dict:
    # Every API error serializes into the same envelope and differs only by its `code`,
    # so building them from one factory keeps a new endpoint's errors from re-deriving
    # the shape. `detail` is untyped unless an endpoint documents structure in it.
    return {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "enum": [code]},
                    "message": {"type": "string"},
                    "detail": detail_json_schema or {"type": ["object", "null"]},
                },
                "required": ["code", "message", "detail"],
            },
        },
        "required": ["error"],
    }


def array_of(item_json_schema: dict) -> dict:
    # The `/all` collection endpoints return a bare array of the resource they list.
    return {"type": "array", "items": item_json_schema}


# --- Shared building blocks -----------------------------------------------------------

STATUS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": "string"},
        "error": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "detail": {"type": ["object", "null"]},
                    },
                    "required": ["code", "message", "detail"],
                    "additionalProperties": False,
                },
            ],
        },
    },
    "required": ["state", "error"],
    "additionalProperties": False,
}

# Shared schema for the event log attached to tasks, listeners, and agent generators.
EVENT_LOG_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "current_progress": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "percent_complete": {"type": "number"},
                        "message": {"type": ["string", "null"]},
                        "data": {"type": "object"},
                        "datetime_reported": {"type": "string"},
                    },
                    "required": [
                        "percent_complete",
                        "message",
                        "data",
                        "datetime_reported",
                    ],
                    "additionalProperties": False,
                },
            ],
        },
        "total_count": {"type": "integer"},
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sequence": {"type": "integer"},
                    "event_type": {"type": "string"},
                    "message": {"type": ["string", "null"]},
                    "data": {"type": "object"},
                    "datetime_reported": {"type": "string"},
                },
                "required": [
                    "sequence",
                    "event_type",
                    "message",
                    "data",
                    "datetime_reported",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["current_progress", "total_count", "entries"],
    "additionalProperties": False,
}

MITRE_ATTACK_TECHNIQUE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "mitre_attack_technique_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "tactics": {"type": "array", "items": {"type": "string"}},
        "url": {"type": "string"},
        "platforms": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "mitre_attack_technique_id",
        "name",
        "description",
        "tactics",
        "url",
        "platforms",
    ],
    "additionalProperties": False,
}

AGENT_TYPE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "agent_capabilities": {
            "type": "object",
            "patternProperties": {
                "(.*?)": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "options": {"type": "object"},
                        "requires_admin": {"type": "boolean"},
                        "supported_oses": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "authors": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "mitre_attack_techniques": {
                            "type": "array",
                            "items": MITRE_ATTACK_TECHNIQUE_JSON_SCHEMA,
                        },
                        "validating_function": {"type": ["string", "null"]},
                    },
                    "required": [
                        "name",
                        "description",
                        "options",
                        "requires_admin",
                        "supported_oses",
                        "authors",
                        "mitre_attack_techniques",
                        "validating_function",
                    ],
                    "additionalProperties": False,
                },
            },
        },
    },
    "required": [
        "name",
        "agent_capabilities",
    ],
    "additionalProperties": False,
}

LISTENER_TYPE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "registered_compatible_agent_types": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["name", "registered_compatible_agent_types"],
    "additionalProperties": False,
}

# Read-time references, mirroring listener_and_agent_reference_models. The live ones
# embed the full type descriptor because the referenced object is guaranteed to exist
# while the reference is built; the persistent one records the agent type by name only,
# since a descriptor written to disk would go stale.
LIVE_AGENT_REFERENCE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "agent_type": AGENT_TYPE_JSON_SCHEMA,
    },
    "required": ["agent_id", "name", "agent_type"],
}
PERSISTENT_AGENT_REFERENCE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "agent_type": {"type": "string"},
    },
    "required": ["agent_id", "name", "agent_type"],
}
LISTENER_REFERENCE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "listener_id": {"type": "string"},
        "name": {"type": "string"},
        "listener_type": LISTENER_TYPE_JSON_SCHEMA,
    },
    "required": ["listener_id", "name", "listener_type"],
}


def repository_resource_json_schema(data_json_schema: dict) -> dict:
    # Artifacts, assets and payloads are all repository resources sharing this
    # envelope exactly, differing only in the `data` each carries.
    return {
        "type": "object",
        "properties": {
            "resource_id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "size": {"type": ["integer", "null"]},
            "exists_on_disk": {"type": "boolean"},
            "datetime_created": {"type": "string"},
            "datetime_modified": {"type": "string"},
            "md5_checksum": {"type": ["string", "null"]},
            "is_directory": {"type": "boolean"},
            "data": data_json_schema,
        },
        "required": [
            "resource_id",
            "name",
            "description",
            "size",
            "exists_on_disk",
            "datetime_created",
            "datetime_modified",
            "md5_checksum",
            "is_directory",
            "data",
        ],
    }


# --- /api/agent-templates -------------------------------------------------------------

AGENT_TEMPLATE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "compatible_framework_version": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "agent_template_id": {"type": "string"},
        "agent_type": AGENT_TYPE_JSON_SCHEMA,
        "compatible_listener_types": {
            "type": "array",
            "items": {"type": "string"},
        },
        "options": {"type": "object"},
        "validating_function": {"type": ["string", "null"]},
    },
    "required": [
        "label",
        "name",
        "description",
        "version",
        "compatible_framework_version",
        "authors",
        "agent_template_id",
        "agent_type",
        "compatible_listener_types",
        "options",
        "validating_function",
    ],
    "additionalProperties": False,
}
ALL_AGENT_TEMPLATES_JSON_SCHEMA = array_of(AGENT_TEMPLATE_JSON_SCHEMA)

AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_TEMPLATE_NOT_FOUND_ERROR"
)
AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_TEMPLATE_OPTION_NOT_FOUND_ERROR"
)
AGENT_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR"
)


# --- /api/agent-generators ------------------------------------------------------------

AGENT_GENERATOR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_generator_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "status": STATUS_JSON_SCHEMA,
        "event_log": EVENT_LOG_JSON_SCHEMA,
        "agent_type": AGENT_TYPE_JSON_SCHEMA,
        "creating_agent_template": {
            "type": "object",
            "properties": {
                "agent_template_id": {"type": "string"},
                "label": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["agent_template_id", "label", "name"],
        },
        "datetime_created": {"type": "string"},
        "parameters": {"type": "object"},
        "agent_generator_build_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    # "ignore_failure": {"type": "boolean"},
                    "datetime_started": {"type": ["string", "null"]},
                    "datetime_stopped": {"type": ["string", "null"]},
                    "time_elapsed_in_seconds": {"type": ["number", "null"]},
                    "status": STATUS_JSON_SCHEMA,
                },
                "required": [
                    "name",
                    "description",
                    # "ignore_failure",
                    "datetime_started",
                    "datetime_stopped",
                    "time_elapsed_in_seconds",
                    "status",
                ],
                "additionalProperties": False,
            },
        },
        "compatible_listener_types": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "agent_generator_id",
        "name",
        "description",
        "status",
        "event_log",
        "creating_agent_template",
        "datetime_created",
        "parameters",
        "agent_generator_build_steps",
        "agent_type",
        "compatible_listener_types",
    ],
    "additionalProperties": False,
}
ALL_AGENT_GENERATORS_JSON_SCHEMA = array_of(AGENT_GENERATOR_JSON_SCHEMA)

AGENT_GENERATOR_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_GENERATOR_NOT_FOUND_ERROR"
)
AGENT_GENERATOR_ALREADY_RUNNING_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_GENERATOR_ALREADY_RUNNING_ERROR"
)
AGENT_GENERATOR_NOT_RUNNING_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_GENERATOR_NOT_RUNNING_ERROR"
)
INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR_JSON_SCHEMA = error_json_schema(
    "INVALID_AGENT_GENERATOR_PARAMETER_NAME_ERROR"
)
INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR_JSON_SCHEMA = error_json_schema(
    "INVALID_AGENT_GENERATOR_PARAMETER_VALUE_ERROR"
)


# --- /api/listener-templates ----------------------------------------------------------

LISTENER_TEMPLATE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "version": {"type": "string"},
        "compatible_framework_version": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "listener_template_id": {"type": "string"},
        "listener_type": LISTENER_TYPE_JSON_SCHEMA,
        "options": {"type": "object"},
        "validating_function": {"type": ["string", "null"]},
    },
    "required": [
        "label",
        "name",
        "description",
        "version",
        "compatible_framework_version",
        "authors",
        "listener_template_id",
        "listener_type",
        "options",
        "validating_function",
    ],
    "additionalProperties": False,
}
ALL_LISTENER_TEMPLATES_JSON_SCHEMA = array_of(LISTENER_TEMPLATE_JSON_SCHEMA)

LISTENER_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "LISTENER_TEMPLATE_NOT_FOUND_ERROR"
)
LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "LISTENER_TEMPLATE_OPTION_NOT_FOUND_ERROR"
)
# The two option errors below document structure in `detail`, so they do not take the
# factory's untyped default.
MISSING_REQUIRED_OPTION_ERROR_JSON_SCHEMA = error_json_schema(
    "MISSING_REQUIRED_LISTENER_TEMPLATE_OPTION_ERROR",
    detail_json_schema={
        "type": "object",
        "properties": {
            "listener_template_str": {"type": "string"},
            "option_str": {"type": "string"},
        },
        "required": ["listener_template_str", "option_str"],
    },
)
OPTION_VALUE_ERROR_JSON_SCHEMA = error_json_schema(
    "LISTENER_TEMPLATE_OPTION_VALUE_VALIDATION_ERROR",
    detail_json_schema={
        "type": "object",
        "properties": {
            "option_str": {"type": "string"},
            "option_value": {},
            "error_message": {"type": "string"},
        },
        "required": ["option_str", "option_value", "error_message"],
    },
)


# --- /api/listeners -------------------------------------------------------------------

LISTENER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "listener_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "endpoint": {"type": "string"},
        "listener_type": LISTENER_TYPE_JSON_SCHEMA,
        "parameters": {"type": "object"},
        "status": STATUS_JSON_SCHEMA,
        "event_log": EVENT_LOG_JSON_SCHEMA,
        "datetime_created": {"type": "string"},
        "connected_agents": array_of(LIVE_AGENT_REFERENCE_JSON_SCHEMA),
        "creating_listener_template": {"type": "object"},
    },
    "required": [
        "listener_id",
        "name",
        "description",
        "endpoint",
        "listener_type",
        "parameters",
        "status",
        "event_log",
        "datetime_created",
        "connected_agents",
        "creating_listener_template",
    ],
}
ALL_LISTENERS_JSON_SCHEMA = array_of(LISTENER_JSON_SCHEMA)

LISTENER_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema("LISTENER_NOT_FOUND_ERROR")
LISTENER_ALREADY_RUNNING_ERROR_JSON_SCHEMA = error_json_schema(
    "LISTENER_ALREADY_RUNNING_ERROR"
)
LISTENER_NOT_RUNNING_ERROR_JSON_SCHEMA = error_json_schema("LISTENER_NOT_RUNNING_ERROR")
INVALID_LISTENER_PARAMETER_NAME_ERROR_JSON_SCHEMA = error_json_schema(
    "INVALID_LISTENER_PARAMETER_NAME_ERROR"
)
INVALID_LISTENER_PARAMETER_VALUE_ERROR_JSON_SCHEMA = error_json_schema(
    "INVALID_LISTENER_PARAMETER_VALUE_ERROR"
)


# --- /api/agents ----------------------------------------------------------------------

# The full resolved agent, matching AgentModel. This is also what `resolved_agent` holds
# when an artifact's persistent `agent` reference resolves at read-time.
AGENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "endpoint": {"type": "string"},
        "agent_type": AGENT_TYPE_JSON_SCHEMA,
        "user": {"type": ["string", "null"]},
        "is_admin": {"type": ["boolean", "null"]},
        "os": {"type": ["string", "null"]},
        "version": {"type": ["string", "null"]},
        "arch": {"type": ["string", "null"]},
        "pid": {"type": ["integer", "null"]},
        "locale": {"type": ["string", "null"]},
        "remote_ip": {"type": ["string", "null"]},
        "local_ip": {"type": ["string", "null"]},
        "hostname": {"type": ["string", "null"]},
        "datetime_first_checked_in": {"type": "string"},
        "datetime_last_checked_in": {"type": "string"},
        "status": {"type": "string"},
        "connected_listener": {
            "oneOf": [LISTENER_REFERENCE_JSON_SCHEMA, {"type": "null"}],
        },
        "agent_data": {"type": ["object", "null"]},
    },
    "required": [
        "agent_id",
        "name",
        "description",
        "endpoint",
        "agent_type",
        "user",
        "is_admin",
        "os",
        "version",
        "arch",
        "pid",
        "locale",
        "remote_ip",
        "local_ip",
        "hostname",
        "datetime_first_checked_in",
        "datetime_last_checked_in",
        "status",
        "connected_listener",
        "agent_data",
    ],
}
ALL_AGENTS_JSON_SCHEMA = array_of(AGENT_JSON_SCHEMA)

AGENT_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema("AGENT_NOT_FOUND_ERROR")
AGENT_CAPABILITY_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "AGENT_CAPABILITY_NOT_FOUND_ERROR"
)


# --- /api/tasks -----------------------------------------------------------------------

# POST /api/agents/{agent_id}/tasks returns this same model, so tasking an agent and
# reading a task back are asserted against one schema.
TASK_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "agent_id": {"type": "string"},
        "command": {"type": "string"},
        "arguments": {"type": "object"},
        "status": STATUS_JSON_SCHEMA,
        "event_log": EVENT_LOG_JSON_SCHEMA,
        "datetime_created": {"type": "string"},
        "datetime_started": {"type": ["string", "null"]},
        "datetime_completed": {"type": ["string", "null"]},
    },
    "required": [
        "task_id",
        "agent_id",
        "command",
        "arguments",
        "status",
        "event_log",
        "datetime_created",
        "datetime_started",
        "datetime_completed",
    ],
}
ALL_TASKS_JSON_SCHEMA = array_of(TASK_JSON_SCHEMA)

TASK_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema("TASK_NOT_FOUND_ERROR")


# --- /api/artifacts -------------------------------------------------------------------

ARTIFACT_JSON_SCHEMA = repository_resource_json_schema(
    {
        "type": "object",
        "properties": {
            # Persistent point-in-time reference to the producing agent recorded at
            # creation, `None` when the artifact was created without agent attribution.
            "agent": {
                "oneOf": [PERSISTENT_AGENT_REFERENCE_JSON_SCHEMA, {"type": "null"}],
            },
            # Live read-time resolution of `agent`, `None` when the producing agent
            # cannot be resolved.
            "resolved_agent": {
                "oneOf": [AGENT_JSON_SCHEMA, {"type": "null"}],
            },
        },
        "required": ["agent", "resolved_agent"],
    }
)
ALL_ARTIFACTS_JSON_SCHEMA = array_of(ARTIFACT_JSON_SCHEMA)


# --- /api/assets ----------------------------------------------------------------------

ASSET_JSON_SCHEMA = repository_resource_json_schema(
    {
        "type": "object",
        "properties": {
            "user_account": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "role": {"type": "string"},
                },
                "required": ["username", "role"],
            },
            "resolved_user_account": {
                "type": ["object", "null"],
                "properties": {
                    "user_account_id": {"type": "string"},
                    "username": {"type": "string"},
                    "role": {"type": "string"},
                },
            },
        },
        "required": ["user_account", "resolved_user_account"],
    }
)
ALL_ASSETS_JSON_SCHEMA = array_of(ASSET_JSON_SCHEMA)

# Shared by every repository resource endpoint, not just assets.
RESOURCE_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema("RESOURCE_NOT_FOUND_ERROR")
DIRECTORY_ARCHIVE_FORMAT_NOT_SPECIFIED_ERROR_JSON_SCHEMA = error_json_schema(
    "REPOSITORY_DIRECTORY_ARCHIVE_FILE_FORMAT_NOT_SPECIFIED_ERROR"
)
DIRECTORY_FILE_NOT_ARCHIVE_ERROR_JSON_SCHEMA = error_json_schema(
    "REPOSITORY_DIRECTORY_FILE_NOT_ARCHIVE_FILE_ERROR"
)


# --- /api/payloads --------------------------------------------------------------------

PAYLOAD_JSON_SCHEMA = repository_resource_json_schema(
    {
        "type": "object",
        "properties": {
            # Persistent point-in-time reference stored on disk. Only `label` and `name`
            # are persisted (the id can vary on restart).
            "agent_template": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "name": {"type": "string"},
                },
                "required": ["label", "name"],
            },
            "build_parameters": {"type": "object"},
            "payload_data": {"type": "object"},
            # Live read-time resolution of `agent_template`, `None` when the template
            # cannot be resolved.
            "resolved_agent_template": {
                "oneOf": [AGENT_TEMPLATE_JSON_SCHEMA, {"type": "null"}],
            },
        },
        "required": [
            "agent_template",
            "build_parameters",
            "payload_data",
            "resolved_agent_template",
        ],
    }
)
ALL_PAYLOADS_JSON_SCHEMA = array_of(PAYLOAD_JSON_SCHEMA)


# --- /api/users and /api/user-accounts ------------------------------------------------

USER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string"},
        "display_name": {"type": "string"},
        "username": {"type": "string"},
        "user_account": {
            "type": "object",
            "properties": {
                "user_account_id": {"type": "string"},
                "username": {"type": "string"},
            },
            "required": ["user_account_id", "username"],
            "additionalProperties": False,
        },
        "role": {"type": "string"},
        "datetime_connected": {"type": "string"},
        "datetime_last_active": {"type": "string"},
    },
    "required": [
        "user_id",
        "display_name",
        "username",
        "role",
        "user_account",
        "datetime_connected",
        "datetime_last_active",
    ],
    "additionalProperties": False,
}
ALL_USERS_JSON_SCHEMA = array_of(USER_JSON_SCHEMA)

USER_ACCOUNT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "user_account_id": {"type": "string"},
        "username": {"type": "string"},
        "password": {"type": "string"},
        "role": {"type": "string", "enum": ["ADMIN", "OPERATOR", "SPECTATOR"]},
    },
    "required": ["user_account_id", "username", "password", "role"],
    "additionalProperties": False,
}
ALL_USER_ACCOUNTS_JSON_SCHEMA = array_of(USER_ACCOUNT_JSON_SCHEMA)

USER_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema("USER_NOT_FOUND_ERROR")
USER_ACCOUNT_NOT_FOUND_ERROR_JSON_SCHEMA = error_json_schema(
    "USER_ACCOUNT_NOT_FOUND_ERROR"
)
USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR_JSON_SCHEMA = error_json_schema(
    "USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR"
)
USER_ACCOUNT_AUTHENTICATION_ERROR_JSON_SCHEMA = error_json_schema(
    "USER_ACCOUNT_AUTHENTICATION_ERROR"
)
EMPTY_USER_ACCOUNT_USERNAME_ERROR_JSON_SCHEMA = error_json_schema(
    "EMPTY_USER_ACCOUNT_USERNAME_ERROR"
)
EMPTY_USER_ACCOUNT_PASSWORD_ERROR_JSON_SCHEMA = error_json_schema(
    "EMPTY_USER_ACCOUNT_PASSWORD_ERROR"
)


# --- /api/login and the events API handshake ------------------------------------------

JSON_WEB_TOKEN_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {"type": "string"},
        "token_type": {"type": "string"},
    },
    "required": ["access_token", "token_type"],
}

WEBSOCKET_TICKET_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "ticket": {"type": "string"},
        "time_to_live_seconds": {"type": "integer"},
    },
    "required": ["ticket", "time_to_live_seconds"],
    "additionalProperties": False,
}


# --- /api/server ----------------------------------------------------------------------

SERVER_VERSION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "codename": {"type": "string"},
        "datetime_released": {"type": ["string", "null"]},
    },
    "required": ["version", "codename", "datetime_released"],
    "additionalProperties": False,
}

SERVER_CONFIG_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "local_host": {"type": "string"},
        "local_port": {"type": "integer"},
        "remote_host_whitelist": {"type": "array", "items": {"type": "string"}},
        "remote_host_blacklist": {"type": "array", "items": {"type": "string"}},
        "server_header": {"type": ["string", "null"]},
        "ssl_certfile": {"type": ["string", "null"]},
        "ssl_keyfile": {"type": ["string", "null"]},
    },
    "required": [
        "local_host",
        "local_port",
        "remote_host_whitelist",
        "remote_host_blacklist",
        "server_header",
        "ssl_certfile",
        "ssl_keyfile",
    ],
    "additionalProperties": False,
}
