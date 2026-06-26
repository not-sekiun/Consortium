import copy

from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import Completer, NestedCompleter, PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition

type CompletionsDict = dict[str, None | CompletionsDict]


# `CustomCompleters` take the form of `NestedCompleters` but whose terminal leaf
# completions are a looping set of `PathCompleters` to allow easy completing of file
# paths anywhere
class CustomCompleter(Completer):
    def __init__(self, completions_dict: CompletionsDict):
        self._completions_dict = completions_dict
        self._nested_completer = NestedCompleter.from_nested_dict(completions_dict)
        self._path_completer = PathCompleter(expanduser=True)

    def get_completions_dict(self) -> CompletionsDict:
        return copy.deepcopy(self._completions_dict)

    def set_completions_dict(self, completions_dict: CompletionsDict) -> None:
        self._completions_dict = completions_dict
        self._nested_completer = NestedCompleter.from_nested_dict(completions_dict)

    def in_command_position(self, text):
        """True  -> still typing a command or subcommand.
        False -> typing a positional argument (i.e. a file path)."""
        stripped = text.lstrip()
        if not stripped:
            return True

        words = stripped.split()
        has_trailing_space = text != text.rstrip()
        current = self._completions_dict

        for i, word in enumerate(words):
            is_last_word = i == len(words) - 1
            is_being_typed = is_last_word and not has_trailing_space

            if is_being_typed:
                # The token under the cursor is a command if its parent node is
                # still a dict of further commands.
                return isinstance(current, dict)

            if isinstance(current, dict) and word in current:
                current = current[word]
            else:
                # An unknown / leaf token sits before the cursor, so everything
                # after it is an argument -> no longer completing commands.
                return False

        return isinstance(current, dict)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if self.in_command_position(text):
            # NestedCompleter does its own tokenizing, so hand it the full doc.
            yield from self._nested_completer.get_completions(document, complete_event)
            return

        # PathCompleter treats the WHOLE text_before_cursor as a single path.
        # Hand it "deploy src/m" and it tries to list a dir called "deploy src"
        # and finds nothing.  So strip everything up to the last whitespace and
        # give it only the current token, in its own Document.
        #
        # (This naive rfind(" ") split ignores quoted paths with spaces; good
        # enough for the MRE.
        token = text[text.rfind(" ") + 1 :]
        sub_doc = Document(token, cursor_position=len(token))
        yield from self._path_completer.get_completions(sub_doc, complete_event)


# complete_while_typing must be a dynamic filter: True in command position
# (popup auto-shows) and False in argument position (file completions stay
# hidden until <Tab>).  We pass `completer` directly rather than reading
# buffer.completer, because PromptSession wraps the completer in a DynamicCompleter and
# the isinstance check on the wrapper would fail.
def custom_completer_filter_builder(custom_completer: CustomCompleter):
    @Condition
    def custom_completer_filter() -> bool:
        try:
            text = get_app().current_buffer.document.text_before_cursor
            return custom_completer.in_command_position(text)
        except Exception:
            return True

    return custom_completer_filter
