FROM public.ecr.aws/docker/library/python:3.13
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies required for markitdown and its dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV PORT=8000
# Suppress CPU detection warnings in Lambda environment
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1
WORKDIR /var/task

# Enable bytecode compilation
# ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /var/task/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/var/task/.venv/bin:$PATH"

EXPOSE $PORT

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD fastapi run --port=$PORT main.py
