from rich import box
from rich.panel import Panel
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
    format_argparse_epilog,
    format_component_life_cycle_state_string_with_color,
)
from consortium.client.utils.printer_utils import console


class ListGeneratorsCommand(BaseCommand):
    name = "list_generators"
    description = (
        "List all created agent generators along with their essential information"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          list_generators
        """,
    )
    group = "Agent Generator Management Commands"

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.environment["rest_api"]
            all_agent_generators = (
                await client_rest_api_connection.get_all_agent_generators()
            )

            table = Table(title="Agent Generators")
            table.add_column("Agent Generator ID")
            table.add_column("Name")
            table.add_column("Agent Generator Build Progress")
            table.add_column("Status")
            for agent_generator in all_agent_generators:
                agent_generator_build_steps_summary = []
                completed_agent_generator_build_steps = 0
                for agent_generator_build_step in agent_generator[
                    "agent_generator_build_steps"
                ]:
                    if agent_generator_build_step["status"]["state"] == "COMPLETED":
                        completed_agent_generator_build_steps += 1

                    agent_generator_build_steps_summary.append(
                        f"{agent_generator_build_step['name']} "
                        f"({
                            format_component_life_cycle_state_string_with_color(
                                state_str=agent_generator_build_step['status']['state']
                            )
                        })",
                    )
                agent_generator_build_steps_summary_string = "\n".join(
                    agent_generator_build_steps_summary,
                )
                table.add_row(
                    agent_generator["agent_generator_id"],
                    agent_generator["name"],
                    Panel(
                        agent_generator_build_steps_summary_string
                        + "\n"
                        + f"{completed_agent_generator_build_steps}/{len(agent_generator['agent_generator_build_steps'])} steps completed",
                        box=box.HEAVY_HEAD,
                        title="Agent Generator Build Progress",
                    ),
                    format_component_life_cycle_state_string_with_color(
                        agent_generator["status"]["state"],
                    ),
                )
            console.print(table, "")
        except SystemExit:
            pass

        return ReturnStatus(type=ReturnStatusType.CONTINUE)
