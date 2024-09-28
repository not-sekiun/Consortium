# These are just used for signal passing, maybe find a way to optimize code to get rid
# of them


class UnclosedSingleQuotesError(Exception):
    pass


class UnclosedDoubleQuotesError(Exception):
    pass
