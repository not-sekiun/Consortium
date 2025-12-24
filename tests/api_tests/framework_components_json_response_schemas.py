# Generic JSON schemas for framework components
STATUS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "error": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "detail": {},
                    },
                    "required": ["code", "message", "detail"],
                    "additionalProperties": False,
                },
            ],
        },
    },
    "required": ["status", "error"],
    "additionalProperties": False,
}

# JSON schemas for the /api/agent-templates endpoints
AGENT_TYPE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_type_id": {"type": "string"},
        "name": {"type": "string"},
        "compatible_listener_types": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "listener_type_id": {"type": "string"},
                    "name": {"type": "string"},
                },
                "required": ["listener_type_id", "name"],
                "additionalProperties": False,
            },
        },
        "agent_capabilities": {
            "type": "object",
            "patternProperties": {
                "(.*?)": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        # TODO: Include each option type's JSON schema in the
                        #  main JSON schema.
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
                    },
                    "required": [
                        "name",
                        "description",
                        "options",
                        "requires_admin",
                        "supported_oses",
                        "authors",
                    ],
                    "additionalProperties": False,
                },
            },
        },
    },
    "required": [
        "agent_type_id",
        "name",
        "compatible_listener_types",
        "agent_capabilities",
    ],
    "additionalProperties": False,
}
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
        "options",
        "validating_function",
    ],
    "additionalProperties": False,
}
ALL_AGENT_TEMPLATES_JSON_SCHEMA = {
    "type": "array",
    "items": AGENT_TEMPLATE_JSON_SCHEMA,
}
AGENT_TEMPLATE_NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "enum": ["AGENT_TEMPLATE_NOT_FOUND_ERROR"],
                },
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}

# JSON schemas for the /api/agent-generators endpoints
AGENT_GENERATOR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_generator_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "status": STATUS_JSON_SCHEMA,
        "agent_type": AGENT_TYPE_JSON_SCHEMA,
        "creating_agent_template": {
            "type": "object",
            "properties": {
                "agent_template_id": {"type": "string"},
                "name": {"type": "string"},
            },
        },
        "datetime_created": {"type": "string"},
        "parameters": {"type": "object"},
        "agent_generator_build_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agent_generator_build_step_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "ignore_failure": {"type": "boolean"},
                    "datetime_started": {"type": ["string", "null"]},
                    "datetime_stopped": {"type": ["string", "null"]},
                    "time_elapsed_in_seconds": {"type": ["number", "null"]},
                    "status": STATUS_JSON_SCHEMA,
                },
                "required": [
                    "agent_generator_build_step_id",
                    "name",
                    "description",
                    "ignore_failure",
                    "datetime_started",
                    "datetime_stopped",
                    "time_elapsed_in_seconds",
                    "status",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "agent_generator_id",
        "name",
        "description",
        "status",
        "creating_agent_template",
        "datetime_created",
        "parameters",
        "agent_generator_build_steps",
        "agent_type",
    ],
    "additionalProperties": False,
}
