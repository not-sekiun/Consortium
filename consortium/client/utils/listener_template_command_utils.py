from rich.table import Table

from consortium.client.client_rest_api import RestAPI
from consortium.client.utils.formatter_utils import (
    format_list_as_multi_line_bulleted_string,
)
from consortium.client.utils.printer_utils import console


async def display_listener_template_info(
    rest_api: RestAPI,
    listener_template_id: str,
) -> None:
    listener_template = await rest_api.get_listener_template_by_listener_template_id(
        listener_template_id=listener_template_id,
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
