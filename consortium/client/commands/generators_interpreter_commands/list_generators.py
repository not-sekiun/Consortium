from rich import box
from rich.panel import Panel
from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import (
    format_agent_generator_state_string_with_color,
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import CONSOLE


class ListGeneratorsCommand(BaseCommand):
    name = "list_generators"
    description = "List all generators."
    epilog = format_argparse_epilog(
        """
        Examples:
            list_generators  # List all agent generators
        """,
    )

    def configure_parser(self, parser) -> None:
        pass

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(command_context.arguments)
            all_agent_generators = await command_context.environment[
                "client_connection"
            ].get_all_agent_generators()

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
                        {
                            "QUEUED": f"[bold white]QUEUED    [/]{agent_generator_build_step["name"]}",
                            "RUNNING": f"[bold yellow]RUNNING   [/]{agent_generator_build_step["name"]}",
                            "COMPLETED": f"[bold green]COMPLETED [/]{agent_generator_build_step["name"]}",
                            "ERRORED": f"[bold red]ERRORED   [/]{agent_generator_build_step["name"]}",
                            "FATAL": f"[bold red]FATAL     [/]{agent_generator_build_step["name"]}",
                        }[agent_generator_build_step["status"]["state"]],
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
                    format_agent_generator_state_string_with_color(
                        agent_generator["status"]["state"],
                    ),
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
