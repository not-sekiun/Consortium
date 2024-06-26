class BaseServiceException(Exception):
    def __init__(self, message: str = "", *args):
        self.message = message
        # The Exception class takes no keyword arguments.
        super().__init__(self.message, *args)
