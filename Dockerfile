FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tk libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
COPY scripts/create_web_user.py ./scripts/create_web_user.py
COPY alembic.ini ./
RUN pip install --no-cache-dir .
RUN groupadd --gid 10001 peclaw && useradd --uid 10001 --gid peclaw --no-create-home peclaw \
    && mkdir -p /data/artifacts && chown -R peclaw:peclaw /app /data/artifacts
ENV MPLBACKEND=Agg PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
USER 10001:10001
CMD ["python", "-m", "uvicorn", "pe_claw_web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
