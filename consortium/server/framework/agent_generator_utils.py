# some of the utils in this file are wrappers around the shutil and os modules and may
# seem redundant because they are not providing any sort of additional functionality
# beyond just calling the function, however they are used to provide a consistent
# utility interface for the agent generation process, specifically for those who are not
# familiar with python
import asyncio
import os
import shutil
from collections import namedtuple


async def run_command(cmd: str, shell: str | None = None) -> namedtuple:
    """
    Run a command in a subprocess shell and return the stdout, stderr and return code.
    Most commonly used to run compilers to generate binary agents
    """
    proc = await asyncio.create_subprocess_shell(
        cmd=cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
        executable=shell,
    )
    stdout, stderr = await proc.communicate()
    return_code = proc.returncode
    return namedtuple("run_command_result", ["stdout", "stderr", "return_code"])(
        stdout,
        stderr,
        return_code,
    )


def search_and_replace_in_file(
    search_string: str,
    replacement_string: str,
    filepath: str,
    count: int = 1,
) -> None:
    """
    Search for a string in a file and replace it with another string, writing the
    changes to disk. Most commonly used to replace placeholder values in your agent's
    source code with values that are generated at runtime before compilation or to be
    outputted as executable oneliner commands or scripts
    """
    with open(filepath, "r") as file:
        filedata = file.read()
    if search_string not in filedata:
        raise ValueError(f"Search string {search_string} not found in file {filepath}")
    filedata = filedata.replace(search_string, replacement_string, count)
    with open(filepath, "w") as file:
        file.write(filedata)


def copy(source_path: str, destination_path: str) -> None:
    """
    Copy a file, an empty directory or a directory of files and directories to another
    directory. Most commonly used to copy the agent's source code to a temporary
    directory for modification before compilation
    """
    if os.path.isdir(source_path):
        shutil.copytree(source_path, destination_path)
    else:
        shutil.copy(source_path, destination_path)


def move(source_path: str, destination_path: str) -> None:
    """
    Move a file, an empty directory or a directory of files and directories to another
    directory. Most commonly used to move the agent's source code to a temporary
    directory for modification before compilation
    """
    shutil.move(source_path, destination_path)


def remove(path: str) -> None:
    """
    Remove a file or an empty directory. Most commonly used to remove temporary files
    and directories after compilation. Removal happens recursively
    """
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def write_file(
    filepath: str,
    data: str | bytes,
    binary: bool = False,
    create_dir_if_non_existent: bool = False,
) -> None:
    """
    Write string or binary data to a file. If the filepath does not exist, optionally
    create the directory path before writing the file. Most commonly used to write
    manually modified agent source code to disk from memory.
    """
    if create_dir_if_non_existent:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if binary:
        with open(filepath, "wb") as file:
            file.write(data)
        return
    with open(filepath, "w") as file:
        file.write(data)


def read_file(filepath: str, binary: bool = False) -> str | bytes:
    """
    Read string or binary data from a file. Most commonly used to read the agent's
    source code from a temporary directory after modification before compilation.
    Particularly useful for creating oneliner commands for agents
    """
    if binary:
        with open(filepath, "rb") as file:
            return file.read()
    with open(filepath, "r") as file:
        return file.read()


def tool_exists(tool_name: str) -> bool:
    """
    Check if a tool exists on the system. Most commonly used to check if a compiler is
    installed on the system before compilation, in particular it checks if the tool is
    in the system's PATH distinguishing it from path_exists which does not
    """
    return shutil.which(tool_name) is not None


def path_exists(path: str) -> bool:
    """
    Check if a path exists on the system. Most commonly used to check if a file or
    directory exists before compilation
    """
    return os.path.exists(path)
