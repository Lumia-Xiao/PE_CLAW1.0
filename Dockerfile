FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tk libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
RUN pip install --no-cache-dir .
ENV MPLBACKEND=Agg PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
CMD ["python", "-m", "uvicorn", "pe_claw_web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
