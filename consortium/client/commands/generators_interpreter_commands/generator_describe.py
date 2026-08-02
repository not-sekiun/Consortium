from argparse import ArgumentParser

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


# Paired with `rename`: both act on an agent generator that already exists. Giving a
# description to an agent generator that has yet to be created is done through the
# `create` command's -d/--description flag inside an agent template's context.
class GeneratorDescribeCommand(BaseConnectedCommand):
    name = "describe"
    description = "Set the description of an agent generator by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          describe 123e4567-e89b-12d3-a456-426614174000 "New description"
        """,
    )
    group = "Agent Generator Management Commands"
    autocompletes = Autocomplete.AGENT_GENERATOR_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="ID of the agent generator whose description should be changed.",
            nargs=1,
        )
        parser.add_argument(
            "description",
            help="New description for the agent generator.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            agent_generator = await rest_api.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )
            await rest_api.update_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
                new_agent_generator_attributes={
                    "description": parsed_args.description[0],
                },
            )
            print_success(
                f"Updated description of agent generator '{agent_generator['name']}' ({agent_generator['agent_generator_id']}) "
                f"to '{parsed_args.description[0]}'",
            )
        except SystemExit:
            pass

        return ContinueSignal()
