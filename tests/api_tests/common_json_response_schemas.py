# Standard HTTP error JSON response schemas for all api endpoints.
INVALID_UUID_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["INVALID_UUID_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
FORBIDDEN_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["FORBIDDEN_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
# TODO: Add tests for  401 Unauthorized, 404 Not Found, 405 Method Not Allowed, and 422
#  Unprocessable Entity.
NOT_FOUND_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["NOT_FOUND_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
METHOD_NOT_ALLOWED_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["METHOD_NOT_ALLOWED_ERROR"]},
                "message": {"type": "string"},
                "detail": {},
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}
UNPROCESSABLE_ENTITY_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["UNPROCESSABLE_ENTITY_ERROR"]},
                "message": {"type": "string"},
                "detail": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "loc": {"type": "array", "items": {"type": "string"}},
                            "msg": {"type": "string"},
                            "type": {"type": "string"},
                        },
                        "required": ["loc", "msg", "type"],
                    },
                },
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


# Standard operation acknowledgement JSON response schemas for all api endpoints
SUCCESS_JSON_SCHEMA = {
    "type": "object",
    "properties": {"success": {"type": "boolean", "enum": [True]}},
    "required": ["success"],
}
ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "enum": [False]},
        "error": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["type", "message"],
        },
    },
    "required": ["success", "error"],
}
