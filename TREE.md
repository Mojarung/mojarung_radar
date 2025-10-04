# RADAR Project Structure

This document explains the organization and purpose of each component in the RADAR project.

## Root Directory

```
/radar-project/
├── .dockerignore          # Files to exclude from Docker builds
├── docker-compose.yml     # Multi-container Docker configuration
├── Dockerfile             # Container image definition
├── pyproject.toml         # Python project dependencies (uv-compatible)
├── README.md              # Quick start guide with launch commands
└── TREE.md                # This file - project structure documentation
```

## Source Code (`src/`)

### Core Module (`src/core/`)

Central configuration and utilities shared across the application.

- `config.py` - Application settings using Pydantic Settings, loads from environment variables
- `logging_config.py` - Loguru configuration for colorful, structured logging

### Database Layer (`src/db/`)

Manages interactions with PostgreSQL and ClickHouse databases.

- `models.py` - SQLAlchemy models for PostgreSQL (Source table)
- `session.py` - PostgreSQL session management and connection pooling
- `clickhouse_client.py` - Client for storing/querying news articles in ClickHouse
- `alembic/` - Database migration scripts
  - `env.py` - Alembic environment configuration
  - `versions/001_initial_migration.py` - Initial schema creation

### Services Layer (`src/services/`)

Business logic and external service integrations.

- `llm_client.py` - Abstract LLM client with OpenRouter implementation (swappable provider)
- `dedup.py` - Faiss-based deduplication using semantic embeddings
- `hotness_scorer.py` - Calculates "hotness" score based on materiality, velocity, breadth, credibility, and unexpectedness

### Agents Layer (`src/agents/`)

LangGraph-based orchestration for the analysis pipeline.

- `graphs.py` - LangGraph workflow definition connecting all processing nodes
- `nodes.py` - Individual node functions:
  1. Fetch recent news from ClickHouse
  2. Cluster articles by dedup_group
  3. Calculate hotness scores
  4. Rank and select top K
  5. Enrich with LLM-generated content (entities, timeline, draft)

### API Layer (`src/api/`)

FastAPI application providing REST endpoints.

- `main.py` - FastAPI app instantiation, middleware, and lifecycle hooks
- `schemas.py` - Pydantic models for request/response validation
- `dependencies.py` - FastAPI dependency injection (database sessions)
- `routers/`
  - `analysis.py` - POST /api/v1/analyze endpoint that triggers the LangGraph pipeline

### Workers (`src/workers/`)

Background processing services.

- `news_processor.py` - RabbitMQ consumer that:
  - Receives incoming news articles
  - Checks for duplicates using Faiss
  - Stores articles in ClickHouse
  - Updates the deduplication index

### Parsers (`src/parsers/`)

News parsing and collection system.

- `base.py` - Abstract base class for all news parsers
- `rbc_parser.py` - РБК (RBC) news parser implementation
- `scheduler.py` - Parser scheduler that:
  - Runs parsers on a configurable schedule (default: every 5 minutes)
  - Prevents duplicate articles by URL checking
  - Sends new articles to RabbitMQ queue
  - Supports multiple concurrent parsers

## Scripts (`scripts/`)

Utility scripts for testing and administration.

- `mock_parser.py` - Sends sample news articles to RabbitMQ for testing the pipeline
- `init_db.py` - Initialize PostgreSQL and ClickHouse databases
- `seed_sources.py` - Seed initial news sources with reputation scores
- `quickstart.py` - Quick initialization script for all setup steps

## Data Flow

1. **Ingestion**: 
   - Parser Scheduler runs every N minutes (configurable)
   - Each parser fetches recent news from its source
   - URL-based deduplication prevents sending duplicates
   - Articles published to RabbitMQ queue
   
2. **Processing**: 
   - Worker consumes messages from RabbitMQ
   - Semantic deduplication using Faiss embeddings
   - Articles stored in ClickHouse with dedup_group
   - Faiss index updated with new article vectors
   
3. **Analysis**: 
   - API endpoint triggered with time window
   - LangGraph agent fetches articles from ClickHouse
   - Clusters grouped by dedup_group
   - Hotness scoring based on multiple factors
   - Top K clusters enriched with LLM
   - Structured results returned to client

## Database Schema

### PostgreSQL (`sources` table)
- Stores news source metadata with reputation scores
- Used for credibility scoring

### ClickHouse (`news_articles` table)
- High-performance storage for large volumes of news articles
- Optimized for time-series queries
- Includes dedup_group for clustering

### Faiss Index
- In-memory/disk-backed vector index for similarity search
- Used for real-time duplicate detection

## Technology Stack

- **Backend**: FastAPI
- **Orchestration**: LangGraph
- **Databases**: PostgreSQL (relational), ClickHouse (columnar)
- **Vector Search**: Faiss
- **Message Queue**: RabbitMQ
- **Data Processing**: Polars
- **LLM Provider**: OpenRouter (configurable)
- **Containerization**: Docker & Docker Compose
- **Python**: 3.12

## Key Design Decisions

1. **LangGraph for Orchestration**: Flexible, graph-based workflow management for complex multi-step analysis
2. **Dual Database Architecture**: PostgreSQL for structured data, ClickHouse for high-volume time-series data
3. **Faiss for Deduplication**: Fast semantic similarity search using embeddings
4. **RabbitMQ Queue**: Decouples ingestion from processing, enables horizontal scaling
5. **Swappable LLM Client**: Abstract base class allows easy provider switching (OpenRouter → OpenAI → local models)
6. **Hotness Scoring**: Multi-factor scoring system balancing multiple dimensions of news importance
7. **Modular Parser Architecture**: Base class pattern allows easy addition of new news sources
8. **Two-Level Deduplication**: URL-based (parser level) + semantic (worker level) for maximum efficiency
9. **Scheduled Parsing**: Automatic periodic news collection with configurable intervals

