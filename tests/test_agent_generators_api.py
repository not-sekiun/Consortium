AGENT_GENERATOR_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_generator_id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "status": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "error": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["type", "message"],
                        },
                    ],
                },
            },
            "required": ["state", "error"],
        },
        "agent_type": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "compatible_listener_type_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "agent_type_id": {"type": "string"},
            },
            "required": ["name", "compatible_listener_type_ids", "agent_type_id"],
        },
        "options": {"type": "object"},
    },
}
