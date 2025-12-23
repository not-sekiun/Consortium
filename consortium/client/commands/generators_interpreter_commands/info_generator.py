from argparse import ArgumentParser

from rich.console import Group
from rich.table import Table

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import (
    format_agent_generator_build_step_state_string_with_color,
    format_agent_generator_state_string_with_color,
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import CONSOLE


class InfoGeneratorCommand(BaseCommand):
    name = "info_generator"
    description = "Display detailed information for a specific agent generator."
    epilog = format_argparse_epilog(
        """
        Examples:
          info_generator 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Generator Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help=(
                "Agent generator ID of the agent generator to display detailed "
                "information for."
            ),
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            agent_generator = await client_rest_api_connection.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )

            table = Table(
                title="Agent Generator Information",
            )
            table.add_column("Information")
            table.add_column("Data")
            table.add_row(
                "Agent generator ID",
                agent_generator["agent_generator_id"],
            )
            table.add_row("Name", agent_generator["name"])
            table.add_row("Description", agent_generator["description"])
            agent_generator_build_steps_tables = []
            for index, build_step in enumerate(
                agent_generator["agent_generator_build_steps"],
            ):
                agent_generator_build_step_table = Table(
                    title=f"Agent generator build step {index + 1}",
                )
                agent_generator_build_step_table.add_column("Information")
                agent_generator_build_step_table.add_column("Data")
                agent_generator_build_step_table.add_row(
                    "Agent Generator Build Step ID",
                    build_step["agent_generator_build_step_id"],
                )
                agent_generator_build_step_table.add_row(
                    "Name",
                    build_step["name"],
                )
                agent_generator_build_step_table.add_row(
                    "Description",
                    build_step["description"],
                )
                agent_generator_build_step_table.add_row(
                    "Ignore Failure",
                    str(build_step["ignore_failure"]),
                )
                agent_generator_build_step_table.add_row(
                    "Datetime Started",
                    str(build_step["datetime_started"]),
                )
                agent_generator_build_step_table.add_row(
                    "Datetime Stopped",
                    str(build_step["datetime_stopped"]),
                )
                agent_generator_build_step_table.add_row(
                    "Time Elapsed In Seconds",
                    str(build_step["time_elapsed_in_seconds"]),
                )
                agent_generator_build_step_table.add_row(
                    "Status",
                    format_agent_generator_build_step_state_string_with_color(
                        build_step["status"]["state"],
                    )
                    + (
                        " (" + build_step["status"]["error"]["message"] + ")"
                        if build_step["status"]["error"]
                        else ""
                    ),
                )
                agent_generator_build_steps_tables.append(
                    agent_generator_build_step_table,
                )
            table.add_row(
                "Agent generator build steps",
                Group(*agent_generator_build_steps_tables),
            )
            table.add_row(
                "Agent Type",
                agent_generator["agent_type"]["name"],
            )
            table.add_row(
                "Compatible Listener Types",
                "\n".join(
                    list(agent_generator["compatible_listener_types"]),
                ),
            )
            parameter_table = Table()
            parameter_table.add_column("Parameter")
            parameter_table.add_column("Value")
            for parameter_name, parameter_value in agent_generator[
                "parameters"
            ].items():
                parameter_table.add_row(parameter_name, str(parameter_value))
            table.add_row("Parameters", parameter_table)
            table.add_row(
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
            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
