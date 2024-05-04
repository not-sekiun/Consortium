import os
from pathlib import Path


class TemporarilyChangeWorkingDirectory:
    """
    A context manager that temporarily changes the working directory to a new specified
    directory. Used for running commands that require a specific working directory.
    """

    def __init__(self, new_working_directory: str | Path):
        self.new_working_directory = new_working_directory
        self.old_working_directory = None

    def __enter__(self):
        self.old_working_directory = os.getcwd()
        os.chdir(self.new_working_directory)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_working_directory)
