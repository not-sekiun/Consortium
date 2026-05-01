from argparse import ArgumentParser

from consortium.client.models.context import Context
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
    SwitchUseAgentTemplateInterpreterSignal,
)
from consortium.client.repl_interface.base_command import (
    BaseCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog
from consortium.client.utils.printer_utils import print_error, print_info


class AgentTemplateUseCommand(BaseCommand):
    name = "use"
    description = "Use an agent template to create a new agent generator by switching to its context"
    epilog = format_argparse_epilog(
        """
        Examples:
          use 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help="ID of the agent template to use.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            rest_api = context.client_session.rest_api
            current_agent_template = context.interpreter_context["agent_template"]

            if (
                parsed_args.agent_template_id[0]
                == current_agent_template["agent_template_id"]
            ):
                print_error(
                    f"Already using agent template: '{current_agent_template['name']}' "
                    f"({current_agent_template['agent_template_id']})",
                )
                return ContinueSignal()

            agent_template = await rest_api.get_agent_template_by_agent_template_id(
                parsed_args.agent_template_id[0],
            )
            print_info(
                f"Using agent template: '{agent_template['name']}' "
                f"({agent_template['agent_template_id']})",
            )
            return SwitchUseAgentTemplateInterpreterSignal(
                agent_template=agent_template,
            )
        except SystemExit:
            pass

        return ContinueSignal()
