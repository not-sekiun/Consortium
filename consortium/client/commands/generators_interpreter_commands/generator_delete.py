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


class GeneratorDeleteCommand(BaseConnectedCommand):
    name = "delete"
    description = "Delete a non-running agent generator by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          delete 123e4567-e89b-12d3-a456-426614174000
        """,
    )
    group = "Agent Generator Management Commands"
    autocompletes = Autocomplete.AGENT_GENERATOR_ID

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="ID of the agent generator to delete.",
            nargs=1,
        )

    async def run(self, context: ConnectedContext) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # If agent generator does not exist, a RESTAPIError is raised and caught by
            # the outer try-except block
            agent_generator = await rest_api.get_agent_generator_by_agent_generator_id(
                parsed_args.agent_generator_id[0],
            )
            _ = await rest_api.delete_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )
            print_success(
                f"Deleted agent generator: '{agent_generator['name']}' "
                f"({agent_generator['agent_generator_id']})",
            )
        except SystemExit:
            pass

        return ContinueSignal()
