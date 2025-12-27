from consortium.client.models.return_status_models import (
    ReturnStatus,
    ReturnStatusType,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
    Context,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class ListenerLaunchCommand(BaseCommand):
    name = "launch"
    description = (
        "Create a listener from the current listener template and then start it"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          launch
        """,
    )
    group = "Listener Management Commands"

    async def run(self, context: Context) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            listener_template_id = context.environment["listener_template"][
                "listener_template_id"
            ]
            listener_template_options = context.environment["listener_template"][
                "options"
            ]

            listener_template_option_values = {}
            for option_name, option in listener_template_options.items():
                listener_template_option_values[option_name] = option["value"]
            listener = await rest_api.create_listener_through_listener_template_by_listener_template_id(
                listener_template_id=listener_template_id,
                listener_template_option_values=listener_template_option_values,
            )
            _ = await rest_api.start_listener_by_listener_id(
                listener_id=listener["listener_id"],
            )
            print_success(
                f"Created and started listener '{listener['name']}' ({listener['listener_id']})",
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
