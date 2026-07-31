import hashlib
import re
import shutil
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from consortium.framework.signal_exceptions._component_signal_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
)
from consortium.framework.utils.path_utils import unique_path
from consortium.framework.utils.shell_utils import run_command

_IMAGE_TAG_PREFIX = "consortium-builder"
_DISALLOWED_IMAGE_TAG_CHARACTERS = re.compile(r"[^a-z0-9._-]")


class ContainerRuntimeUnavailableError(ComponentStartError):
    """Raised when no usable container runtime can be reached.

    Subclasses ComponentStartError, so raising it from a component's start hook
    aborts the start with a clean, client-facing error rather than an unhandled
    traceback.
    """


class ContainerBuildError(ComponentRuntimeError):
    """Raised when a containerized build fails.

    Subclasses ComponentRuntimeError, so raising it from an agent generator build
    step, a listener, or a plugin surfaces as that component's own runtime error
    without the caller needing to catch and re-raise it.
    """


def _sanitize_image_tag_fragment(fragment: str) -> str:
    return _DISALLOWED_IMAGE_TAG_CHARACTERS.sub("-", fragment.lower()).strip("-.")


def _default_image_tag(context_directory: Path) -> str:
    # Derived from the absolute context path rather than just its name so that two
    # components with identically named source directories cannot collide on one
    # shared engine. It is stable across builds, which keeps the image layer cache
    # warm instead of leaving a trail of dangling tags.
    digest = hashlib.sha256(str(context_directory).encode()).hexdigest()[:8]
    return f"{_IMAGE_TAG_PREFIX}-{_sanitize_image_tag_fragment(context_directory.name)}-{digest}"


async def _run_or_raise(command: list[str], description: str) -> None:
    output = await run_command(*command)
    if output.return_code == 0:
        return

    combined_output = "\n".join(part for part in (output.stdout, output.stderr) if part)
    raise ContainerBuildError(
        f"Failed to {description}. Command '{' '.join(command)}' exited with code "
        f"{output.return_code}:\n{combined_output}",
        detail={
            "command": command,
            "exit_code": output.return_code,
            "output": combined_output,
        },
    )


async def ensure_container_runtime_available() -> None:
    """Verify that a container runtime is installed and reachable.

    Call this from a component's start hook so the component refuses to start on a
    machine that cannot build, instead of failing partway through a build.

    Raises:
        ContainerRuntimeUnavailableError: If the docker client is not on the system
            path, or no engine is currently reachable through it.
    """
    if shutil.which("docker") is None:
        raise ContainerRuntimeUnavailableError(
            "Docker is not installed or not found on the system path. Hint: Check "
            "https://docs.docker.com/get-started/get-docker/ for installing docker"
        )

    output = await run_command("docker", "info")
    if output.return_code != 0:
        raise ContainerRuntimeUnavailableError(
            "The Docker engine is not currently running or accessible. Hint: Start "
            "the Docker service on Linux or launch Docker Desktop if on "
            "Windows/MacOS",
            detail={"output": "\n".join((output.stdout, output.stderr)).strip()},
        )


async def build_container_image(
    context_directory: str | Path,
    *,
    dockerfile: str | Path | None = None,
    image_tag: str | None = None,
) -> str:
    """Build a container image from a directory and return its tag.

    Args:
        context_directory: Directory sent to the engine as the build context. Its
            Dockerfile is used unless dockerfile is given.
        dockerfile: Dockerfile to build with, when it does not sit at the root of
            the build context.
        image_tag: Tag to apply. Defaults to a stable tag derived from the context
            directory, which keeps the layer cache warm across builds and cannot
            collide with another component's image.

    Returns:
        The tag the image was built under, to be passed to
        build_artifact_in_container.

    Raises:
        ContainerBuildError: If the image fails to build.
    """
    resolved_context_directory = Path(context_directory).resolve()
    resolved_image_tag = image_tag or _default_image_tag(resolved_context_directory)

    command = ["docker", "build", "--tag", resolved_image_tag]
    if dockerfile is not None:
        command += ["--file", str(Path(dockerfile).resolve())]
    command.append(str(resolved_context_directory))

    await _run_or_raise(command, "build the container image")
    return resolved_image_tag


async def build_artifact_in_container(
    *,
    image_tag: str,
    command: Sequence[str],
    artifact_path: str | PurePosixPath,
    output_directory: str | Path,
    output_name: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path:
    """Run a build command in a throwaway container and retrieve the file it produces.

    The artifact is copied out of the container rather than shared through a mounted
    directory. Mounts are resolved by the engine, which is not necessarily the
    machine this code runs on: when the server itself runs in a container against a
    mounted docker socket, a mount of a local path silently resolves to an empty
    directory on the engine's filesystem. Copying keeps the build identical whether
    the engine is local, remote, or the host's engine seen from inside a container.

    The container is always removed, including when the build command fails or the
    surrounding task is cancelled.

    Args:
        image_tag: Image to run, as returned by build_container_image.
        command: Command and arguments to execute inside the container.
        artifact_path: Absolute path of the file to retrieve, inside the container.
        output_directory: Directory on this machine to place the retrieved file in.
        output_name: Filename to save the artifact under. Defaults to a per-build
            name, so that concurrent builds cannot overwrite each other's output.
        environment: Environment variables to set inside the container. This is the
            supported way to vary a build (compiler targets, feature flags), since
            the same image is reused across builds.

    Returns:
        Path of the retrieved artifact. The caller owns the file and is responsible
        for moving or deleting it.

    Raises:
        ContainerBuildError: If the build command fails, or the artifact cannot be
            retrieved from the container.
    """
    build_id = uuid.uuid4()
    container_name = f"{_IMAGE_TAG_PREFIX}-{build_id}"
    artifact_name = PurePosixPath(artifact_path).name
    output_path = unique_path(
        Path(output_directory).resolve()
        / (output_name or f"{artifact_name}-{build_id}")
    )

    run_container_command = ["docker", "run", "--name", container_name]
    for key, value in (environment or {}).items():
        run_container_command += ["--env", f"{key}={value}"]
    run_container_command.append(image_tag)
    run_container_command += list(command)

    try:
        await _run_or_raise(
            run_container_command, "run the build command inside the container"
        )
        await _run_or_raise(
            ["docker", "cp", f"{container_name}:{artifact_path}", str(output_path)],
            "copy the built artifact out of the container",
        )
    except BaseException:
        # Output names are never reused, so a half written artifact left by a failed
        # copy would linger instead of being overwritten by the next build.
        output_path.unlink(missing_ok=True)
        raise
    finally:
        # Best effort. The container is disposable, and a removal failure must not
        # replace the build error that is already on its way out.
        await run_command("docker", "rm", "--force", container_name)

    return output_path
