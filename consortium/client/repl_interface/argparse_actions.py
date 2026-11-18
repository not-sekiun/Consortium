from argparse import SUPPRESS, Action, ArgumentParser, Namespace
from collections.abc import Sequence
from typing import Any


class ExtendedHelpAction(Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        *,
        epilog: str,
        help: str | None = None,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            default=SUPPRESS,
            help=help,
        )
        self.epilog = epilog

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Any,
        option_string: str | None = None,
    ) -> None:
        original_epilog = parser.epilog
        try:
            parser.epilog = self.epilog
            parser.print_help()
        finally:
            parser.epilog = original_epilog
        parser.exit()
