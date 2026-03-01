# MenuLens

Competitive menu pricing intelligence for restaurant operators. Search any dish, see what competitors in your neighborhood charge, and find your pricing sweet spot.

## The Problem

Restaurant owners make pricing decisions blind. They drive around checking competitor menus, browse outdated PDFs, or guess. A restaurant serving 350 customers/day that misprices by $0.75/item loses ~$100K/year. MenuLens fixes this with automated competitor price discovery and benchmarking.

## What It Does

A restaurant owner opens MenuLens, types a dish name (e.g., "Butter Chicken"), and instantly sees:

- **Price statistics** across nearby competitors (median, low, high, range)
- **Your price benchmark** with percentile ranking ("higher than 57% of competitors")
- **Competitor details** for each restaurant: price, Google rating, review count, price tier ($/$$/$$), distance, and a visual price bar relative to the median

The owner walks away knowing exactly where their price sits in the local market and whether there's room to adjust.

## Current State

**MVP (v0.1)** with seeded demo data for 12 Indian restaurants in the SF Bay Area, covering 13 canonical dishes. The extraction pipeline is functional with a local LFM2-8B-A1B model. 67 tests passing.

### What Works Today

- Dish search with autocomplete across 13 dishes
- Neighborhood price comparison with configurable radius (5/10/15/25 mi)
- Stats dashboard (median, p25, p75, low, high)
- Your-price benchmarking with percentile and actionable insight
- Competitor cards with ratings, price tiers, distance, price bars
- LLM-based menu extraction pipeline (text -> structured menu data)
- Dual-model strategy: local LFM2-8B-A1B (primary) + Claude API (fallback)
- Confidence scoring for extraction quality

### What's Next

- Google Maps restaurant discovery (API integration built, needs API key)
- Live menu fetching (HTML + PDF fetchers implemented)
- Dish name normalization via embeddings (taxonomy + matcher built)
- PostgreSQL + PostGIS for persistent storage and geospatial queries
- Price change monitoring and alerts

## Architecture

```
                    Frontend (React + Vite)
                    localhost:5173
                          |
                     /api proxy
                          |
                    FastAPI Backend
                    localhost:8000
                   /      |       \
                  /       |        \
           Demo API   Extract API   Compare API
           (seeded)   (LLM pipeline) (DB queries)
                          |
                    Model Client
                   /            \
          llama-server       Claude API
          (LFM2-8B-A1B)     (fallback)
          localhost:8081
```

### Backend Pipeline (6 stages)

```
Discovery -> Fetching -> Extraction -> Normalization -> Storage -> Intelligence
   |            |            |              |              |            |
Google Maps  HTML/PDF    LLM + Schema   Embeddings    PostgreSQL   Comparison
             cleanup     enforcement    + Taxonomy    + PostGIS    + Benchmarking
```

### Source Layout

```
src/
  api/            # FastAPI routes (demo, extract, compare, restaurants, dishes, benchmark)
  config/         # Pydantic settings (env vars, model registry)
  common/         # Structured logging (structlog)
  db/             # SQLAlchemy models + async engine
  discovery/      # Google Maps restaurant discovery
  fetching/       # HTML/PDF fetchers + content cleaner
  extraction/     # LLM model client, prompts, schemas, confidence scoring
  normalization/  # Dish name taxonomy, embedding matcher
  intelligence/   # Price comparison logic
  pipeline/       # Full pipeline runner
frontend/
  src/
    components/   # DishSearch, ComparisonResults
    api/          # API client (compare, extract)
    types/        # TypeScript interfaces
tests/            # 67 tests (unit + integration)
scripts/          # Model server launcher
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- [llama-server](https://github.com/ggerganov/llama.cpp) (for local model inference)

### 1. Install Python dependencies

```bash
pip install -e ".[dev]"
```

### 2. Install frontend dependencies

```bash
cd frontend && npm install
```

### 3. Download the extraction model

The model binary lives in the shared model registry (`~/Projects/_models/`), not inside this project.

```bash
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('LiquidAI/LFM2-8B-A1B-GGUF', filename='LFM2-8B-A1B-Q4_K_M.gguf', local_dir='$HOME/Projects/_models')"
```

Or set `MODELS_DIR` to point at your model directory if using a different location.

### 4. Start the model server

```bash
./scripts/start_model_server.sh
```

This starts llama-server on port 8081 with the LFM2-8B-A1B model. Override with env vars:

```bash
PORT=9090 GPU_LAYERS=0 ./scripts/start_model_server.sh
```

### 5. Start the backend

```bash
uvicorn src.api.main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 to use the app.

## Configuration

All config is via environment variables (or `.env` file). Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `MODELS_DIR` | `~/Projects/_models` | Shared model registry path |
| `LLM_HOST` | `localhost` | llama-server host |
| `LLM_PORT` | `8081` | llama-server port |
| `EXTRACTION_MODEL_PRIMARY` | `lfm2-8b-a1b` | Primary extraction model name |
| `ANTHROPIC_API_KEY` | (empty) | Enables Claude fallback when set |
| `EXTRACTION_MODEL_FALLBACK` | `claude-sonnet-4-20250514` | Fallback model |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection (future) |
| `GOOGLE_MAPS_API_KEY` | (empty) | Google Maps discovery (future) |

## Running Tests

```bash
# All unit tests (67 tests)
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Skip integration tests (require running llama-server)
pytest -m "not integration"

# Only integration tests
pytest -m integration
```

## Linting & Type Checking

```bash
# Lint
ruff check .

# Auto-fix
ruff check --fix .

# Format
black --line-length=100 .

# Type check
mypy --strict src/
```

## API Endpoints

### Demo (seeded data, no DB required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/demo/dishes` | List available dishes for autocomplete |
| `GET` | `/api/demo/compare?dish=...&radius=...&your_price=...` | Compare dish pricing across competitors |

### Extraction (requires llama-server)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/extract` | Extract structured menu from raw text |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health check |

## Tech Stack

**Backend:** Python 3.11, FastAPI, Pydantic, SQLAlchemy (async), structlog

**Frontend:** React 19, TypeScript, Vite

**LLM:** LFM2-8B-A1B (Liquid AI, Q4_K_M quantization) via llama-server, with Claude Sonnet fallback via Anthropic API. Schema enforcement via [instructor](https://github.com/instructor-ai/instructor).

**Database (planned):** PostgreSQL + PostGIS + pgvector

**Infrastructure:** Celery + Redis (task queue), Playwright (JS-rendered pages)

## Model Strategy

MenuLens uses a dual-model approach:

1. **Primary:** Local LFM2-8B-A1B running on llama-server (OpenAI-compatible API, JSON mode). Fast, private, no API costs. ~220 tok/s on Apple Silicon.
2. **Fallback:** Claude Sonnet via Anthropic API. Activates automatically when the primary model is unreachable or fails schema validation after retries.

Both models are wrapped with [instructor](https://github.com/instructor-ai/instructor) for guaranteed Pydantic schema compliance. The extraction output is always a typed `ExtractedMenu` with sections, items, prices, dietary tags, and confidence scores.

Model binaries are stored in the shared workspace registry (`~/Projects/_models/`) and registered in `_models/config.yaml`. See the [model registry docs](../_models/CLAUDE.md) for the shared pattern.

## License

Private repository. All rights reserved.
