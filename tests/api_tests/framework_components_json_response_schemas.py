# Generic JSON schemas for framework components
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
                        "detail": {},
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

# JSON schemas for the /api/agent-templates endpoints
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
