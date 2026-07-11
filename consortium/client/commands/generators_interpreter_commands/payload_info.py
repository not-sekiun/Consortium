from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import BaseConnectedCommand
from consortium.client.utils.agent_template_command_utils import (
    display_agent_template_info,
)
from consortium.client.utils.formatter_utils import (
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_bulleted_key_value_string,
    format_size_bytes_as_human_readable_str,
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
            help="The payload's resource ID.",
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
            # The payload metadata lives in the `data` field. `agent_template` is the
            # immutable point-in-time reference persisted at creation (only the template's
            # label and name); `resolved_agent_template` is its live, read-time resolution
            # (the full agent template) and is `None` when the template can no longer be
            # resolved (for example it was deleted after the payload was created).
            data = payload["data"]
            info_table.add_row(
                "Build Parameters",
                format_dict_as_multi_line_bulleted_key_value_string(
                    input_dict=data["build_parameters"]
                ),
            )
            console.print(info_table, "")

            agent_template_reference = data["agent_template"]
            resolved_agent_template = data["resolved_agent_template"]

            if resolved_agent_template is None:
                # The agent template can no longer be resolved, so only the persisted
                # reference (label and name as of creation) is available. Full template
                # details (including in verbose mode) cannot be shown.
                unresolved_table = Table(
                    title="Agent Template (Summary)", highlight=True
                )
                unresolved_table.add_column("Information")
                unresolved_table.add_column("Data")
                unresolved_table.add_row(
                    "Template Label", agent_template_reference["label"]
                )
                unresolved_table.add_row(
                    "Template Name", agent_template_reference["name"]
                )
                unresolved_table.add_row("Status", "Agent template no longer exists")
                console.print(unresolved_table, "")
            elif not parsed_args.verbose:
                # Summary table showing agent type and key template identifiers
                summary_table = Table(title="Agent Template (Summary)", highlight=True)
                summary_table.add_column("Information")
                summary_table.add_column("Data")
                summary_table.add_row(
                    "Agent Type", resolved_agent_template["agent_type"]["name"]
                )
                summary_table.add_row(
                    "Template ID", resolved_agent_template["agent_template_id"]
                )
                summary_table.add_row(
                    "Template Label", resolved_agent_template["label"]
                )
                summary_table.add_row("Template Name", resolved_agent_template["name"])
                console.print(summary_table, "")
            else:
                display_agent_template_info(agent_template=resolved_agent_template)

                # Options in a dedicated table to avoid cluttering the template table
                options = resolved_agent_template["options"]
                if options:
                    options_table = Table(
                        title="Agent Template Options", highlight=True
                    )
                    options_table.add_column("Option")
                    options_table.add_column("Option Type")
                    options_table.add_column("Description")
                    for option_name, option in options.items():
                        options_table.add_row(
                            option_name,
                            option.get("option_type", ""),
                            str(option.get("description", "")),
                        )
                    console.print(options_table, "")
        except SystemExit:
            pass

        return ContinueSignal()
