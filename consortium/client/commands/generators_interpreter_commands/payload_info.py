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
    format_list_as_multi_line_bulleted_string,
    format_size_bytes_as_human_readable_str,
    format_snake_case_to_title,
)
from consortium.client.utils.printer_utils import console


class PayloadInfoCommand(BaseConnectedCommand):
    name = "pl-info"
    description = "Display information about a payload by its resource ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          pl-info 123e4567-e89b-12d3-a456-42661417400
          pl-info 123e4567-e89b-12d3-a456-42661417400 --verbose
        """,
    )
    group = "Payload Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "resource_id",
            help="Resource ID of the payload to display information for.",
            nargs=1,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            help="Display full agent template information including all options.",
            action="store_true",
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            payload = await rest_api.get_payload_by_resource_id(
                resource_id=parsed_args.resource_id[0],
            )

            # Resource information table
            info_table = Table(title="Payload Information", highlight=True)
            info_table.add_column("Information")
            info_table.add_column("Data")
            info_table.add_row("Resource ID", str(payload["resource_id"]))
            info_table.add_row("Name", str(payload["name"]))
            info_table.add_row("Description", str(payload["description"]))
            size = payload["size"]
            info_table.add_row(
                "Size",
                f"{size} B ({format_size_bytes_as_human_readable_str(size_bytes=size)})"
                if size is not None
                else "N/A",
            )
            info_table.add_row("Exists on Disk", str(payload["exists_on_disk"]))
            info_table.add_row("MD5 Checksum", str(payload["md5_checksum"]))
            info_table.add_row(
                "Datetime Created",
                format_datetime_as_human_readable_str(
                    datetime_str=payload["datetime_created"], include_elapsed_time=True
                ),
            )
            info_table.add_row(
                "Datetime Modified",
                format_datetime_as_human_readable_str(
                    datetime_str=payload["datetime_modified"], include_elapsed_time=True
                ),
            )
            info_table.add_row(
                "Type", "DIRECTORY" if payload["is_directory"] else "FILE"
            )
            console.print(info_table, "")

            agent_type = payload["agent_type"]
            agent_template = payload["agent_template"]

            if not parsed_args.verbose:
                # Summary table showing agent type and key template identifiers
                summary_table = Table(
                    title="Agent & Template [Summary]", highlight=True
                )
                summary_table.add_column("Information")
                summary_table.add_column("Data")
                summary_table.add_row("Agent Type", agent_type["name"])
                summary_table.add_row(
                    "Template ID", agent_template["agent_template_id"]
                )
                summary_table.add_row("Template Label", agent_template["label"])
                summary_table.add_row("Template Name", agent_template["name"])
                console.print(summary_table, "")
            else:
                # Full agent template table
                at_table = Table(title="Agent Template Information", highlight=True)
                at_table.add_column("Information")
                at_table.add_column("Data")
                at_table.add_row(
                    "Agent Template ID", agent_template["agent_template_id"]
                )
                at_table.add_row("Label", agent_template["label"])
                at_table.add_row("Name", agent_template["name"])
                at_table.add_row("Description", agent_template["description"])
                at_table.add_row("Version", agent_template["version"])
                at_table.add_row(
                    "Compatible Framework Version",
                    agent_template["compatible_framework_version"],
                )
                at_table.add_row(
                    "Authors",
                    format_list_as_multi_line_bulleted_string(
                        input_list=agent_template["authors"]
                    ),
                )
                at_table.add_row("Agent Type", agent_type["name"])
                at_table.add_row(
                    "Compatible Listener Types",
                    format_list_as_multi_line_bulleted_string(
                        input_list=list(agent_template["compatible_listener_types"]),
                    ),
                )
                console.print(at_table, "")

                # Options in a dedicated table to avoid cluttering the template table
                options = agent_template["options"]
                if options:
                    options_table = Table(
                        title="Agent Template Options", highlight=True
                    )
                    options_table.add_column("Option")
                    options_table.add_column("Type")
                    options_table.add_column("Description")
                    for option_name, option in options.items():
                        options_table.add_row(
                            option_name,
                            format_snake_case_to_title(option.get("option_type", "")),
                            str(option.get("description", "")),
                        )
                    console.print(options_table, "")
        except SystemExit:
            pass

        return ContinueSignal()
