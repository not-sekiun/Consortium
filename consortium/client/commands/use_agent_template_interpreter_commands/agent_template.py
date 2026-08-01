from argparse import Namespace

from consortium.client.commands.generators_interpreter_commands import (
    AgentTemplateCommand as GeneratorsInterpreterAgentTemplateCommand,
)
from consortium.client.models.context_models import ConnectedContext
from consortium.client.utils.formatter_utils import format_argparse_epilog


# Only the `info` sub-parser's arguments differ from the generators interpreter's
# template command, so the sub-commands themselves are handled by the inherited
# handlers.
class AgentTemplateCommand(GeneratorsInterpreterAgentTemplateCommand):
    epilog = format_argparse_epilog(
        """
        Examples:
          template list
          template info
          template info 123e4567-e89b-12d3-a456-426614174000

        Notes:
          Every sub-command carries its own help, for example:
            template info --help
        """,
    )
    # An agent template is already being used in this interpreter, so the sub-commands
    # that take an agent template ID fall back to it rather than requiring one.
    agent_template_id_nargs = "?"
    info_help = (
        "Display information about the current agent template, or about a specific "
        "agent template by its ID."
    )
    info_agent_template_id_help = (
        "ID of the agent template to display information for (defaults to the current "
        "agent template if not provided)."
    )
    info_epilog = format_argparse_epilog(
        """
        Examples:
          template info  # Displays detailed information for the currently selected agent template being used if the agent template ID is not specified.
          template info 123e4567-e89b-12d3-a456-426614174000
        """,
    )

    # Information about the current agent template is always retrieved from the server
    # rather than from the cached info because options may have changed
    @staticmethod
    def _resolve_agent_template_id(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> str:
        if parsed_args.agent_template_id is not None:
            return parsed_args.agent_template_id
        return context.interpreter_context.agent_template["agent_template_id"]
