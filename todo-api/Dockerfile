FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.1 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY ssot-api/pyproject.toml ssot-api/
COPY todo-api/pyproject.toml todo-api/
RUN uv sync --frozen --no-dev --no-install-workspace --package todo-api
COPY todo-api todo-api
RUN uv sync --frozen --no-dev --package todo-api
ENV PATH=/opt/venv/bin:$PATH
EXPOSE 8010
CMD ["uvicorn", "todo_api.main:app", "--host", "0.0.0.0", "--port", "8010"]
