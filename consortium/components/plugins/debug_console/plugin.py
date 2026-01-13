import random
import string
import traceback

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import StdoutProxy, patch_stdout
from prompt_toolkit.styles import Style
from rich.pretty import pprint

from consortium.framework.plugins import BasePlugin
from consortium.server.server_logging import log_formatter


class _ServicesMethodsCompleter(Completer):
    def __init__(
        self,
        services_methods_completion_dict: dict[str, dict[str, None] | None],
        services,
    ):
        self._services_methods_completions_dict = services_methods_completion_dict
        self._services = services

    # Checks to see if a key list exists in a dictionary. The key list is a list of
    # keys that are traversed recursively in the dictionary. So if the key list is
    # ['a', 'b', 'c'] then the function will check if the dictionary has a key 'a'
    # which has a key 'b' which has a key 'c' and then for that key 'c' check all valid
    # completions for the provided completion substring.
    def _return_valid_completions_in_services_methods_completions_dict(
        self,
        key_list: list[str],
        string_to_complete: str,
    ) -> tuple[bool, list[str | tuple[str, bool]]]:
        current_dict = self._services_methods_completions_dict
        for key in key_list:
            if key not in current_dict:
                # Key list is not even valid so return an empty list. This means that no
                # such chain of namespaces exists.
                return False, []
            current_dict = current_dict[key]

        # Key list is valid but there are no more completions possible. This means that
        # we are at the end of the chain of namespaces.
        if current_dict is None:
            return False, []

        # Key list is valid and there are more completions possible. This means that we
        # are not at the end of the chain of namespaces so we return the next valid
        # completions if there are any.
        valid_completions = []
        for key in current_dict:
            if key.startswith(string_to_complete):
                valid_completions.append(key)

        # When we are completing members, the key list will have exactly one element.
        # This means we are now completing attrs and methods. We return a tuple
        # indicating if the member is callable or not along with a bool indicating
        # whether we are completing for members of a service or services themselves.
        if len(key_list) == 1:
            return True, [
                (
                    member,
                    callable(getattr(vars(self._services)[key_list[0]], member)),
                )
                for member in valid_completions
            ]
        return False, valid_completions

    def get_completions(self, document, complete_event):
        space_separated_text = document.text.split()
        if document.text.endswith(" "):
            latest_space_separated_word = ""
        elif document.text == "":
            latest_space_separated_word = ""
        else:
            latest_space_separated_word = space_separated_text[-1]

        if "." in latest_space_separated_word:
            dot_separated_words = latest_space_separated_word.split(".")
            is_completing_members, completions = (
                self._return_valid_completions_in_services_methods_completions_dict(
                    key_list=dot_separated_words[:-1],
                    string_to_complete=dot_separated_words[-1],
                )
            )
            for completion_tuple in completions:
                if is_completing_members:
                    if completion_tuple[1]:
                        display = "<a bg='ansiblue' fg='ansiwhite'> meth </a>"
                    else:
                        display = "<a bg='ansigreen' fg='ansiwhite'> attr </a>"
                    yield Completion(
                        completion_tuple[0],
                        start_position=-len(dot_separated_words[-1]),
                        display=HTML(f"{display} {completion_tuple[0]}"),
                    )
                else:
                    yield Completion(
                        completion_tuple[0],
                        start_position=-len(dot_separated_words[-1]),
                    )
        else:
            for service in self._services_methods_completions_dict:
                if service.startswith(latest_space_separated_word.lstrip()):
                    yield Completion(
                        service,
                        start_position=-len(latest_space_separated_word.lstrip()),
                    )


