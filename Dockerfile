FROM python:3.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /consortium

# Dependency only layer. Stays cached until pyproject.toml or uv.lock change.
# `--frozen` rather than `--locked` is deliberate: the workspace members declared
# in [tool.uv.workspace] have not been copied in yet, so their dependencies drop
# out of the resolution and uv would report the lockfile as needing an update when
# it is in fact current. The sync below, which runs with every member present, is
# the one that verifies the lockfile.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev --no-install-workspace

# The uv workspace members live under consortium/components/*, so they can only
# be installed once the package tree has been copied in. `--all-packages` is what
# installs their own dependencies: a plain sync from the workspace root resolves
# the whole workspace but only installs the root project, which leaves components
# failing to load at runtime on a missing third-party dependency.
COPY consortium/ consortium/
RUN uv sync --locked --no-cache --no-dev --all-packages

FROM python:3.14-slim-bookworm AS runtime

# uv is a runtime dependency, not just a build tool. The server runs a component
# dependency pre-flight sync on startup which aborts if uv is not on PATH.
COPY --from=builder /bin/uv /bin/uv

# Agent generators that compile their payloads inside a container shell out to
# `docker` and refuse to start when the binary is missing from PATH. Only the
# client is installed, never an engine: it drives whatever DOCKER_HOST points at,
# which under compose is a sidecar engine. The cli-plugins directory carries
# buildx, which the client needs to build against engines where the classic
# builder is unavailable.
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:cli /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/

WORKDIR /consortium

COPY --from=builder /consortium /consortium

# The root project is a virtual uv project (uv.lock records
# `source = { virtual = "." }`) so nothing is installed into site-packages. The
# `consortium` package is only importable because running this script places
# /consortium at the front of sys.path, which means the script itself has to be
# in the image.
COPY consortium.py ./

# Copied after the dependency layers so that editing configuration files does
# not invalidate them. Shadowed by the ./data bind mount under compose, this
# copy only serves plain `docker run` invocations with no mount.
COPY data/ data/

# Default mount point for a host directory to exchange files with the client:
# uploads and downloads resolve relative paths against the working directory, so
# compose points the client's working directory here. Created in the image so that
# the directory exists (and is writable) even when nothing is mounted over it.
RUN mkdir -p /consortium/workspace

# The pre-flight sync rewrites pyproject.toml/uv.lock and installs into .venv on
# startup, so the runtime user has to own the project directory. UID 1000 is
# chosen to line up with the usual first non-root host user, which keeps files
# written into the bind mounted data directory owned correctly on Linux hosts.
RUN useradd --create-home --uid 1000 consortium \
    && chown -R consortium:consortium /consortium
USER consortium

# RUNNING_IN_DOCKER lets the server tell that it is containerized, which it cannot
# detect portably on its own. It uses this to check its configured address against the
# container's networking setup on startup and warn about combinations that leave the
# API unreachable from outside the container.
ENV HOME=/home/consortium \
    PATH="/consortium/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    RUNNING_IN_DOCKER=1 \
    UV_CACHE_DIR=/home/consortium/.cache/uv \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

# Absolute so that the entrypoint keeps working when the working directory is
# moved off the project root, which compose does for the client to put it in the
# mounted workspace directory.
ENTRYPOINT ["python", "/consortium/consortium.py"]
CMD ["server"]
