from argparse import ArgumentParser

from rich.table import Table

from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import (
    format_agent_generator_state_string_with_color,
    format_argparse_epilog,
    format_datetime_as_human_readable_str,
    format_dict_as_multi_line_key_value_string,
    format_list_as_multi_line_bulleted_string,
    format_seconds_as_human_readable_str,
)
from consortium.client.utils.printer_utils import console


class GeneratorInfoCommand(BaseCommand):
    name = "info"
    description = "Display information about an agent generator by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          info 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Generator Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="ID of the agent generator to display information for.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent_generator = await rest_api.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )

            # Build steps table
            build_steps_table = Table(
                title="Agent Generator Build Steps Information",
                highlight=True,
            )

            # Define columns (former "Information" rows)
            build_steps_table.add_column("#", justify="right")
            build_steps_table.add_column("Build Step ID", no_wrap=True)
            build_steps_table.add_column("Name")
            build_steps_table.add_column("Description")
            build_steps_table.add_column("Status")
            build_steps_table.add_column("Datetime Started")
            build_steps_table.add_column("Elapsed")

            total_time_elapsed = 0
            for index, build_step in enumerate(
                agent_generator["agent_generator_build_steps"],
                start=1,
            ):
                if build_step["time_elapsed_in_seconds"]:
                    total_time_elapsed += build_step["time_elapsed_in_seconds"]

                build_steps_table.add_row(
                    str(index),
                    build_step["agent_generator_build_step_id"],
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

            console.print(agent_generator_info_table, "")
            console.print(build_steps_table, "")
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