def _print_custom_formatted_exception_message(
    exc: Exception,
    temporary_function_identifier: str,
) -> None:
    stack_summary = traceback.extract_tb(exc.__traceback__)
    innermost_frame = stack_summary[-1]
    # This indicates the error occurred at the top most module level. But since the
    # code runs in a temporary function implicitly, we need to change the name.
    if innermost_frame.name == temporary_function_identifier:
        innermost_frame.name = "<module>"
    print("Traceback (most recent call last):")
    print(
        f'  File "{innermost_frame.filename}", line {innermost_frame.lineno}, in {innermost_frame.name}'
    )
    print(f"{exc.__class__.__name__}: {exc}")


class Plugin(BasePlugin):
    label = "consortium.plugins.debug_console_plugin"
    name = "Debug Interpreter Plugin"
    description = (
        "A plugin that provides an interactive debug interpreter for running arbitrary "
        "Python code in the context of the framework. Access to all of the "
        "frameworks services is given in the environment."
    )
    version = "0.1.0"
    compatible_framework_version = ">=0.1.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_started(self) -> None:
        self.logger.info(
            "Debug interpreter is now running. All framework services are available in "
            "the current environment. You can tab complete services along with their "
            "API methods.",
        )

        # FIXME: Consider providing a dedicated logger service to interact with logging,
        #  might be useful to send logs remotely or do custom things with them. Log
        #  index 2 is always stdout due to how server_logging sets up the loggers.
        #  This is brittle. fix it.
        # Remove the current stdout logger and patch it with `StdoutProxy` to prevent
        # loguru from messing with prompt_toolkit's stdout handling. Retain the current
        # log configuration.
        logger.remove(2)
        # FIXME: Weird bug: logger.remove(2) removes the stdout logger so when logger.add
        #  errors out we see no output.
        logging_config = self.services.logging_service.logging_config
        logger.add(
            StdoutProxy(raw=True),
            format=log_formatter,
            level=logging_config.level,
            colorize=logging_config.colorize,
        )

    async def on_running(self) -> None:
        # Construct completions dict. The keys are the symbols of every service in
        # `self.services`. The values are dictionaries with keys that are the
        # public methods and attributes of each service and whose values are `None` to
        # indicate termination of auto-completion.
        services_methods_completions_dict = {
            service_name: {
                member: None for member in dir(service) if not member.startswith("_")
            }
            for service_name, service in vars(self.services).items()
        }
        services_methods_completions_dict["exit"] = None
        style = Style.from_dict(
            {
                # User input (default text).
                "": "ansiwhite bold",
                # Prompt.
                "surrounding_prompt": "ansiwhite bold",
                "debug": "ansiwhite bold bg:ansired bold",
            },
        )
        prompt = [
            ("class:surrounding_prompt", "Consortium ("),
            ("class:debug", "Debug"),
            ("class:surrounding_prompt", ") > "),
        ]
        history = InMemoryHistory()
        # Passing in a `bottom_toolbar` in `prompt_async` will mutate the
        # `PromptSession` object such that every subsequent call has the bottom
        # toolbar. Passing in `None` does not remove the bottom toolbar so we need to
        # have separate `PromptSessions` here
        single_line_input_session = PromptSession(
            completer=_ServicesMethodsCompleter(
                services_methods_completion_dict=services_methods_completions_dict,
                services=self.services,
            ),
            style=style,
            history=history,
        )
        multi_line_input_session = PromptSession(
            completer=_ServicesMethodsCompleter(
                services_methods_completion_dict=services_methods_completions_dict,
                services=self.services,
            ),
            style=style,
            multiline=True,
            history=history,
            bottom_toolbar=HTML(
                "<bold>Press [Meta+Enter] or [Esc] followed by [Enter] "
                "to accept input. Press [Ctrl+C] to cancel input."
                "</bold>",
            ),
        )
        globals_dict = vars(self.services)

        with patch_stdout(raw=True):
            while True:
                try:
                    expression = (
                        await single_line_input_session.prompt_async(
                            prompt,
                            style=style,
                        )
                    ).rstrip(" ")

                    if expression in ("exit", "exit()"):
                        self.logger.success(
                            "Exited the debug interpreter. Use CTRL-C to stop the "
                            "server.",
                        )
                        break
                    elif not expression:
                        continue

                    # Create a temporary function to hold the code block. This allows
                    # inline execution of asynchronous code expressions. At the very
                    # end of execution the temporary function updates the global scope
                    # with its local scope to retain the behavior of the interpreter
                    # instantiating variables because the user is not aware of any
                    # implicit scoping happening in the background.
                    random_identifier = "_" + "".join(
                        [random.choice(string.ascii_letters) for _ in range(8)],
                    )
                    temporary_function = (
                        f"async def {random_identifier}():"
                        + f"\n    _ = {expression}"
                        # If there is an assignment happening as the expression, we
                        # update the global scope with the local scope to retain the
                        # behavior of the interpreter.
                        + "\n    globals().update({key: value for key, value in locals().items() if key != '_'})"
                        + "\n    return _"
                    )
                    try:
                        # Create the temporary function to house asynchronous code.
                        exec(temporary_function, globals_dict)
                        # Evaluate the function to obtain the coroutine that can then
                        # be awaited in the current event loop.
                        result = await eval(f"{random_identifier}()", globals_dict)
                        # Print the result of the expression if it is not None to
                        # simulate the behavior of the interpreter.
                        if result is not None:
                            pprint(result)
                        # Remove the temporary function from the global scope so that
                        # it can't be accessed from the interpreter.
                        del globals_dict[random_identifier]
                    # Here syntax error will be raised if the input provided is not a
                    # valid python expression, so we instead execute the statement.
                    except SyntaxError:
                        exec(expression, globals_dict)
                # When this is raised, this indicates that the user has started a
                # statement that requires an indent. We enter a loop where we allow
                # the user to arbitrarily provide multiline data.
                except IndentationError as exc:
                    # Kinda hacky way to differentiate between different types of
                    # indentation errors. We only want to catch the one that indicates
                    # the user started a statement that requires an indent.
                    if "expected an indented block" not in str(exc):
                        _print_custom_formatted_exception_message(
                            exc=exc,
                            temporary_function_identifier=random_identifier,
                        )
                        continue

                    def prompt_continuation(
                        width: int,
                        _line_number: int,
                        wrap_count: int,
                    ):
                        if wrap_count > 0:
                            return " " * width
                        else:
                            text = "." * (width - 1) + " "
                            return HTML(f"<bold><ansiwhite>{text}</ansiwhite></bold>")

                    try:
                        multi_line_input = await multi_line_input_session.prompt_async(
                            ".................... ",
                            prompt_continuation=prompt_continuation,
                        )
                    except KeyboardInterrupt:
                        continue
                    indent_input_lines_buffer = [expression] + multi_line_input.split(
                        "\n",
                    )

                    try:
                        # Determine the indentation level of the first indented line of
                        # the buffer.
                        indent_level = len(indent_input_lines_buffer[1]) - len(
                            indent_input_lines_buffer[1].lstrip(),
                        )

                        # Same procedure as executing single line inputs as above.
                        random_identifier = "_" + "".join(
                            [random.choice(string.ascii_letters) for _ in range(10)],
                        )
                        indent = " " * indent_level
                        temporary_function = (
                            f"async def {random_identifier}():"
                            + f"\n{indent}"
                            + f"\n{indent}".join(indent_input_lines_buffer)
                            + f"\n{indent}globals().update(locals())"
                        )
                        exec(temporary_function, globals_dict)
                        await eval(f"{random_identifier}()", globals_dict)
                        del globals_dict[random_identifier]
                    except Exception as exc:
                        _print_custom_formatted_exception_message(
                            exc=exc,
                            temporary_function_identifier=random_identifier,
                        )
                except KeyboardInterrupt:
                    self.logger.info("Use 'exit' to exit the debug interpreter")
                except Exception as exc:
                    _print_custom_formatted_exception_message(
                        exc=exc,
                        temporary_function_identifier=random_identifier,
                    )
