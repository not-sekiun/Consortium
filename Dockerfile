# Stage 1: Build virtual environment
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /consortium

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-install-project

COPY . .
RUN uv sync --frozen --no-cache

# Stage 2: Clean runtime
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /consortium

COPY --from=builder /consortium/.venv /consortium/.venv
COPY --from=builder /consortium /consortium

ENV PATH="/consortium/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Change this to whatever command runs your CLI tool by default
ENTRYPOINT ["uv", "run", "consortium.py"]
