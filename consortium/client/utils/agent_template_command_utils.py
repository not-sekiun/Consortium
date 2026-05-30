from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.utils.formatter_utils import (
    format_list_as_multi_line_bulleted_string,
)
from consortium.client.utils.printer_utils import console


async def display_agent_template_info(
    rest_api: RestAPI,
    agent_template_id: str,
) -> None:
    agent_template = await rest_api.get_agent_template_by_agent_template_id(
        agent_template_id=agent_template_id,
    )

    table = Table(title="Agent Template Information", highlight=True)
    table.add_column("Information")
    table.add_column("Data")
    table.add_row(
        "Agent Template ID",
        agent_template["agent_template_id"],
    )
    table.add_row(
        "Label",
        agent_template["label"],
    )
    table.add_row("Name", agent_template["name"])
    table.add_row("Description", agent_template["description"])
    table.add_row("Version", agent_template["version"])
    table.add_row(
        "Compatible Framework Version",
        agent_template["compatible_framework_version"],
    )
    table.add_row(
        "Authors",
        format_list_as_multi_line_bulleted_string(input_list=agent_template["authors"]),
    )
    table.add_row(
        "Agent Type",
        agent_template["agent_type"]["name"],
    )
    table.add_row(
        "Compatible Listener Types",
        format_list_as_multi_line_bulleted_string(
            input_list=list(agent_template["compatible_listener_types"]),
        ),
    )
    console.print(table, "")
