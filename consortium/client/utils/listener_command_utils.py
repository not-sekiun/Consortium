from typing import Any

from rich.table import Table

from consortium.client.utils.formatter_utils import (
    format_listener_state_string_with_color,
)
from consortium.client.utils.printer_utils import console


def display_all_listeners(all_listeners: list[dict[str, Any]]) -> None:
    table = Table(title="Listeners", highlight=True)
    table.add_column("Listener ID")
    table.add_column("Listener Type")
    table.add_column("Name")
    table.add_column("Endpoint")
    table.add_column("Status")
    for listener in all_listeners:
        table.add_row(
            listener["listener_id"],
            listener["listener_type"]["name"],
            listener["name"],
            listener["endpoint"],
            format_listener_state_string_with_color(
                listener["status"]["state"],
            ),
        )
    console.print(table, "")
