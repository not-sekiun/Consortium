from argparse import ArgumentParser

from consortium.client.models.context_model import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_success


class GeneratorStartCommand(BaseCommand):
    name = "start"
    description = "Start a non-running agent generator by its ID"
    epilog = format_argparse_epilog(
        """
        Examples:
          start 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Generator Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_generator_id",
            help="ID of the agent generator to start.",
            nargs=1,
        )

    async def run(self, context: Context) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api

            # If agent generator does not exist, a RESTAPIError is raised and caught by
            # the outer try-except block
            agent_generator = await rest_api.get_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )
            _ = await rest_api.start_agent_generator_by_agent_generator_id(
                agent_generator_id=parsed_args.agent_generator_id[0],
            )
            print_success(
                f"Started agent generator: '{agent_generator['name']}' "
                f"({agent_generator['agent_generator_id']})",
            )
        except SystemExit:
            pass

        return ContinueSignal()
