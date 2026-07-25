from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class AssetRenameCommand(BaseConnectedCommand):
    name = "as-rename"
    description = "Set the name of an asset by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          as-rename 123e4567-e89b-12d3-a456-42661417400 "New name"
        """,
    )
    group = "Asset Management Commands"
    autocompletes = Autocomplete.ASSET_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="The asset's resource ID.",
            nargs=1,
        )
        parser.add_argument(
            "name",
            help="New name for the asset.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # The asset is fetched first purely so that the previous name can be shown
            # back to the operator alongside the new one.
            asset = await rest_api.get_asset_by_resource_id(
                resource_id=parsed_args.resource_id[0],
            )
            await rest_api.update_asset_by_resource_id(
                resource_id=parsed_args.resource_id[0],
                new_asset_attributes={"name": parsed_args.name[0]},
            )
            print_success(
                f"Renamed asset '{asset['name']}' ({asset['resource_id']}) to "
                f"'{parsed_args.name[0]}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
