# ----------------------------------------------------------------------------------
# Stage 0: uv depedency
# ----------------------------------------------------------------------------------
ARG UV_VERSION=0.9
# variable expansion is not supported for --from, so use it as separate stage
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-source

# ----------------------------------------------------------------------------------
# Stage 1: development (dev+prod depedencies and tests)
# ----------------------------------------------------------------------------------
FROM python:3.13-slim-trixie AS development

# Copy uv binary
COPY --from=uv-source /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock* ./ 

# Install all depedencies
RUN uv sync --no-install-project

COPY src src
COPY alembic.ini alembic.ini
COPY alembic alembic
COPY main.py main.py

ENTRYPOINT ["python", "main.py"]

# ----------------------------------------------------------------------------------
# Stage 2: production (minimal image, only prod depedencies)
# ----------------------------------------------------------------------------------
FROM python:3.13-slim-trixie AS production

COPY --from=uv-source /uv /uvx /bin/

# Copy uv binary
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock* ./

# Install everything into /app/.venv
RUN uv sync --frozen --no-dev --no-install-project && \
	# Clean up cache and temporary files to reduce layer size
	rm -rf /root/.cache/uv

COPY src src
COPY alembic.ini alembic.ini
COPY alembic alembic
COPY main.py main.py

ENTRYPOINT ["python", "main.py"]

