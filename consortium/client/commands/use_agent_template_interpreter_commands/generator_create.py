from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class GeneratorCreateCommand(BaseConnectedCommand):
    name = "create"
    description = "Create an agent generator from the current agent template and start it (use --no-start to skip starting)"
    epilog = format_argparse_epilog(
        """
        Examples:
          create
          create --no-start
          create -n
        """,
    )
    group = "Agent Generator Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--no-start",
            "-n",
            help="Create the agent generator without starting it.",
            action="store_true",
            default=False,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            agent_template_id = context.interpreter_context.agent_template[
                "agent_template_id"
            ]
            agent_template_options = context.interpreter_context.agent_template[
                "options"
            ]

            agent_template_option_values = {}
            for option_name, option in agent_template_options.items():
                agent_template_option_values[option_name] = option["value"]
            # The staged name and description are sent separately from the option
            # values: they are the created agent generator's display metadata rather than
            # agent template options. A name of `None` means none was staged through the
            # `rename` command, leaving the server to generate one.
            agent_generator = await rest_api.create_agent_generator_through_agent_template_by_agent_template_id(
                agent_template_id=agent_template_id,
                agent_template_option_values=agent_template_option_values,
                name=context.interpreter_context.agent_generator_name,
                description=context.interpreter_context.agent_generator_description,
            )
            if parsed_args.no_start:
                print_success(
                    f"Created agent generator: '{agent_generator['name']}' ({agent_generator['agent_generator_id']})",
                )
            else:
                _ = await rest_api.start_agent_generator_by_agent_generator_id(
                    agent_generator_id=agent_generator["agent_generator_id"],
                )
                print_success(
                    f"Created and started agent generator: '{agent_generator['name']}' ({agent_generator['agent_generator_id']})",
                )
        except SystemExit:
            pass

        return ContinueSignal()
