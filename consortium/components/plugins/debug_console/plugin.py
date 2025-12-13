import random
import string
import traceback

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.patch_stdout import StdoutProxy, patch_stdout
from prompt_toolkit.styles import Style

import consortium.server.server_singletons as server_singletons
from consortium.framework.plugins.base_plugin import BasePlugin
from consortium.server.server_logging import log_formatter


class _ServicesMethodsCompleter(Completer):
    def __init__(self, services_methods_completion_dict: dict[str, dict[str, None]]):
        self.services_methods_completions_dict = services_methods_completion_dict

    # Checks to see if a key list exists in a dictionary. The key list is a list of
    # keys that are traversed recursively in the dictionary. So if the key list is
    # ['a', 'b', 'c'] then the function will check if the dictionary has a key 'a'
    # which has a key 'b' which has a key 'c' and then for that key 'c' check all valid
    # completions for the provided completion substring.
    def _return_valid_completions_in_services_methods_completions_dict(
        self,
        key_list: list[str],
        string_to_complete: str,
    ) -> list[str]:
        current_dict = self.services_methods_completions_dict
        for key in key_list:
            if key not in current_dict:
                # Key list is not even valid so return an empty list. This means that no
                # such chain of namespaces exists.
                return []
            current_dict = current_dict[key]

        # Key list is valid but there are no more completions possible. This means that
        # we are at the end of the chain of namespaces.
        if current_dict is None:
            return []

        # Key list is valid and there are more completions possible. This means that we
        # are not at the end of the chain of namespaces so we return the next valid
        # completions if there are any.
        valid_completions = []
        for key in current_dict:
            if key.startswith(string_to_complete):
                valid_completions.append(key)
        return valid_completions

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
            for (
                completion
            ) in self._return_valid_completions_in_services_methods_completions_dict(
                key_list=dot_separated_words[:-1],
                string_to_complete=dot_separated_words[-1],
            ):
                yield Completion(
                    completion,
                    start_position=-len(dot_separated_words[-1]),
                )
        else:
            for service in self.services_methods_completions_dict:
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
    innermost_frame.lineno = innermost_frame.lineno - 1
    innermost_frame.filename = "<stdin>"
    # This indicates the error occurred at the top most module level. But since the
    # code runs in a temporary function implicitly, we need to change the name.
    if innermost_frame.name == temporary_function_identifier:
        innermost_frame.name = "<module>"
    new_stack_summary = [innermost_frame]
    # Print exception header.
    print("Traceback (most recent call last):")
    # Print exception location.
    print("".join(traceback.format_list(new_stack_summary)), end="")
    # Print exception type and message.
    print(
        f"{exc.__class__.__name__}: {exc}",
    )


