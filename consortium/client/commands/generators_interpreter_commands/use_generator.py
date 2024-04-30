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
from consortium.client.utils.printer_utils import print_info
from consortium.client.utils.string_processing_utils import argparse_epilog_formatter


class UseGeneratorCommand(BaseCommand):
    name = "use_generator"
    description = "Use an agent generator."
    epilog = argparse_epilog_formatter(
        """
        Example:
            use_generator 123e4567-e89b-12d3-a456-42661417400  # Use an agent generator with the agent generator template with agent generator template ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help="Agent template ID of the agent generator to create.",
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
                f'Using agent generator with agent template: '
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
