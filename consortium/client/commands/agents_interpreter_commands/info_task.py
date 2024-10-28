from argparse import ArgumentParser

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
    format_agent_task_state_string_with_color,
    format_argparse_epilog,
)
from consortium.client.utils.printer_utils import CONSOLE


class InfoTaskCommand(BaseCommand):
    name = "info_task"
    description = (
        "Display detailed information about a specific agent task for a specific "
        "agent."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            info_task 123e4567-e89b-12d3-a456-42661417400 43e56f0b-c3d2-4c70-82a9-8d27ded2cb2f
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_id",
            help=(
                "The agent ID of the agent to get the information of a particular "
                "task for."
            ),
            type=str,
            nargs=1,
        )
        parser.add_argument(
            "task_id",
            help="The task ID of the task to display detailed information for.",
            type=str,
        )

    @staticmethod
    async def _display_task_info_from_agent_id_and_task_id(
        client_rest_api_connection: "ClientRESTAPIConnection",
        agent_id: str,
        task_id: str,
    ) -> None:
        task = await client_rest_api_connection.get_agent_task_by_agent_id_and_task_id(
            agent_id=agent_id,
            task_id=task_id,
        )

        table = Table(title="Task Information")
        table.add_column("Information")
        table.add_column("Data")
        table.add_row("Task ID", task["task_id"])
        table.add_row("Command", task["command"])
        arguments_table = Table(
            title="Arguments",
        )
        arguments_table.add_column("Argument")
        arguments_table.add_column("Value")
        for argument, value in task["arguments"].items():
            arguments_table.add_row(argument, value)
        table.add_row("Arguments", arguments_table)
        table.add_row("State", format_agent_task_state_string_with_color(task["state"]))
        table.add_row("Datetime Started", task["datetime_started"])

        CONSOLE.print(table)

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_rest_api_connection = command_context.environment[
                "client_rest_api_connection"
            ]
            await self._display_task_info_from_agent_id_and_task_id(
                client_rest_api_connection=client_rest_api_connection,
                agent_id=parsed_args.agent_id[0],
                task_id=parsed_args.task_id,
            )
        except SystemExit:
            pass

        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
