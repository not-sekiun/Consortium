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


class CreateGeneratorCommand(BaseCommand):
    name = "create_generator"
    description = (
        "Create an agent generator with the currently set agent template options."
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          create_generator
        """,
    )
    group = "Agent Generator Management Commands"

    async def run(self, context: Context) -> ReturnStatus:
        try:
            _ = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.environment["rest_api"]
            agent_template_id = context.environment["agent_template"][
                "agent_template_id"
            ]
            agent_template_options = context.environment["agent_template"]["options"]

            agent_template_option_values = {}
            for option_name, option in agent_template_options.items():
                agent_template_option_values[option_name] = option["value"]
            agent_generator = await client_rest_api_connection.create_agent_generator_through_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
                agent_template_option_values=agent_template_option_values,
            )

            print_success(
                f'Created agent generator: "{agent_generator["name"]}" ({agent_generator["agent_generator_id"]})',
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
