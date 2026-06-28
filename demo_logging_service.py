"""
Demo: LoggingService

Run with:  uv run python demo_logging_service.py
"""

import io
import sys

from loguru import logger

from consortium.server.models.logging_models import LoggerType, LoggingConfigModel
from consortium.server.services.logging_service import LoggingService


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# 1. Bootstrap via configure_default_logging (mirrors server startup)
# ---------------------------------------------------------------------------
section("1. Configure default logging (stdout only)")

service = LoggingService()

config = LoggingConfigModel(
    level="DEBUG",
    log_file=None,
    rotation=None,
    retention=None,
    colorize=True,
)
service.configure_default_logging(config)

app_logger = logger.bind(logger_name="Demo App", logger_type=LoggerType.SERVER_LOGGER)
app_logger.debug("Server started - debug message")
app_logger.info("Server started - info message")
app_logger.success("Server started - success message")
app_logger.warning("Server started - warning message")

# ---------------------------------------------------------------------------
# 2. Inspect registered sinks
# ---------------------------------------------------------------------------
section("2. Inspect registered sinks")

for info in service.get_all_sinks():
    print(
        f"  label={info.label!r:12}  level={info.level:<8}  "
        f"server_default={info.is_server_default}  handler_id={info.handler_id}"
    )

# ---------------------------------------------------------------------------
# 3. Add a custom callable sink (e.g. forward to a buffer / remote provider)
# ---------------------------------------------------------------------------
section("3. Add a callable sink (captures into a StringIO buffer)")

buffer = io.StringIO()

service.add_sink(
    sink=buffer,
    level="WARNING",
    label="buffer",
    format="{time:HH:mm:ss} {level:<8} {message}",
    colorize=False,
)

app_logger.debug("This won't appear in the buffer (below WARNING)")
app_logger.warning("This WILL appear in the buffer")
app_logger.error("This WILL appear in the buffer too")

print("  Buffer contents:")
for line in buffer.getvalue().splitlines():
    print(f"    {line}")

# ---------------------------------------------------------------------------
# 4. Add an stderr sink marked as non-server-default (e.g. added by a plugin)
# ---------------------------------------------------------------------------
section("4. Plugin adds an stderr sink (not a server default)")

service.add_sink(
    sink=sys.stderr,
    level="ERROR",
    label="plugin_stderr",
    format="{time:HH:mm:ss} PLUGIN [{level}] {message}",
    colorize=False,
    is_server_default=False,
)

print("  Registered sinks after plugin add:")
for info in service.get_all_sinks():
    print(f"    label={info.label!r:16}  server_default={info.is_server_default}")

# ---------------------------------------------------------------------------
# 5. Modify a sink at runtime (e.g. plugin raises the stdout threshold)
# ---------------------------------------------------------------------------
section("5. Modify stdout level to ERROR at runtime")

print(
    "  Before modify - stdout level:",
    next(i for i in service.get_all_sinks() if i.label == "stdout").level,
)
service.modify_sink("stdout", level="ERROR")
print(
    "  After modify  - stdout level:",
    next(i for i in service.get_all_sinks() if i.label == "stdout").level,
)

app_logger.info("This info message is now suppressed on stdout")
app_logger.error("This error message still appears on stdout")

# ---------------------------------------------------------------------------
# 6. Redirect all non-server-default sinks to a different target
# ---------------------------------------------------------------------------
section("6. Redirect plugin sinks to a central buffer")

central = io.StringIO()

for info in service.get_all_sinks():
    if not info.is_server_default:
        service.modify_sink(info.label, sink=central, colorize=False)
        print(f"  Redirected {info.label!r} -> central buffer")

app_logger.error("Error routed through central buffer by plugin sink")

print("  Central buffer contents:")
for line in central.getvalue().splitlines():
    print(f"    {line}")

# ---------------------------------------------------------------------------
# 7. Remove a sink
# ---------------------------------------------------------------------------
section("7. Remove the plugin stderr sink")

service.remove_sink("plugin_stderr")
labels = [i.label for i in service.get_all_sinks()]
print(f"  Remaining sinks: {labels}")

# ---------------------------------------------------------------------------
# 8. Restore stdout to DEBUG and reset state for a clean finish
# ---------------------------------------------------------------------------
section("8. Restore stdout to DEBUG")

service.modify_sink("stdout", level="DEBUG")
app_logger.debug("Back to DEBUG - all done")
