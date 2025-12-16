from consortium.framework.options import SingleValueOption

jit = SingleValueOption(
    name="sleep_time_jitter",
    description=(
        "The percentage of the duration of the sleep time to randomly vary "
        "sleeping by expressed as a decimal. A random value between 0 and "
        "the value of the jitter percentage option is chosen to randomly "
        "increase or decrease the duration of the sleep time by."
    ),
    default_value=0.5,
    value_type=float,
    greater_than_or_equal_to=0.0,
)
jit.validate_value(1)

# import sys
# import threading
#
# from loguru import logger
#
# # Thread-local storage to track the current indentation level per thread
# _thread_local = threading.local()
# _thread_local.indent = 0
# _thread_local.is_end_branch = False
#
# # --- Custom Log Formatting Characters ---
# VERTICAL = "│   "  # Vertical line to maintain context
# BRANCH_MID = "├── "  # Mid-branch character
# BRANCH_END = "└── "  # End-branch character
#
#
# class IndentedLogger:
#     """
#     A context manager for creating indented, hierarchical log blocks.
#     """
#
#     def __init__(
#         self,
#         message: str,
#         level: str = "INFO",
#         logger_name: str | None = None,
#         maintain_context_level: int = 0,
#     ):
#         self.message = message
#         self.level = level
#         self.logger_name = logger_name
#         self.original_indent = _thread_local.indent
#         self.maintain_context_level = maintain_context_level
#
#     def __enter__(self):
#         # 1. Calculate the prefix string based on current indent level
#         prefix = self._get_prefix(is_start=True)
#
#         # 2. Log the starting message with the calculated prefix
#         log_func = logger.bind(indent_prefix=prefix)
#         if self.logger_name:
#             log_func = log_func.bind(name=self.logger_name)
#
#         log_func.log(self.level, self.message)
#
#         # 3. Increase indentation level for children logs
#         _thread_local.indent += 1
#
#         self.maintain_context_level = (
#             self.maintain_context_level
#             if self.maintain_context_level < _thread_local.indent
#             else _thread_local.indent - 1
#         )
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         # 1. Decrease indentation level back to where we started
#         _thread_local.indent -= 1
#
#         # 2. Reset the branch state if needed (optional cleanup)
#         _thread_local.is_end_branch = False
#
#     def branch(self, message: str, level: str = "INFO", is_end: bool = False):
#         """Logs a single branch line within the current context."""
#
#         # 1. Calculate the prefix string
#         prefix = self._get_prefix(is_end=is_end)
#
#         # 2. Log the message
#         log_func = logger.bind(indent_prefix=prefix)
#         if self.logger_name:
#             log_func = log_func.bind(name=self.logger_name)
#
#         log_func.log(level, message)
#
#         # 3. If this is the final branch, set the thread-local state
#         if is_end:
#             _thread_local.is_end_branch = True
#
#     def _get_prefix(self, is_start: bool = False, is_end: bool = False) -> str:
#         """Calculates the full indentation prefix string."""
#
#         # Base prefix calculation
#         prefix = ""
#         current_indent = _thread_local.indent
#
#         for i in range(current_indent - 1):
#             if i < (current_indent - self.maintain_context_level - 1):
#                 # Maintain context level with spaces
#                 prefix += "    "
#             else:
#                 # For all preceding levels, use the vertical line or empty space
#                 prefix += VERTICAL
#
#         # Append the correct branch character if this isn't the outer start
#         if not is_start or current_indent > 0:
#             if is_end:
#                 prefix += BRANCH_END
#             elif not is_start:
#                 prefix += BRANCH_MID
#             elif current_indent > 0:
#                 prefix += BRANCH_MID  # Should only happen in nested context
#
#         return prefix
#
#
# # --- Loguru Setup ---
# # You MUST modify your logger format to include the placeholder.
#
# # 1. Define the colored name based on your choice (e.g., Bold Cyan for Framework Services)
# SERVICE_NAME_COLOR = "<bold><cyan>"
#
# LOG_FORMAT = (
#     "<dim><white>{time:YYYY-MM-DDTHH:mm:ss.SSSZ}</></> | "
#     "{level:<8} | "
#     # Inject the bound variable {extra[indent_prefix]} AND the colored name {name}
#     f"{SERVICE_NAME_COLOR}{{name:<30}}</></> | "
#     "<level>{extra[indent_prefix]}</level>"  # THIS IS WHERE THE MAGIC HAPPENS
#     "<level>{message}</level>"
# )
#
# # You need to ensure the logger is configured with the new format
# logger.remove()
# logger.add(sys.stdout, format=LOG_FORMAT)
#
# # --- Example Usage ---
# SERVICE_NAME = "Listener Profiles Service"
#
# # --- Main Block Start ---
#
# with IndentedLogger(
#     message="Loading framework listener profiles...",
#     level="INFO",
#     logger_name=SERVICE_NAME,
#     maintain_context_level=0,
# ) as loader:
#     loader.branch(
#         message="Loaded listener profile: 'HTTP Listener' (d011ee9e...)",
#         level="SUCCESS",
#     )
#     loader.branch(
#         message="Loaded listener profile: 'Reverse TCP Listener' (28e96a99...)",
#         level="SUCCESS",
#     )
#     with IndentedLogger(
#         message="Loading framework listener profiles...",
#         level="INFO",
#         logger_name=SERVICE_NAME,
#         maintain_context_level=1,
#     ) as loader_2:
#         loader_2.branch(
#             message="Loaded listener profile: 'HTTP Listener' (d011ee9e...)",
#             level="SUCCESS",
#         )
#         loader_2.branch(
#             message="Loaded listener profile: 'Reverse TCP Listener' (28e96a99...)",
#             level="SUCCESS",
#         )
#         loader_2.branch(
#             message="Loaded 2 listener profiles from '...listeners'.",
#             level="INFO",
#             is_end=True,  # Signals the final item in this block
#         )
#     loader.branch(
#         message="Loaded 2 listener profiles from '...listeners'.",
#         level="INFO",
#         is_end=True,  # Signals the final item in this block
#     )
#
# # Log after the block exits (indentation reverts automatically)
# logger.info("Server initialization complete.")
