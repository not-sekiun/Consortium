from typing import Any

from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.utils.formatter_utils import (
    format_agent_status_string_with_color,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
    format_list_as_single_line_comma_separated_string,
    format_mitre_attack_technique,
)
from consortium.client.utils.printer_utils import console, print_success


async def describe_agent(
    rest_api: RestAPI,
    agent_id: str,
    description: str,
) -> None:
    agent = await rest_api.get_agent_by_agent_id(
        agent_id=agent_id,
    )
    await rest_api.update_agent_by_agent_id(
        agent_id=agent_id,
        new_agent_attributes={"description": description},
    )
    print_success(
        f"Updated description of agent '{agent['name']}' ({agent['agent_id']}) "
        f"to '{description}'",
    )


async def rename_agent(
    rest_api: RestAPI,
    agent_id: str,
    name: str,
) -> None:
    agent = await rest_api.get_agent_by_agent_id(
        agent_id=agent_id,
    )
    await rest_api.update_agent_by_agent_id(
        agent_id=agent_id,
        new_agent_attributes={"name": name},
    )
    print_success(f"Renamed agent '{agent['name']}' ({agent['agent_id']}) to '{name}'")


def display_agent_info(
    agent: dict[str, Any],
    verbose: bool,
) -> None:
    # The agent data is passed in already resolved rather than fetched here: callers
    # source it differently (a direct agent lookup for the agent info command, the
    # resolved producing-agent embedded in an artifact for the artifact info command),
    # so this function is purely a renderer over an agent representation.
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
    agent_info_table.add_row("Remote IP", str(agent["remote_ip"]))
    agent_info_table.add_row("Local IP", str(agent["local_ip"]))
    agent_info_table.add_row("Hostname", str(agent["hostname"]))
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
        hint = (
            " [bold magenta](This agent's listener is not currently running. "
            "It may reconnect when the listener becomes available)."
        )
    elif agent["status"] == "UNREACHABLE":
        hint = (
            " [bold red](This agent's listener has been deleted. "
            "It will no longer be able to check in)."
        )
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
        f"'{agent['connected_listener']['name']}' "
        f"({agent['connected_listener']['listener_id']})"
        if agent["connected_listener"] is not None
        else None,
    )
    agent_info_table.add_row(
        "Agent Data",
        format_dict_as_multi_line_key_value_string(agent["agent_data"]),
    )
    console.print(agent_info_table, "")

    if verbose:
        # The capability description is deliberately omitted from the information table
        # and rendered in a dedicated "Agent Capabilities Description" table below it to
        # keep the information table compact.
        agent_capabilities_info_table = Table(
            title="Agent Capabilities Information", highlight=True
        )
        agent_capabilities_info_table.add_column("Name")
        agent_capabilities_info_table.add_column("Admin")
        agent_capabilities_info_table.add_column("Supported OSes")
        agent_capabilities_info_table.add_column("MITRE ATT&CK Techniques")

        agent_capabilities_description_table = Table(
            title="Agent Capabilities Description", highlight=True
        )
        agent_capabilities_description_table.add_column("Name")
        agent_capabilities_description_table.add_column("Description")

        sorted_agent_capabilities = dict(
            sorted(agent["agent_type"]["agent_capabilities"].items())
        )
        for capability_name, capability in sorted_agent_capabilities.items():
            agent_capabilities_info_table.add_row(
                capability_name,
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
            agent_capabilities_description_table.add_row(
                capability_name,
                capability["description"],
            )
        console.print(agent_capabilities_info_table, "")
        console.print(agent_capabilities_description_table, "")
