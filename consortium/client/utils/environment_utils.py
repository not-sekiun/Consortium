import os
from pathlib import Path, PurePosixPath

from consortium.client.utils.printer_utils import print_info, print_warning

# Set on the image so the client can tell that it is running inside a container. There
# is no portable way to detect this from the inside, so the environment variable is the
# signal. The server has its own copy of this check for its own startup warnings.
RUNNING_IN_DOCKER_ENVIRONMENT_VARIABLE = "RUNNING_IN_DOCKER"
_FALSE_ENVIRONMENT_VARIABLE_VALUES = frozenset({"", "0", "false", "no", "off"})

# Lists every mount visible to the process, one per line, with the mount point itself
# in the fifth field. Linux only, which is all a container running the client can be.
_MOUNT_INFO_FILE_PATH = "/proc/self/mountinfo"
# Mount points containing any of these characters are written escaped in mountinfo.
_MOUNT_INFO_ESCAPES = {"\\040": " ", "\\011": "\t", "\\012": "\n", "\\134": "\\"}


def is_running_in_docker() -> bool:
    value = os.environ.get(RUNNING_IN_DOCKER_ENVIRONMENT_VARIABLE, "")
    return value.strip().lower() not in _FALSE_ENVIRONMENT_VARIABLE_VALUES


def _get_mount_points() -> list[PurePosixPath] | None:
    try:
        with open(_MOUNT_INFO_FILE_PATH) as file:
            mount_info_lines = file.readlines()
    except OSError:
        return None

    mount_points = []
    for line in mount_info_lines:
        fields = line.split(" ")
        if len(fields) < 5:
            continue
        mount_point = fields[4]
        for escape, character in _MOUNT_INFO_ESCAPES.items():
            mount_point = mount_point.replace(escape, character)
        mount_points.append(PurePosixPath(mount_point))

    return mount_points


def is_path_mounted_from_host(path: Path) -> bool | None:
    # Returns None when the answer cannot be determined instead of guessing. Telling a
    # user that a file survives the container when it does not is worse than saying
    # nothing about it at all.
    mount_points = _get_mount_points()
    if mount_points is None:
        return None

    resolved_path = PurePosixPath(path.resolve())
    for mount_point in mount_points:
        # The container's own root filesystem is always a mount point but is thrown
        # away with the container, so it never counts as host backed. Every other entry
        # was mounted in from outside: a bind mount, a named volume, or one of the
        # engine's own injected files.
        if mount_point == PurePosixPath("/"):
            continue
        if resolved_path == mount_point or mount_point in resolved_path.parents:
            return True

    return False


def print_containerized_missing_path_notice(path: Path) -> None:
    # A container only sees the directories mounted into it, so a path that is entirely
    # valid on the host reads back from inside as simply missing. The plain "not found"
    # this follows is true but points at the wrong cause, which sends the user looking
    # for a typo instead of at the container boundary.
    if not is_running_in_docker():
        return

    working_directory = Path.cwd()
    if is_path_mounted_from_host(path=working_directory):
        print_warning(
            f"'{path}' resolved to '{path.resolve()}' inside the container, which can "
            f"only see the directories mounted into it. If this is a path on the host, "
            f"copy it into the directory mounted at '{working_directory}' (./workspace "
            f"on the host under the bundled docker-compose.yml) and upload it from "
            f"there."
        )
        return

    print_warning(
        f"'{path}' resolved to '{path.resolve()}' inside the container, which can only "
        f"see the directories mounted into it. If this is a path on the host, mount the "
        f"directory holding it into the container and upload it from there."
    )


def print_containerized_working_directory_notice() -> None:
    # Uploads and downloads resolve relative paths against the working directory, which
    # inside a container is a container path even though it reads like a host one. That
    # is invisible until a download appears to succeed and the file is nowhere to be
    # found on the host, so it is called out once at startup.
    if not is_running_in_docker():
        return

    working_directory = Path.cwd()
    is_mounted_from_host = is_path_mounted_from_host(path=working_directory)

    match is_mounted_from_host:
        case True:
            print_info(
                f"Running in a container. Downloads without '-o' and relative upload "
                f"paths use '{working_directory}', which is mounted from the host, so "
                f"downloaded files are visible outside the container."
            )
        case False:
            print_warning(
                f"Running in a container. Downloads without '-o' and relative upload "
                f"paths use '{working_directory}', which is not mounted from the host, "
                f"so downloaded files are lost when the container exits. Mount a host "
                f"directory and run the client with it as the working directory (the "
                f"bundled docker-compose.yml does this with ./workspace), or download "
                f"with -o pointing into a directory that is mounted."
            )
        case None:
            print_info(
                f"Running in a container. Downloads without '-o' and relative upload "
                f"paths use '{working_directory}', which is a path inside the "
                f"container, not on the host."
            )
