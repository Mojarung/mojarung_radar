# RADAR - Financial News Analysis System

## Running with Docker Compose

```bash
docker-compose up --build
```

Access the API at `http://localhost:8000`

Access Adminer (PostgreSQL UI) at `http://localhost:8080`

Access Tabix (ClickHouse UI) at `http://localhost:8081`

Access RabbitMQ Management at `http://localhost:15672` (user: radar_user, password: radar_password)

## Running Locally with uv

### Prerequisites

Ensure PostgreSQL, ClickHouse, and RabbitMQ are running locally.

### Setup

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Run Migrations

```bash
cd src/db
alembic upgrade head
```

### Start API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Worker

```bash
python -m src.workers.news_processor
```

### Send Sample News

```bash
python scripts/mock_parser.py
```

## API Usage

### Analyze News

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"time_window_hours": 24, "top_k": 5}'
```

