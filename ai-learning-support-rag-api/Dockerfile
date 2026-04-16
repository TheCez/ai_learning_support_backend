FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --frozen --no-dev

COPY app ./app
RUN mkdir -p /app/data/raw_pdfs

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]