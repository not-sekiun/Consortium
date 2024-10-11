from argparse import ArgumentParser

from consortium.client.objects.client_return_status_objects import (
    ClientReturnStatusType,
    InterpreterType,
)
from consortium.client.repl_framework.base_command import (
    BaseCommand,
    CommandContext,
    ReturnStatus,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info


class UseListenerTemplateCommand(BaseCommand):
    name = "use_listener_template"
    description = "Select a listener template to use to create a new listener."
    epilog = format_argparse_epilog(
        """
        Examples:
          use_listener_template 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help="Listener template ID of the listener template to use.",
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
            listener_template = await client_rest_api_connection.get_listener_template_by_listener_template_id(
                parsed_args.listener_template_id[0],
            )

            print_info(
                f'Using listener template: "{listener_template["name"]}" '
                f"({listener_template["listener_template_id"]})",
            )

            return ReturnStatus(
                type=ClientReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.USE_LISTENER_TEMPLATE_INTERPRETER,
                    "listener_template": listener_template,
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ClientReturnStatusType.CONTINUE,
        )
