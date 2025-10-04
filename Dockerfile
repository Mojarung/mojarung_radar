FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using uv
RUN /root/.local/bin/uv pip install --system fastapi>=0.115.0 uvicorn[standard]>=0.32.0 \
    pydantic>=2.9.0 pydantic-settings>=2.6.0 sqlalchemy>=2.0.36 alembic>=1.14.0 \
    psycopg2-binary>=2.9.10 clickhouse-connect>=0.8.8 aio-pika>=9.5.0 \
    faiss-cpu>=1.9.0 polars>=1.12.0 langgraph>=0.2.45 langchain>=0.3.7 \
    langchain-core>=0.3.15 langchain-openai>=0.2.9 loguru>=0.7.2 \
    httpx>=0.28.0 'numpy>=1.26.0,<2.0.0' sentence-transformers>=3.3.1 python-dateutil>=2.9.0 \
    requests>=2.32.0 beautifulsoup4>=4.12.0 lxml>=5.3.0 pandas>=2.2.0 \
    fasttext-wheel>=0.9.2 huggingface-hub>=0.26.0 natasha>=1.6.0 razdel>=0.5.0

# Copy application code
COPY . .

# Create data directory for Faiss index
RUN mkdir -p /app/data

# Set Python path
ENV PYTHONPATH=/app

# Default command (will be overridden in docker-compose)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

