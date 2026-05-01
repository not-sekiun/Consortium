from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class GeneratorLaunchCommand(BaseCommand):
    name = "launch"
    description = (
        "Create an agent generator from the current agent template and then start it"
    )
    epilog = format_argparse_epilog(
        """
        Examples:
          launch
        """,
    )
    group = "Agent Generator Management Commands"

    async def run(self, context: Context) -> InterpreterSignal:
        try:
            _ = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            agent_template_id = context.interpreter_context["agent_template"][
                "agent_template_id"
            ]
            agent_template_options = context.interpreter_context["agent_template"][
                "options"
            ]

            agent_template_option_values = {}
            for option_name, option in agent_template_options.items():
                agent_template_option_values[option_name] = option["value"]
            agent_generator = await rest_api.create_agent_generator_through_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
                agent_template_option_values=agent_template_option_values,
            )
            _ = await rest_api.start_agent_generator_by_agent_generator_id(
                agent_generator_id=agent_generator["agent_generator_id"],
            )
            print_success(
                f"Created and started agent generator: '{agent_generator['name']}' ({agent_generator['agent_generator_id']})",
            )
        except SystemExit:
            pass

        return ContinueSignal()
