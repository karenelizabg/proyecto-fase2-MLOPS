FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /usr/local/bin/uv

WORKDIR /app

RUN useradd --system --no-create-home appuser

COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=180
RUN uv sync --locked --no-install-project --no-dev

COPY ingestion/ ./ingestion/
COPY analyzers/ ./analyzers/
COPY policies/ ./policies/
COPY splits/ ./splits/
COPY storage/ ./storage/
COPY presentation/ ./presentation/

ENV PATH="/app/.venv/bin:$PATH"
USER appuser

CMD ["python", "-m", "presentation.main"]
