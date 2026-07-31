from consortium.client.commands.disconnected_interpreter_commands.client_session import (
    SessionCommand,
)

# The variant of the session command that the disconnected interpreter registers in
# place of the core one, having no client session of its own.
SESSION_COMMAND = SessionCommand()
