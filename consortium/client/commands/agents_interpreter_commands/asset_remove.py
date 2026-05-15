from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
)


class AssetRemoveCommand(BaseCommand):
    name = "as-rm"
    description = "Delete an asset by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          as-rm 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Asset Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "asset_id",
            help="ID of the asset to be removed.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            self.parser.parse_args(context.arguments)
        except SystemExit:
            pass

        return ContinueSignal()
