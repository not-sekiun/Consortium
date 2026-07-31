from consortium.client.commands.home_interpreter_commands.client_session import (
    SessionCommand,
)

# Client sessions are created, switched between and torn down from anywhere in the
# client rather than from the home interpreter alone, so this instance of the session
# command is registered as one of the core commands (see `CORE_COMMANDS`).
SESSION_COMMAND = SessionCommand()
