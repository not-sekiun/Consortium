import pathlib
import shutil
import tempfile
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter

from rich.progress import Progress
from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
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
from consortium.client.utils.printer_utils import (
    console,
    print_error,
    print_info,
    print_success,
)


class PayloadCommand(BaseConnectedCommand):
    name = "payload"
    description = "Manage payloads through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          payload list
          payload info 123e4567-e89b-12d3-a456-42661417400
          payload download 123e4567-e89b-12d3-a456-42661417400
          payload rename 123e4567-e89b-12d3-a456-42661417400 "New name"
          payload describe 123e4567-e89b-12d3-a456-42661417400 "New description"
          payload remove 123e4567-e89b-12d3-a456-42661417400

        Notes:
          Every sub-command carries its own help, for example:
            payload download --help
        """,
    )
    group = "Resource Management Commands"
    autocompletes = {
        "list": None,
        "info": Autocomplete.PAYLOAD_ID,
        "download": Autocomplete.PAYLOAD_ID,
        "rename": Autocomplete.PAYLOAD_ID,
        "describe": Autocomplete.PAYLOAD_ID,
        "remove": Autocomplete.PAYLOAD_ID,
    }

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        subparsers.add_parser(
            "list",
            help="List all payloads along with their essential information.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  payload list
                """,
            ),
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help="Display information about a payload by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  payload info 123e4567-e89b-12d3-a456-42661417400
                  payload info 123e4567-e89b-12d3-a456-42661417400 --verbose
                """,
            ),
        )
        parser_info.add_argument(
            "resource_id",
            help="The payload's resource ID.",
            nargs=1,
        )
        parser_info.add_argument(
            "-v",
            "--verbose",
            help="Display full agent template information including all options.",
            action="store_true",
        )

        # download sub-command
        parser_download = subparsers.add_parser(
            "download",
            help="Download a payload by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  payload download 123e4567-e89b-12d3-a456-42661417400
                  payload download 123e4567-e89b-12d3-a456-42661417400 --decompress  # Automatically decompresses the payload if it is a payload directory.
                """,
            ),
        )
        parser_download.add_argument(
            "resource_id",
            help="The payload's resource ID.",
            nargs=1,
        )
        parser_download.add_argument(
            "-o",
            "--output",
            help=(
                "Output path to write the payload file or directory to (defaults to "
                "the current working directory with the payload's name)."
            ),
            nargs="?",
        )
        parser_download.add_argument(
            "-w",
            "--overwrite",
            help=(
                "Overwrite the output file if it already exists (disabled by default). "
                "Refuses to overwrite if the output path is an existing directory."
            ),
            action="store_true",
        )
        parser_download.add_argument(
            "-d",
            "--decompress",
            help=(
                "Automatically decompress downloaded archive (.zip) payload directories "
                "(disabled by default). Does not decompress payloads explicitly marked "
                "as files even if they are zip archives."
            ),
            action="store_true",
        )

        # rename sub-command
        parser_rename = subparsers.add_parser(
            "rename",
            help="Set the name of a payload by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  payload rename 123e4567-e89b-12d3-a456-42661417400 "New name"
                """,
            ),
        )
        parser_rename.add_argument(
            "resource_id",
            help="The payload's resource ID.",
            nargs=1,
        )
        parser_rename.add_argument(
            "name",
            help="New name for the payload.",
            nargs=1,
        )

        # describe sub-command
        parser_describe = subparsers.add_parser(
            "describe",
            help="Set the description of a payload by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  payload describe 123e4567-e89b-12d3-a456-42661417400 "New description"
                """,
            ),
        )
        parser_describe.add_argument(
            "resource_id",
            help="The resource ID of the payload whose description should be changed.",
            nargs=1,
        )
        parser_describe.add_argument(
            "description",
            help="New description for the payload.",
            nargs=1,
        )

        # remove sub-command
        parser_remove = subparsers.add_parser(
            "remove",
            help="Delete a payload by its resource ID.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  payload remove 123e4567-e89b-12d3-a456-42661417400
                """,
            ),
        )
        parser_remove.add_argument(
            "resource_id",
            help="The payload's resource ID.",
            nargs=1,
        )

    @staticmethod
    async def _handle_list_sub_command(
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        payloads = await rest_api.get_all_payloads()

        table = Table(title="Payloads", highlight=True)
        table.add_column("Payload ID")
        table.add_column("Name")
        table.add_column("Agent Type")
        table.add_column("Type")
        table.add_column("Size")
        table.add_column("Datetime Created")
        for payload in payloads:
            size = payload["size"]
            # A payload is "just" a repository resource with metadata: the
            # generating agent template reference, build parameters and payload
            # data live in the `data` field. The stored reference records only the
            # template's label and name; the live `resolved_agent_template` (when
            # present) supplies the template's current details (including its agent
            # type), while its absence means the agent template has since been
            # deleted.
            resolved_agent_template = payload["data"]["resolved_agent_template"]
            agent_type = (
                resolved_agent_template["agent_type"]["name"]
                if resolved_agent_template is not None
                else "N/A"
            )
            table.add_row(
                payload["resource_id"],
                payload["name"],
                agent_type,
                "DIRECTORY" if payload["is_directory"] else "FILE",
                format_size_bytes_as_human_readable_str(size_bytes=size)
                if size is not None
                else "N/A",
                format_datetime_as_human_readable_str(
                    datetime_str=payload["datetime_created"],
                    include_elapsed_time=True,
                ),
            )
        console.print(table, "")

        return ContinueSignal()

    @staticmethod
    async def _handle_info_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
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
        info_table.add_row("Type", "DIRECTORY" if payload["is_directory"] else "FILE")
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
            unresolved_table = Table(title="Agent Template (Summary)", highlight=True)
            unresolved_table.add_column("Information")
            unresolved_table.add_column("Data")
            unresolved_table.add_row(
                "Template Label", agent_template_reference["label"]
            )
            unresolved_table.add_row("Template Name", agent_template_reference["name"])
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
            summary_table.add_row("Template Label", resolved_agent_template["label"])
            summary_table.add_row("Template Name", resolved_agent_template["name"])
            console.print(summary_table, "")
        else:
            display_agent_template_info(agent_template=resolved_agent_template)

            # Options in a dedicated table to avoid cluttering the template table
            options = resolved_agent_template["options"]
            if options:
                options_table = Table(title="Agent Template Options", highlight=True)
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

        return ContinueSignal()

    @staticmethod
    async def _handle_download_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        payload = await rest_api.get_payload_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        # If user supplies an output path that takes precedence, else use the payload
        # name directly for payload files or append ".zip" for payload directories
        # because all payload directories are returned as zip files. Resolved so that
        # every message below names the exact location written to: a bare relative name
        # reads as if the file landed next to the user, which is misleading when the
        # client runs in a container and the working directory is a container path.
        output_file_path = pathlib.Path(
            parsed_args.output
            if parsed_args.output
            else (
                payload["name"]
                if not payload["is_directory"]
                else payload["name"] + ".zip"
            ),
        ).resolve()

        if output_file_path.exists():
            # Refuse to overwrite a directory regardless of the overwrite flag as
            # clobbering a whole directory is never the intended download behaviour.
            if output_file_path.is_dir():
                print_error(
                    f"Cannot download payload to '{output_file_path}' because a "
                    f"directory already exists at that path"
                )
                return ContinueSignal()
            if not parsed_args.overwrite:
                print_error(
                    f"Cannot download payload to '{output_file_path}' because a file "
                    f"already exists at that path (use -w/--overwrite to overwrite "
                    f"it)"
                )
                return ContinueSignal()

        print_info(
            f"Downloading payload {'directory' if payload['is_directory'] else 'file'} "
            f"'{payload['name']}' ({payload['resource_id']}) to '{output_file_path}'..."
        )
        with Progress(transient=True) as progress:
            downloading_task = progress.add_task(
                "",
                total=payload["size"],
            )
            with output_file_path.open("wb") as output_file:
                async for chunk in rest_api.download_payload_by_resource_id(
                    resource_id=parsed_args.resource_id[0],
                ):
                    progress.update(downloading_task, advance=len(chunk))
                    output_file.write(chunk)
        print_success("Finished downloading payload")

        if payload["is_directory"] and parsed_args.decompress:
            print_info(f"Decompressing payload directory: '{output_file_path}'")
            with tempfile.TemporaryDirectory() as temp_dir:
                shutil.unpack_archive(output_file_path, temp_dir)
                output_file_path.unlink()
                shutil.move(temp_dir, output_file_path)
            print_success("Finished decompressing payload")

        return ContinueSignal()

    @staticmethod
    async def _handle_rename_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        # The payload is fetched first purely so that the previous name can be shown
        # back to the operator alongside the new one.
        payload = await rest_api.get_payload_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        await rest_api.update_payload_by_resource_id(
            resource_id=parsed_args.resource_id[0],
            new_payload_attributes={"name": parsed_args.name[0]},
        )
        print_success(
            f"Renamed payload '{payload['name']}' ({payload['resource_id']}) to "
            f"'{parsed_args.name[0]}'",
        )

        return ContinueSignal()

    @staticmethod
    async def _handle_describe_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
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

        return ContinueSignal()

    @staticmethod
    async def _handle_remove_sub_command(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        await rest_api.delete_payload_by_resource_id(
            resource_id=parsed_args.resource_id[0],
        )
        print_success(f"Deleted payload '{parsed_args.resource_id[0]}'")

        return ContinueSignal()

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            match parsed_args.sub_command:
                case "list":
                    return await self._handle_list_sub_command(context=context)
                case "info":
                    return await self._handle_info_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "download":
                    return await self._handle_download_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "rename":
                    return await self._handle_rename_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "describe":
                    return await self._handle_describe_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case "remove":
                    return await self._handle_remove_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case _:
                    raise AssertionError(
                        f"Unknown payload sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()
