from consortium.client.commands.home_interpreter_commands import (
    SessionCommand as SessionHomeInterpreterCommand,
)
from consortium.client.utils.formatter_utils import format_argparse_epilog


class SessionCommand(SessionHomeInterpreterCommand):
    epilog = format_argparse_epilog(
        """
        Examples:
          session connect
          session list
          session interact 123e4567-e89b-12d3-a456-426614174000
          session info 123e4567-e89b-12d3-a456-426614174000
          session rename 123e4567-e89b-12d3-a456-426614174000 "New name"
          session describe 123e4567-e89b-12d3-a456-426614174000 "New description"
          session disconnect 123e4567-e89b-12d3-a456-426614174000

        Notes:
          Every sub-command carries its own help, for example:
            session connect --help
        """,
    )
    # There is no client session being interacted with while disconnected, so every
    # sub-command that takes a client session ID requires it rather than defaulting to
    # the current client session. Only the sub-parsers' arguments differ from the home
    # interpreter's session command, so the sub-commands themselves are handled by the
    # inherited handlers.
    client_session_id_nargs = None
    disconnect_help = "Disconnect a client session by its ID."
    disconnect_client_session_id_help = "ID of the client session to disconnect."
    disconnect_epilog = format_argparse_epilog(
        """
        Examples:
          session disconnect 123e4567-e89b-12d3-a456-426614174000
        """,
    )
    info_help = "Display information for a client session by its ID."
    info_client_session_id_help = "ID of the client session to display information for."
    info_epilog = format_argparse_epilog(
        """
        Examples:
          session info 123e4567-e89b-12d3-a456-426614174000
          session info 123e4567-e89b-12d3-a456-426614174000 -p  # Displays password
        """,
    )
    describe_help = "Set the description of a client session by its ID."
    describe_client_session_id_help = (
        "ID of the client session whose description should be changed."
    )
    describe_epilog = format_argparse_epilog(
        """
        Examples:
          session describe 123e4567-e89b-12d3-a456-426614174000 "New description"
        """,
    )
    rename_help = "Set the name of a client session by its ID."
    rename_client_session_id_help = "ID of the client session to rename."
    rename_epilog = format_argparse_epilog(
        """
        Examples:
          session rename 123e4567-e89b-12d3-a456-426614174000 "New name"
        """,
    )
