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
from consortium.client.utils.printer_utils import print_error, print_info


class UseListenerCommand(BaseCommand):
    name = "use_listener"
    description = "Use a listener."
    epilog = format_argparse_epilog(
        """
        Example:
            use_listener 123e4567-e89b-12d3-a456-42661417400  # Use a listener with the listener template with listener template ID 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help="Listener template ID of the listener to use.",
            nargs=1,
        )

    async def run_command(
        self,
        command_context: CommandContext,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(command_context.arguments)

            if (
                parsed_args.listener_template_id[0]
                == command_context.environment["listener_template_id"]
            ):
                print_error("You are already using this listener.")
                return ReturnStatus(
                    type=ClientReturnStatusType.CONTINUE,
                )

            listener_template = await command_context.environment[
                "client_connection"
            ].get_listener_template_by_listener_template_id(
                parsed_args.listener_template_id[0],
            )

            print_info(
                f'Using listener with listener template: "{listener_template["name"]}" '
                f'({listener_template["listener_template_id"]})',
            )

            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.USE_LISTENER,
                    "listener_template_id": listener_template["listener_template_id"],
                    "listener_template_name": listener_template["name"],
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
