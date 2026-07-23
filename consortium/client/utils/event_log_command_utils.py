from rich.table import Table

from consortium.client.utils.formatter_utils import (
    format_agent_task_event_type_string_with_color,
    format_datetime_as_human_readable_str,
)


# Shared builder for the event log entries table. Event logs are now attached to tasks,
# listeners, and agent generators alike, so their tabular display is factored out here to
# keep the presentation consistent across every command that renders one.
def create_event_log_table(
    event_log: dict,
    title: str = "Event Log",
) -> Table:
    total_count = event_log["total_count"]
    entries = event_log["entries"]

    event_log_table = Table(
        title=f"{title} (showing {len(entries)} of {total_count} entries)",
        highlight=True,
    )
    event_log_table.add_column("#", justify="right")
    event_log_table.add_column("Status")
    event_log_table.add_column("Message")
    event_log_table.add_column("Datetime Reported")
    for entry in entries:
        event_log_table.add_row(
            str(entry["sequence"]),
            format_agent_task_event_type_string_with_color(
                event_type_str=entry["event_type"]
            ),
            entry["message"],
            format_datetime_as_human_readable_str(
                datetime_str=entry["datetime_reported"],
                include_elapsed_time=True,
            ),
        )

    return event_log_table
