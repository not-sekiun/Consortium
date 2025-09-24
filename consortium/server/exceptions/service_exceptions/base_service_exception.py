class BaseServiceException(Exception):
    """
    Base exception for all service related errors. This exception is meant to be used
    to catch and handle all service related errors.

    Attributes:
        message (str): A human-readable message that describes the error condition that
            occurred.
    """

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)
