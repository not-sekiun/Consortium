from argparse import Namespace

from consortium.client.commands.listeners_interpreter_commands import (
    ListenerTemplateCommand as ListenersInterpreterListenerTemplateCommand,
)
from consortium.client.models.context_models import ConnectedContext
from consortium.client.utils.formatter_utils import format_argparse_epilog


# Only the `info` sub-parser's arguments differ from the listeners interpreter's
# template command, so the sub-commands themselves are handled by the inherited
# handlers.
class ListenerTemplateCommand(ListenersInterpreterListenerTemplateCommand):
    epilog = format_argparse_epilog(
        """
        Examples:
          template list
          template info
          template info 123e4567-e89b-12d3-a456-42661417400

        Notes:
          Every sub-command carries its own help, for example:
            template info --help
        """,
    )
    # A listener template is already being used in this interpreter, so the sub-commands
    # that take a listener template ID fall back to it rather than requiring one.
    listener_template_id_nargs = "?"
    info_help = (
        "Display information about the current listener template, or about a specific "
        "listener template by its ID."
    )
    info_listener_template_id_help = (
        "ID of the listener template to display information for (defaults to the "
        "current listener template if not provided)."
    )
    info_epilog = format_argparse_epilog(
        """
        Examples:
          template info  # Displays detailed information for the currently selected listener template being used if the listener template ID is not specified.
          template info 123e4567-e89b-12d3-a456-42661417400
        """,
    )

    # Information about the current listener template is always retrieved from the
    # server rather than from the cached info because a new agent profile may have been
    # loaded or removed, causing the registered compatible agent types information to be
    # stale
    @staticmethod
    def _resolve_listener_template_id(
        parsed_args: Namespace,
        context: ConnectedContext,
    ) -> str:
        if parsed_args.listener_template_id is not None:
            return parsed_args.listener_template_id
        return context.interpreter_context.listener_template["listener_template_id"]
