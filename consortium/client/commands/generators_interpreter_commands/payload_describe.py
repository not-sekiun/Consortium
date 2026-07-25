from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class PayloadDescribeCommand(BaseConnectedCommand):
    name = "pl-describe"
    description = "Set the description of a payload by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          pl-describe 123e4567-e89b-12d3-a456-42661417400 "New description"
        """,
    )
    group = "Payload Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="The resource ID of the payload whose description should be changed.",
            nargs=1,
        )
        parser.add_argument(
            "description",
            help="New description for the payload.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # The payload is fetched first purely so that its name can be shown back to
            # the operator alongside its resource ID.
            payload = await rest_api.get_payload_by_resource_id(
                resource_id=parsed_args.resource_id[0],
            )
            await rest_api.update_payload_by_resource_id(
                resource_id=parsed_args.resource_id[0],
                new_payload_attributes={"description": parsed_args.description[0]},
            )
            print_success(
                f"Updated description of payload '{payload['name']}' "
                f"({payload['resource_id']}) to '{parsed_args.description[0]}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
