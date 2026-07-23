from argparse import ArgumentParser

from rich.panel import Panel
from rich.table import Table

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.event_log_command_utils import create_event_log_table
from consortium.client.utils.formatter_utils import (
    format_agent_generator_state_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
    format_seconds_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class GeneratorInfoCommand(BaseConnectedCommand):
    name = "info"
    description = "Display information about an agent generator by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
          info 123e4567-e89b-12d3-a456-42661417400 --limit 20  # Show last 20 event log entries (tail)
          info 123e4567-e89b-12d3-a456-42661417400 --offset 0 --limit 5  # Show first 5 event log entries
          info 123e4567-e89b-12d3-a456-42661417400 --offset -5 --limit 10  # Show 10 entries starting from 5th from end
        """,
    )
    group = "Agent Generator Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="ID of the agent generator to display information for.",
            nargs=1,
        )
        parser.add_argument(
            "-l",
            "--limit",
            help=(
                "Maximum number of event log entries to return. "
                "When specified without --offset, returns the last N entries (tail). "
                "Must be a positive integer. Default is 10."
            ),
            type=int,
            default=None,
        )
        parser.add_argument(
            "-o",
            "--offset",
            help=(
                "Starting position in the event log. Positive values start from the "
                "beginning, negative values offset from the end. "
                "If not specified, returns the tail (last N entries based on limit)."
            ),
            type=int,
            default=None,
        )

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent_generator = await rest_api.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
                limit=parsed_args.limit,
                offset=parsed_args.offset,
            )

            # Build steps table
            build_steps_table = Table(
                title="Agent Generator Build Steps Information",
                highlight=True,
            )

            # Define columns (former "Information" rows).
            build_steps_table.add_column("#", justify="right")
            build_steps_table.add_column("Name")
            build_steps_table.add_column("Description")
            build_steps_table.add_column("Status")
            build_steps_table.add_column("Datetime Started")
            build_steps_table.add_column("Elapsed")

            build_steps = agent_generator["agent_generator_build_steps"]

            total_time_elapsed = 0
            for index, build_step in enumerate(build_steps, start=1):
                if build_step["time_elapsed_in_seconds"]:
                    total_time_elapsed += build_step["time_elapsed_in_seconds"]

                build_steps_table.add_row(
                    str(index),
                    build_step["name"],
                    build_step["description"],
                    format_agent_generator_state_string_with_color(
                        build_step["status"]["state"]
                    ),
                    format_datetime_as_human_readable_str(
                        datetime_str=build_step["datetime_started"],
                    )
                    if build_step["datetime_started"]
                    else "",
                    format_seconds_as_human_readable_str(
                        seconds=build_step["time_elapsed_in_seconds"],
                    )
                    if build_step["time_elapsed_in_seconds"] is not None
                    else "",
                )

            # Collate any errored build steps into a dedicated red panel shown at the
            # very bottom. When no build steps errored the panel is omitted entirely.
            errored_build_steps = [
                (build_step_num + 1, build_step)
                for build_step_num, build_step in enumerate(build_steps)
                if build_step["status"]["error"]
            ]
            build_step_errors_panel = None
            if errored_build_steps:
                build_step_errors_string = "\n\n".join(
                    f"[bold white](#{build_step_num}) "
                    f"{build_step['name']}:[/]\n"
                    f"{build_step['status']['error']['message']}"
                    for build_step_num, build_step in errored_build_steps
                )
                build_step_errors_panel = Panel(
                    build_step_errors_string,
                    title="Agent Generator Build Step Errors",
                    title_align="left",
                    expand=False,
                    style="red",
                )

            agent_generator_info_table = Table(
                title="Agent Generator Information", highlight=True
            )
            agent_generator_info_table.add_column("Information")
            agent_generator_info_table.add_column("Data")
            agent_generator_info_table.add_row(
                "Agent Generator ID",
                agent_generator["agent_generator_id"],
            )
            agent_generator_info_table.add_row("Name", agent_generator["name"])
            agent_generator_info_table.add_row(
                "Description", agent_generator["description"]
            )
            agent_generator_info_table.add_row(
                "Agent Type",
                agent_generator["agent_type"]["name"],
            )
            agent_generator_info_table.add_row(
                "Compatible Listener Types",
                format_list_as_multi_line_bulleted_string(
                    input_list=list(agent_generator["compatible_listener_types"]),
                ),
            )
            agent_generator_info_table.add_row(
                "Status",
                format_agent_generator_state_string_with_color(
                    state_str=agent_generator["status"]["state"],
                )
                + (
                    " (" + agent_generator["status"]["error"]["message"] + ")"
                    if agent_generator["status"]["error"]
                    else ""
                ),
            )
            agent_generator_info_table.add_row(
                "Datetime Created",
                format_datetime_as_human_readable_str(
                    datetime_str=agent_generator["datetime_created"],
                    include_elapsed_time=True,
                ),
            )
            agent_generator_info_table.add_row(
                "Datetime Started",
                format_datetime_as_human_readable_str(
                    datetime_str=agent_generator["agent_generator_build_steps"][0][
                        "datetime_started"
                    ],
                    include_elapsed_time=True,
                )
                if agent_generator["agent_generator_build_steps"][0]["datetime_started"]
                else "",
            )
            agent_generator_info_table.add_row(
                "Total Build Time Elapsed",
                format_seconds_as_human_readable_str(
                    seconds=total_time_elapsed,
                ),
            )
            agent_generator_info_table.add_row(
                "Parameters",
                format_dict_as_multi_line_key_value_string(
                    input_dict=agent_generator["parameters"]
                ),
            )
            agent_generator_info_table.add_row(
                "Creating Agent Template",
                f"'{agent_generator['creating_agent_template']['name']}' "
                f"{agent_generator['creating_agent_template']['agent_template_id']}",
            )

            event_log_table = create_event_log_table(
                event_log=agent_generator["event_log"],
                title="Agent Generator Event Log",
            )

            console.print(agent_generator_info_table, "")
            console.print(build_steps_table, "")
            console.print(event_log_table, "")
            if build_step_errors_panel is not None:
                console.print(build_step_errors_panel, "")
        except SystemExit:
            pass

        return ContinueSignal()
