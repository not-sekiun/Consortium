from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter

from consortium.client.models.context_models import ConnectedContext
from consortium.client.models.interpreter_signal_models import (
    ContinueSignal,
    InterpreterSignal,
)
from consortium.client.repl_interface.autocompletes import Autocomplete
from consortium.client.repl_interface.base_command import (
    BaseConnectedCommand,
)
from consortium.client.utils.agent_template_command_utils import (
    display_agent_template_info,
    display_all_agent_templates,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class AgentTemplateCommand(BaseConnectedCommand):
    name = "template"
    description = "Manage agent templates through its sub-commands"
    epilog = format_argparse_epilog(
        """
        Examples:
          template list
          template info 123e4567-e89b-12d3-a456-42661417400

        Notes:
          Every sub-command carries its own help, for example:
            template info --help
        """,
    )
    group = "Agent Template Management Commands"
    autocompletes = {
        "list": None,
        "info": Autocomplete.AGENT_TEMPLATE_ID,
    }
    # Help and examples for every sub-command that takes an agent template ID, declared
    # as class attributes so that the use agent template interpreter's variant of this
    # command can default that ID to the agent template being used without having to
    # redeclare every sub-parser. `agent_template_id_nargs` of `None` is argparse's own
    # default of a single required positional.
    agent_template_id_nargs: str | None = None
    info_help = "Display information about an agent template by its ID."
    info_agent_template_id_help = "ID of the agent template to display information for."
    info_epilog = format_argparse_epilog(
        """
        Examples:
          template info 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(
            help="Available sub-commands", dest="sub_command", required=True
        )

        # list sub-command
        subparsers.add_parser(
            "list",
            help="List all agent templates along with their essential information.",
            formatter_class=RawDescriptionHelpFormatter,
            epilog=format_argparse_epilog(
                """
                Examples:
                  template list
                """,
            ),
        )

        # info sub-command
        parser_info = subparsers.add_parser(
            "info",
            help=self.info_help,
            formatter_class=RawDescriptionHelpFormatter,
            epilog=self.info_epilog,
        )
        parser_info.add_argument(
            "agent_template_id",
            help=self.info_agent_template_id_help,
            nargs=self.agent_template_id_nargs,
            default=None,
        )

    # The agent template ID every sub-command that takes one operates on. The use agent
    # template interpreter's variant of this command overrides this to fall back to the
    # agent template it is scoped to, which this interpreter has no notion of, which is
    # why the ID is required outright here.
    @staticmethod
    def _resolve_agent_template_id(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> str:
        return parsed_args.agent_template_id

    @staticmethod
    async def _handle_list_sub_command(
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        display_all_agent_templates(
            all_agent_templates=await rest_api.get_all_agent_templates(),
        )

        return ContinueSignal()

    async def _handle_info_sub_command(
        self,
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        rest_api = context.client_session.rest_api

        agent_template = await rest_api.get_agent_template_by_agent_template_id(
            agent_template_id=self._resolve_agent_template_id(
                parsed_args=parsed_args,
                context=context,
            ),
        )
        display_agent_template_info(agent_template=agent_template)

        return ContinueSignal()

    async def run(
        self,
        context: ConnectedContext,
    ) -> InterpreterSignal:
        try:
            parsed_args = self.parser.parse_args(context.arguments)

            match parsed_args.sub_command:
                case "list":
                    return await self._handle_list_sub_command(context=context)
                case "info":
                    return await self._handle_info_sub_command(
                        parsed_args=parsed_args,
                        context=context,
                    )
                case _:
                    raise AssertionError(
                        f"Unknown template sub-command '{parsed_args.sub_command}'",
                    )
        except SystemExit:
            pass

        return ContinueSignal()
