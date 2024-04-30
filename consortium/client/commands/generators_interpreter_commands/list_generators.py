from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.printer_utils import CONSOLE
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class ListGeneratorsCommand(BaseCommand):
    name = "list_generators"
    description = "List all generators."
    epilog = argparse_epilog_formatter(
        """
        Example:
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

            table = Table(title="Agent Generators", show_lines=True)

            table.add_column("Agent Generator ID")
            table.add_column("Name")
            table.add_column("Agent Generator Build Progress")
            table.add_column("Status")

            for agent_generator in all_agent_generators:
                agent_generator_status_string = agent_generator["status"]["state"]
                if agent_generator_status_string == "RUNNING":
                    agent_generator_status_string = (
                        f"[bold green]{agent_generator_status_string}"
                    )
                elif agent_generator_status_string == "ERRORED":
                    agent_generator_status_string = (
                        f"[bold red]{agent_generator_status_string}"
                    )

                table.add_row(
                    agent_generator["agent_generator_id"],
                    agent_generator["name"],
                    "\n".join(
                        [
                            {
                                "QUEUED": f"[bold white]QUEUED    {agent_generator_build_step["name"]}",
                                "RUNNING": f"[bold yellow]RUNNING   {agent_generator_build_step["name"]}",
                                "COMPLETED": f"[bold green]COMPLETED {agent_generator_build_step["name"]}",
                                "ERRORED": f"[bold red]ERRORED   {agent_generator_build_step["name"]}",
                                "FATAL": f"[bold red]FATAL     {agent_generator_build_step["name"]}",
                            }[agent_generator_build_step["status"]["state"]]
                            for agent_generator_build_step in agent_generator[
                                "agent_generator_build_steps"
                            ]
                        ],
                    )
                    + "\n"
                    + str(
                        len(
                            [
                                agent_generator_build_step
                                for agent_generator_build_step in agent_generator[
                                    "agent_generator_build_steps"
                                ]
                                if agent_generator_build_step["status"]["state"]
                                == "COMPLETED"
                            ],
                        ),
                    )
                    + "/"
                    + str(len(agent_generator["agent_generator_build_steps"]))
                    + " steps completed",
                    agent_generator_status_string,
                )

            CONSOLE.print(table)
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
