from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_list_as_multi_line_bulleted_string,
)
from consortium.client.utils.printer_utils import console


class ListenerTemplateInfoCommand(BaseCommand):
    name = "lt-info"
    description = "Display information about a listener template by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          lt-info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help=(
                "Listener template ID of the listener template to display information "
                "for."
            ),
            nargs=1,
        )

    @staticmethod
    async def _display_listener_template_info(
        rest_api: RestAPI, listener_template_id: str
    ) -> None:
        listener_template = (
            await rest_api.get_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
            )
        )
        table = Table(title="Listener Template Information", highlight=True)
        table.add_column("Information")
        table.add_column("Data")
        table.add_row(
            "Listener Template ID",
            listener_template["listener_template_id"],
        )
        table.add_row(
            "Label",
            listener_template["label"],
        )
        table.add_row("Name", listener_template["name"])
        table.add_row("Description", listener_template["description"])
        table.add_row("Version", listener_template["version"])
        table.add_row(
            "Compatible Framework Version",
            listener_template["compatible_framework_version"],
        )
        table.add_row(
            "Authors",
            format_list_as_multi_line_bulleted_string(
                input_list=listener_template["authors"]
            ),
        )
        table.add_row(
            "Listener Type",
            listener_template["listener_type"]["name"],
        )
        table.add_row(
            "Compatible Agent Types",
            format_list_as_multi_line_bulleted_string(
                input_list=listener_template["listener_type"][
                    "registered_compatible_agent_types"
                ]
            ),
        )
        console.print(table, "")

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_listener_template_info(
                rest_api=rest_api,
                listener_template_id=parsed_args.listener_template_id[0],
            )
        except SystemExit:
            pass

        return ContinueSignal()
