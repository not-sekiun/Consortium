import traceback

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.patch_stdout import StdoutProxy, patch_stdout
from prompt_toolkit.styles import Style

import consortium.server.server_singletons as server_singletons
from consortium.framework.base_plugin import BasePlugin
from consortium.server.server_logging import log_formatter


# TODO: Allow plugins to define third party libraries that are required for the plugin
#  to run.
class Plugin(BasePlugin):
    name = "Debug Interpreter Plugin"
    description = (
        "A plugin that provides an interactive debug interpreter for running arbitrary "
        "Python code in the context of the framework. Access to all of the "
        "frameworks services is given in the environment."
    )
    authors = {"Sekiun (github.com/not-sekiun)"}
    autostart = True

    async def on_plugin_started(self) -> None:
        self.plugin_logger.info(
            "Debug interpreter is now running. All framework services are available in "
            "the environment. You can tab complete services along with their API "
            "methods.",
        )
        self.plugin_logger.warning(
            "⚠️ Note that whatever you do here WILL affect the state of the framework. "
            "You are also not protected from accessing any private attributes or "
            "methods. Modify things with caution. You have been warned.",
        )

        # TODO: Implement a logging service to make this more configurable and
        #  accessible.
        logger.remove(2)
        logger.add(
            StdoutProxy(raw=True),
            format=log_formatter,
            level=server_singletons.server.server_config.log_level,
        )

    async def on_plugin_running(self) -> None:
        # Super fucking cursed dictionary comprehension within a dictionary
        # comprehension. Essentially what we are doing is constructing a dictionary of
        # with keys of type string, each key corresponds to the symbol of a service.
        # The values of those keys is another dictionary with keys that now correspond
        # to the public methods (any property that is callable and that does not start
        # with an underscore) of each service. This lets us dynamically build the
        # completer based on whatever services are added to the framework and made
        # publicly accessible from the `server_singletons` module. All this for a
        # fucking autocomplete feature, whew.
        completer_dict = {
            attr: {
                method: None
                for method in dir(getattr(server_singletons, attr))
                if callable(getattr(getattr(server_singletons, attr), method))
                and not method.startswith("_")
            }
            for attr in dir(server_singletons)
            if attr.endswith("_service")
        }
        completer_dict["exit"] = None
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
            completer=NestedCompleter.from_nested_dict(completer_dict),
            style=style,
        )
        globals_dict = {
            attr: getattr(server_singletons, attr)
            for attr in dir(server_singletons)
            if attr.endswith("_service")
        }
        with patch_stdout():
            while True:
                try:
                    expression = (
                        await session.prompt_async(
                            prompt,
                            style=style,
                        )
                    ).rstrip(" ")

                    if expression in ("exit", "exit()"):
                        self.plugin_logger.success(
                            "Exited the debug interpreter. Use CTRL-C to stop the "
                            "server.",
                        )
                        break

                    exec(
                        expression,
                        globals_dict,
                    )
                except IndentationError as exc:
                    # Kinda hacky way to differentiate between different types of
                    # indentation errors.
                    if "expected an indented block" not in str(exc):
                        raise exc

                    # This exception being raised indicates a user starts an expression
                    # whose next line requires an indent. So we enter a loop where we
                    # allow the user to arbitrarily provide multiline content.
                    indent_input_lines_buffer = [expression]
                    while True:
                        next_line = await session.prompt_async(".................... ")
                        indent_input_lines_buffer.append(next_line)
                        if not next_line:
                            if not indent_input_lines_buffer[-1]:
                                break
                    try:
                        exec(
                            "\n".join(indent_input_lines_buffer),
                            globals_dict,
                        )
                    except Exception:
                        traceback.print_exc()
                except KeyboardInterrupt:
                    self.plugin_logger.info("Use 'exit' to exit the debug interpreter.")
                except Exception:
                    traceback.print_exc()

    async def on_plugin_stopped(self) -> None:
        pass

    async def on_plugin_cancelled(self) -> None:
        pass

    async def on_plugin_errored(self, exc: Exception) -> None:
        self.plugin_logger.error(
            "❗ Debug console interpreter plugin encountered a fatal error while "
            "running. Exiting console...",
        )
