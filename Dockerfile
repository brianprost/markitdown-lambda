FROM public.ecr.aws/docker/library/python:3.13
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.0 /lambda-adapter /opt/extensions/lambda-adapter
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /var/task

# Set environment variables to handle Lambda constraints
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ORT_LOGGING_LEVEL=4 \
    ORT_DISABLE_ALL_LOGS=1 \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false \
    NUMEXPR_MAX_THREADS=1 \
    PYTHONWARNINGS=ignore \
    ONNX_DISABLE_EXCEPTIONS=1 \
    ORT_DISABLE_PYTHON_PACKAGE_PATH_SEARCH=1

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


# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD ["python", "lambda_handler.py"]
