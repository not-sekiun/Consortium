from argparse import ArgumentParser

from consortium.client.models.return_status_models import (
    InterpreterType,
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info


class ListenerTemplateUseCommand(BaseCommand):
    name = "use"
    description = (
        "Use a listener template to create a new listener by switching to its context"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          use 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Listener Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "listener_template_id",
            help="ID of the listener template to use.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            current_listener_template = context.environment["listener_template"]

            if (
                parsed_args.listener_template_id[0]
                == current_listener_template["listener_template_id"]
            ):
                print_error(
                    f"Already using listener template '{current_listener_template['name']}' "
                    f"({current_listener_template['listener_template_id']})",
                )
                return ReturnStatus(
                    type=ReturnStatusType.CONTINUE,
                )

            listener_template = (
                await rest_api.get_listener_template_by_listener_template_id(
                    parsed_args.listener_template_id[0],
                )
            )
            print_info(
                f"Using listener template '{listener_template['name']}' "
                f"({listener_template['listener_template_id']})",
            )
            return ReturnStatus(
                type=ReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.USE_LISTENER_TEMPLATE_INTERPRETER,
                    "listener_template": listener_template,
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