class Plugin(BasePlugin):
    label = "consortium.plugins.debug_console_plugin"
    name = "Debug Interpreter Plugin"
    description = (
        "A plugin that provides an interactive debug interpreter for running arbitrary "
        "Python code in the context of the framework. Access to all of the "
        "frameworks services is given in the environment."
    )
    version = "0.1.0"
    compatible_framework_version = ">=1.0.0"
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_started(self) -> None:
        self.logger.info(
            "Debug interpreter is now running. All framework services are available in "
            "the current environment. You can tab complete services along with their "
            "API methods.",
        )

        # TODO: Consider providing a dedicated logger service to interact with logging,
        #  might be useful to send logs remotely or do custom things with them.
        # Remove the current stdout logger and patch it with `StdoutProxy` to prevent
        # loguru from messing with prompt_toolkit's stdout handling. Retain the current
        # log configuration.
        logger.remove(2)
        logger.add(
            StdoutProxy(raw=True),
            format=log_formatter,
            level=server_singletons.server.logging_config.log_level,
            colorize=server_singletons.server.logging_config.colorize,
        )

    async def on_running(self) -> None:
        # Super fucking cursed dictionary comprehension within a dictionary
        # comprehension. Essentially what we are doing is constructing a dictionary
        # with keys of type string, each key corresponds to the symbol of a service.
        # The values of those keys is another dictionary with keys that now correspond
        # to the public methods (any property that is callable and that does not start
        # with an underscore) of each service. This lets us dynamically build the
        # completer based on whatever services are added to the framework and made
        # publicly accessible from the `server_singletons` module. All this for a
        # fucking autocomplete feature, whew.
        services_methods_completions_dict = {
            attr: {
                method: None
                for method in dir(getattr(server_singletons, attr))
                if callable(getattr(getattr(server_singletons, attr), method))
                and not method.startswith("_")
            }
            for attr in dir(server_singletons)
            if attr.endswith("_service")
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
        session = PromptSession(
            completer=_ServicesMethodsCompleter(
                services_methods_completion_dict=services_methods_completions_dict,
            ),
            style=style,
        )
        globals_dict = {
            attr: getattr(server_singletons, attr)
            for attr in dir(server_singletons)
            if attr.endswith("_service")
        }

        with patch_stdout(raw=True):
            while True:
                try:
                    expression = (
                        # We need to explicitly provide the `multiline` and
                        # `bottom_toolbar` parameters here because for some reason
                        # those parameter values modified and persisted across
                        # different calls to `prompt_async()`. This means that if a
                        # multiline prompt is called for `prompt_async()` once then
                        # those parameters that made it multiline will apply to the
                        # single line prompt too unless explicitly set otherwise.
                        await session.prompt_async(
                            prompt,
                            style=style,
                            multiline=False,
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
                        [random.choice(string.ascii_letters) for _ in range(10)],
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
                            print(result)
                        # Remove the temporary function from the global scope so that
                        # it can't be accessed from the interpreter.
                        del globals_dict[random_identifier]
                    # Here syntax error will be raised if the input provided is not a
                    # valid python expression, so we instead execute the statement.
                    except SyntaxError:
                        exec(expression, globals_dict)
                # When this is raised, this indicates that the user has started a
                # statement that requires an indent. We enter a loop where we allow
                # the user to arbitrarily provide multiline content.
                except IndentationError as exc:
                    # Kinda hacky way to differentiate between different types of
                    # indentation errors. We only want to catch the one that indicates
                    # the user started a statement that requires an indent.
                    if "expected an indented block" not in str(exc):
                        raise exc

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
                        multiline_input = await session.prompt_async(
                            ".................... ",
                            multiline=True,
                            prompt_continuation=prompt_continuation,
                            bottom_toolbar=HTML(
                                "<bold>Press [Meta+Enter] or [Esc] followed by [Enter] to "
                                "accept input. Press [Ctrl+C] to cancel input.</bold>",
                            ),
                        )
                    except KeyboardInterrupt:
                        continue
                    indent_input_lines_buffer = [expression] + multiline_input.split(
                        "\n",
                    )

                    try:
                        # Determine the indentation level of the first indented line of
                        # the buffer.
                        indent_level = len(indent_input_lines_buffer[1]) - len(
                            indent_input_lines_buffer[1].lstrip(),
                        )

                        # Create a temporary function to hold the code block. This
                        # allows execution of asynchronous code blocks. At the very end
                        # of execution the temporary function updates the global scope
                        # with its local scope to retain the behavior of the interpreter
                        # instantiating variables because the user is not aware of any
                        # implicit scoping happening in the background.
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
                        # Create the temporary function to house asynchronous code.
                        exec(temporary_function, globals_dict)
                        # Evaluate the function to obtain the coroutine that can then
                        # be awaited in the current event loop.
                        await eval(f"{random_identifier}()", globals_dict)
                        # Remove the dummy function from the global scope.
                        del globals_dict[random_identifier]
                    except Exception as exc:
                        _print_custom_formatted_exception_message(
                            exc=exc,
                            temporary_function_identifier=random_identifier,
                        )
                except KeyboardInterrupt:
                    self.logger.info("Use 'exit' to exit the debug interpreter.")
                except Exception as exc:
                    _print_custom_formatted_exception_message(
                        exc=exc,
                        temporary_function_identifier=random_identifier,
                    )

    async def on_errored(self, _exc: Exception) -> None:
        self.logger.error(
            "Debug console interpreter plugin encountered a fatal error while "
            "running. Exiting console...",
        )
