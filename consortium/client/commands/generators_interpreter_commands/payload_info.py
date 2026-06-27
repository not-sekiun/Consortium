from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_size_bytes_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class PayloadInfoCommand(BaseConnectedCommand):
    name = "pl-info"
    description = "Display information about a payload by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          pl-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Payload Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "payload_id",
            help="ID of the payload to display information for.",
            nargs=1,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            payload = await rest_api.get_payload_by_payload_id(
                payload_id=parsed_args.payload_id[0],
            )
            table = Table(title="Payload Information", highlight=True)
            table.add_column("Information")
            table.add_column("Data")
            table.add_row("Resource ID", str(payload["resource_id"]))
            table.add_row("Name", str(payload["name"]))
            table.add_row("Description", str(payload["description"]))
            table.add_row(
                "Size",
                f"{payload['size']} ({format_size_bytes_as_human_readable_str(size_bytes=payload['size'])})",
            )
            table.add_row("Exists on disk", str(payload["exists_on_disk"]))
            table.add_row("MD5 Checksum", str(payload["md5_checksum"]))
            table.add_row(
                "Datetime Created",
                format_datetime_as_human_readable_str(
                    datetime_str=payload["datetime_created"], include_elapsed_time=True
                ),
            )
            table.add_row(
                "Datetime Updated",
                format_datetime_as_human_readable_str(
                    datetime_str=payload["datetime_modified"], include_elapsed_time=True
                ),
            )
            table.add_row("Type", "DIRECTORY" if payload["is_directory"] else "FILE")
            console.print(table, "")
        except SystemExit:
            pass

        return ContinueSignal()
