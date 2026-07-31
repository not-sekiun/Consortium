from math import floor
from typing import Any

from rich.table import Table

from consortium.client.utils.formatter_utils import (
    format_agent_generator_state_string_with_color,
)
from consortium.client.utils.printer_utils import console


def display_all_agent_generators(
    all_agent_generators: list[dict[str, Any]],
) -> None:
    table = Table(title="Agent Generators", highlight=True)
    table.add_column("Agent Generator ID")
    table.add_column("Agent Type")
    table.add_column("Name")
    table.add_column("Build Progress")
    table.add_column("Status")

    progress_bar_length = 10
    empty_chr = "░"
    full_chr = "█"

    for agent_generator in all_agent_generators:
        total_build_steps = len(agent_generator["agent_generator_build_steps"])

        # Handle agent generator having an empty list of build steps edge case
        if total_build_steps == 0:
            table.add_row(
                agent_generator["agent_generator_id"],
                agent_generator["agent_type"]["name"],
                agent_generator["name"],
                f"[{progress_bar_length * empty_chr}] 0/0: N/A (N/A)",
                format_agent_generator_state_string_with_color(
                    agent_generator["status"]["state"]
                ),
            )
            continue

        completed_build_steps = 0
        current_build_step = agent_generator["agent_generator_build_steps"][0]
        for build_step in agent_generator["agent_generator_build_steps"]:
            current_build_step = build_step
            if build_step["status"]["state"] == "COMPLETED":
                completed_build_steps += 1
            else:
                break  # Stop counting at the first non-completed step
        filled = floor(completed_build_steps / total_build_steps * progress_bar_length)
        progress_bar_str = (
            "[" + (full_chr * filled + empty_chr * (progress_bar_length - filled)) + "]"
        )
        # Cap at total so the last completed step shows N/N, not (N+1)/N
        current_step_display = min(completed_build_steps + 1, total_build_steps)
        table.add_row(
            agent_generator["agent_generator_id"],
            agent_generator["agent_type"]["name"],
            agent_generator["name"],
            f"{progress_bar_str} "
            f"{current_step_display}/{total_build_steps}: "
            f"{current_build_step['name']} "
            f"({format_agent_generator_state_string_with_color(current_build_step['status']['state'])})",
            format_agent_generator_state_string_with_color(
                agent_generator["status"]["state"],
            ),
        )
    console.print(table, "")
