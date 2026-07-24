# Standard HTTP error JSON response schemas for all api endpoints.
INVALID_UUID_ERROR_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "enum": ["INVALID_UUID_ERROR"]},
                "message": {"type": "string"},
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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
                "detail": {"type": ["object", "null"]},
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
                    "type": "object",
                    "properties": {
                        "validation_errors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                # Typed according to pydantic v2, documentation from
                                # https://pydantic.dev/docs/validation/latest/errors/errors/
                                # with documentation of the ErrorDetail object here
                                # https://pydantic.dev/docs/validation/latest/api/pydantic-core/pydantic_core/#pydantic_core.ErrorDetails
                                "properties": {
                                    "ctx": {},
                                    "loc": {
                                        "type": "array",
                                        # first location is the field, subsequent ones
                                        # are subfields/indices
                                        "items": {"type": ["string", "integer"]},
                                    },
                                    "input": {},
                                    "msg": {"type": "string"},
                                    "type": {"type": "string"},
                                    "url": {"type": "string"},
                                },
                                "additionalProperties": False,
                                "required": ["type", "loc", "msg", "input"],
                            },
                        }
                    },
                    "required": ["validation_errors"],
                },
            },
            "required": ["code", "message", "detail"],
        },
    },
    "required": ["error"],
}


# Standard error JSON response schemas for all api endpoints
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
