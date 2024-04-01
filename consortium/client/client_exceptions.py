# Client session exceptions.
class AlreadyLoggedInError(Exception):
    pass


class NotLoggedInError(Exception):
    pass


class FailedToLoginError(Exception):
    pass


# Interpreter lexer exceptions.
class IncompleteSingleQuoteError(Exception):
    pass


class IncompleteDoubleQuoteError(Exception):
    pass


class IncompleteEscapeError(Exception):
    pass


# Interpreter command execution exceptions
class InvalidCommandError(Exception):
    pass


class InvalidCommandReturnStatusError(Exception):
    pass
