from argparse import ArgumentParser

from consortium.client.framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_info


class UseAgentTemplateCommand(BaseCommand):
    name = "use_agent_template"
    description = "Use an agent template to create an agent generator."
    epilog = format_argparse_epilog(
        """
        Examples:
            use_agent_template 123e4567-e89b-12d3-a456-42661417400  # Use an agent template with agent template ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help="Agent template ID of the agent template to use.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            agent_template = await command_context.environment[
                "client_connection"
            ].get_agent_template_by_agent_template_id(
                parsed_args.agent_template_id[0],
            )

            print_info(
                f'Using agent template: '
                f'"{agent_template["name"]}" '
                f'({agent_template["agent_template_id"]})',
            )

            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.USE_GENERATOR,
                    "agent_template_id": agent_template["agent_template_id"],
                    "agent_template_name": agent_template["name"],
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
