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


class UseAgentTemplateCommand(BaseCommand):
    name = "use_agent_template"
    description = "Select an agent template to use to create a new agent generator."
    epilog = format_argparse_epilog(
        """
        Examples:
          use_agent_template 123e4567-e89b-12d3-a456-42661417400
        """,
    )
    group = "Agent Template Management Commands"

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "agent_template_id",
            help="Agent template ID of the agent template to use.",
            nargs=1,
        )

    async def run(
        self,
        context: Context,
    ) -> ReturnStatus:
        try:
            parsed_args = self.parser.parse_args(context.arguments)
            client_rest_api_connection = context.client_session.rest_api
            currently_used_agent_template = context.interpreter_context[
                "agent_template"
            ]

            if (
                currently_used_agent_template["agent_template_id"]
                == parsed_args.agent_template_id[0]
            ):
                print_error(
                    f"Already using agent template: "
                    f'"{currently_used_agent_template["name"]}" '
                    f"({currently_used_agent_template['agent_template_id']})",
                )
                return ReturnStatus(
                    type=ReturnStatusType.CONTINUE,
                )

            agent_template = await client_rest_api_connection.get_agent_template_by_agent_template_id(
                parsed_args.agent_template_id[0],
            )
            print_info(
                f"Using agent template: "
                f'"{agent_template["name"]}" '
                f"({agent_template['agent_template_id']})",
            )

            return ReturnStatus(
                type=ReturnStatusType.SWITCH_INTERPRETER,
                data={
                    "interpreter_type": InterpreterType.USE_AGENT_TEMPLATE_INTERPRETER,
                    "agent_template": agent_template,
                },
            )
        except SystemExit:
            pass

        return ReturnStatus(
            type=ReturnStatusType.CONTINUE,
        )
