from rich.table import Table

from consortium.client.utils.formatter_utils import (
    format_agent_task_event_type_string_with_color,
    format_agent_task_status_string_with_color,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
)


def create_task_info_and_task_events_tables(task: dict) -> tuple[Table, Table]:
    task_info_table = Table(title="Task Information", highlight=True)
    task_info_table.add_column("Information")
    task_info_table.add_column("Data")
    task_info_table.add_row("Task ID", task["task_id"])
    task_info_table.add_row("Command", task["command"])
    task_info_table.add_row(
        "Arguments",
        format_dict_as_multi_line_key_value_string(input_dict=task["arguments"]),
    )
    task_info_table.add_row(
        "Status",
        format_agent_task_status_string_with_color(task["status"]["state"])
        + (
            " (" + task["status"]["error"]["message"] + ")"
            if task["status"]["error"]
            else ""
        ),
    )
    task_info_table.add_row(
        "Current Progress",
        f"{task['current_progress']['message']} "
        f"({task['current_progress']['percent_complete']}% complete)"
        if task["current_progress"]
        else "N/A",
    )
    task_info_table.add_row(
        "Datetime Created",
        format_datetime_as_human_readable_str(
            datetime_str=task["datetime_created"], include_elapsed_time=True
        ),
    )
    task_info_table.add_row(
        "Datetime Started",
        format_datetime_as_human_readable_str(
            datetime_str=task["datetime_started"], include_elapsed_time=True
        )
        if task["datetime_started"] is not None
        else "N/A",
    )
    task_info_table.add_row(
        "Datetime Completed",
        format_datetime_as_human_readable_str(
            datetime_str=task["datetime_completed"], include_elapsed_time=True
        )
        if task["datetime_completed"] is not None
        else "N/A",
    )

    events = task["events"]
    total_count = events["total_count"]
    entries = events["entries"]
    task_events_table = Table(
        title=(
            f"Task Events Information (showing {len(entries)} of {total_count} entries)"
        ),
        highlight=True,
    )
    task_events_table.add_column("#", justify="right")
    task_events_table.add_column("Status")
    task_events_table.add_column("Message")
    task_events_table.add_column("Datetime Reported")
    for event in entries:
        task_events_table.add_row(
            str(event["sequence"]),
            format_agent_task_event_type_string_with_color(
                event_type_str=event["event_type"]
            ),
            event["message"],
            # TODO: Remove, events dont have percent complete?
            # f"{event['percent_complete']}%",
            format_datetime_as_human_readable_str(
                datetime_str=event["datetime_reported"],
                include_elapsed_time=True,
            ),
        )

    return task_info_table, task_events_table
