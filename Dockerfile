FROM ghcr.io/astral-sh/uv:0.12.11-python3.13-trixie-slim

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project
COPY src/backend src/backend
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["sh", "-c", "python -m backend.dal.generate_data --if-empty && exec uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
