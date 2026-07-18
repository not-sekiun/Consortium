from consortium.client.models.logging_models import LoggerType


def log_formatter(record) -> str:
    logger_type_to_color_str_map = {
        LoggerType.CLIENT_REST_API_LOGGER: "<bold><blue>",
        LoggerType.CLIENT_WEBSOCKETS_EVENTS_API_LOGGER: "<bold><blue>",
        LoggerType.CLIENT_INTERPRETER_LOGGER: "<bold><red>",
        LoggerType.CLIENT_SESSIONS_SERVICE: "<bold><green>",
    }

    logger_type = record["extra"].get("logger_type")

    if not logger_type:
        color = "<dim><white>"
    else:
        color = logger_type_to_color_str_map.get(logger_type, "<dim><white>")

    logger_name = record["extra"].get("logger_name") or record["name"]

    # logger_name is resolved here rather than via {extra[logger_name]} in the
    # format string to avoid a KeyError when logging without a bound logger_name.
    # Can't use f-string here because of the loguru syntax. Also, we need to add
    # the newline character at the end of the string for formatter functions.
    return (
        "<dim><white>{time:YYYY-MM-DDTHH:mm:ss.SSSZ}</></> <level>{level:<8}</> "
        + color
        + logger_name
        + "</></>: {message}\n{exception}"
    )
