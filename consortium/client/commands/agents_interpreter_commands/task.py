from rich.table import Table

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class TaskCommand(BaseCommand):
    name = "task"
    description = (
        "Task a specific agent with a command and arguments. The task will be "
        "queued and executed by the agent."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
            task 123e4567-e89b-12d3-a456-42661417400  command arg1 arg2
        """,
    )

    def configure_parser(self, parser):
        parser.add_argument(
            "agent_id",
            help="The agent ID of the agent to task.",
            nargs=1,
        )
        parser.add_argument(
            "command",
            help="The command to task the agent with.",
            nargs=1,
        )
        parser.add_argument(
            "arguments",
            help="The arguments to pass to the command.",
            nargs="*",
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)
            client_connection = command_context.environment["client_connection"]

            agent = await client_connection.get_agent_by_agent_id(
                agent_id=parsed_args.agent_id[0],
            )
            task = await client_connection.task_agent_by_agent_id(
                agent_id=parsed_args.agent_id[0],
                command=parsed_args.command[0],
                arguments=parsed_args.arguments,
            )

            print_success(
                f'Tasked agent "{agent["name"]}" ({agent["agent_id"]}) with task ID: '
                f'{task['task_id']}',
            )
        except SystemExit:
            pass
        return ReturnStatus(type=ClientReturnStatusType.CONTINUE)
