from argparse import ArgumentParser

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import (
    format_agent_status_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
    format_list_as_single_line_comma_separated_string,
    format_mitre_attack_technique,
)
from consortium.client.utils.printer_utils import console


class AgentInfoCommand(BaseCommand):
    name = "info"
    description = "Display information about an agent by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
          info 123e4567-e89b-12d3-a456-42661417400 -v
        """,
    )
    group = "Agent Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help="ID of the agent to display information for.",
            nargs=1,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            help=(
                "Display verbose information about the agent, including detailed agent "
                "capability information."
            ),
            action="store_true",
        )

    @staticmethod
    async def _display_agent_info(
        rest_api: RestAPI,
        agent_id: str,
        verbose: bool,
    ) -> None:
        agent = await rest_api.get_agent_by_agent_id(
            agent_id=agent_id,
        )
        agent_info_table = Table(title="Agent Information", highlight=True)
        agent_info_table.add_column("Information")
        agent_info_table.add_column("Data")
        agent_info_table.add_row(
            "Agent ID",
            agent["agent_id"],
        )
        agent_info_table.add_row("Name", str(agent["name"]))
        agent_info_table.add_row("Description", str(agent["description"]))
        agent_info_table.add_row("Endpoint", str(agent["endpoint"]))
        agent_info_table.add_row("Agent Type", str(agent["agent_type"]["name"]))
        agent_info_table.add_row(
            "Agent Capabilities",
            format_dict_as_multi_line_key_value_string(
                input_dict={
                    name: capability["description"]
                    for name, capability in agent["agent_type"][
                        "agent_capabilities"
                    ].items()
                },
                display_value_as_repr=False,
            ),
        )
        agent_info_table.add_row("User", str(agent["user"]))
        agent_info_table.add_row("Running As Admin", str(agent["is_admin"]))
        agent_info_table.add_row("Operating System", str(agent["os"]))
        agent_info_table.add_row("System Version", str(agent["version"]))
        agent_info_table.add_row("System Arch", str(agent["arch"]))
        agent_info_table.add_row("Process ID", str(agent["pid"]))
        agent_info_table.add_row("System Locale", str(agent["locale"]))
        agent_info_table.add_row(
            "Remote Host Address", str(agent["remote_host_address"])
        )
        agent_info_table.add_row("Local Host Address", str(agent["local_host_address"]))
        agent_info_table.add_row(
            "First Checked In",
            format_datetime_as_human_readable_str(
                datetime_str=agent["datetime_first_checked_in"],
                include_elapsed_time=True,
            ),
        )
        agent_info_table.add_row(
            "Last Checked In",
            format_datetime_as_human_readable_str(
                datetime_str=agent["datetime_last_checked_in"],
                include_elapsed_time=True,
            ),
        )
        if agent["status"] == "ORPHANED":
            hint = " [bold magenta](This agent's listener is not currently running. It may reconnect when the listener becomes available)."
        elif agent["status"] == "UNREACHABLE":
            hint = " [bold red](This agent's listener has been deleted. It will no longer be able to check in)."
        else:
            hint = ""
        agent_info_table.add_row(
            "Status",
            format_agent_status_string_with_color(
                status_str=agent["status"],
            )
            + hint,
        )
        agent_info_table.add_row(
            "Connected Listener",
            f"'{agent['connected_listener']['name']}' ({agent['connected_listener']['listener_id']})"
            if agent["connected_listener"] is not None
            else None,
        )
        agent_info_table.add_row(
            "Agent Data",
            format_dict_as_multi_line_key_value_string(agent["agent_data"]),
        )
        console.print(agent_info_table, "")

        if verbose:
            agent_capabilities_info_table = Table(
                title="Agent Capabilities Information", highlight=True
            )
            agent_capabilities_info_table.add_column("Name")
            agent_capabilities_info_table.add_column("Description")
            agent_capabilities_info_table.add_column("Admin")
            agent_capabilities_info_table.add_column("Supported OSes")
            agent_capabilities_info_table.add_column("MITRE ATT&CK Techniques")
            sorted_agent_capabilities = dict(
                sorted(
                    agent["agent_type"]["agent_capabilities"].items(),
                )
            )
            for capability_name, capability in sorted_agent_capabilities.items():
                agent_capabilities_info_table.add_row(
                    capability_name,
                    capability["description"],
                    str(capability["requires_admin"]),
                    format_list_as_single_line_comma_separated_string(
                        capability["supported_oses"]
                    ),
                    format_list_as_multi_line_bulleted_string(
                        list(
                            map(
                                format_mitre_attack_technique,
                                capability["mitre_attack_techniques"],
                            )
                        )
                    )
                    if capability["mitre_attack_techniques"]
                    else "[dim white]N/A[/]",
                )
            console.print(agent_capabilities_info_table, "")

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            await self._display_agent_info(
                rest_api=rest_api,
                agent_id=parsed_args.agent_id[0],
                verbose=parsed_args.verbose,
            )
        except SystemExit:
            pass

        return ContinueSignal()
