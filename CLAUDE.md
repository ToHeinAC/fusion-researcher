# Fusion Research Intelligence Platform

AI-powered platform for aggregating, analyzing, and updating comprehensive research data on the global nuclear fusion industry.

## Project Overview

This platform transforms static fusion research documentation into a dynamic, queryable knowledge base with:
- Natural language queries powered by LLMs (OpenAI GPT-4 or Ollama local models)
- Semantic search using ChromaDB vector database
- Automated data updates via web research and news scraping
- Executive dashboards for market intelligence

**Target Users:** Technical researchers and investment analysts seeking fusion industry intelligence.

## Technology Stack

- **Python 3.11+** with **uv** package manager
- **SQLite** database with SQLAlchemy 2.0+
- **Streamlit 1.28+** for web UI (8 pages)
- **LangChain 0.1+** for LLM orchestration
- **ChromaDB 0.4+** for semantic search
- **Pydantic 2.0+** for data validation

## Directory Structure

```
src/
├── config.py           # Pydantic-based configuration
├── models/             # Domain models (Company, Funding, Technology, etc.)
├── data/
│   ├── database.py     # SQLite connection and schema
│   ├── repositories.py # Repository pattern for DB access
│   ├── vector_store.py # ChromaDB wrapper
│   └── parsers/        # Markdown parser for Fusion_Research.md
├── llm/
│   ├── chain_factory.py    # LangChain setup
│   ├── query_processor.py  # NL → SQL translation
│   ├── analyzer.py         # SWOT analysis, comparisons
│   └── cache.py            # Query result caching
└── services/
    ├── company_service.py      # Company search/filtering
    ├── market_service.py       # Market dashboard KPIs
    ├── technology_service.py   # TRL matrix analysis
    ├── report_service.py       # Report generation
    ├── news_service.py         # RSS feeds, news summarization
    ├── semantic_search_service.py  # Semantic search
    └── updater_service.py      # LLM-powered database updates

streamlit_app/
├── app.py              # Main entry point
└── pages/              # 8 Streamlit pages (Home, Companies, Technologies, etc.)

scripts/                # CLI utilities (init_db, populate, etc.)
tests/                  # pytest test suite
research/               # Database files and caches
```

## Key Commands

```bash
# Install dependencies
uv sync

# Run the Streamlit app
uv run streamlit run streamlit_app/app.py

# Initialize database
uv run python scripts/init_db.py

# Populate from Fusion_Research.md
uv run python scripts/populate_sample_data.py

# Build vector store for semantic search
uv run python scripts/populate_vector_store.py

# Generate news digest
uv run python scripts/generate_news_digest.py

# Run tests
uv run pytest tests/

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Formatting
uv run black src/
```

## Database Schema

Core tables: `companies`, `funding_rounds`, `investors`, `technologies`, `markets`, `partnerships`, `update_proposals`, `audit_log`

The database is SQLite stored at `research/fusion_research.db`.

## Configuration

Environment variables in `.env`:
- `OPENAI_API_KEY` - For GPT-4 (or use Ollama for local LLMs)
- `LLM_MODEL` - Model name (gpt-4, qwen3:8b, etc.)
- `DATABASE_PATH` - Path to SQLite database
- `CHROMA_DB_PATH` - Path to ChromaDB vector store

## Code Conventions

- **Repository Pattern**: All database access goes through `src/data/repositories.py`
- **Service Layer**: Business logic in `src/services/`
- **Pydantic Models**: All data models use Pydantic for validation
- **Type Hints**: All functions should have type hints
- **Security**: Parameterized SQL queries only, never string interpolation

## Data Source

Primary data comes from `Fusion_Research.md` (146KB German-language fusion market analysis) containing:
- 60+ fusion company profiles globally
- Market sizing projections (USD 356B → 843B by 2040)
- Technology TRL assessments
- Funding rounds and investor networks

## Important Notes

1. **Multi-LLM Support**: Can run with OpenAI or local Ollama models
2. **Offline-First**: Designed to work entirely locally without API keys
3. **German Language**: Source data is in German; app handles German queries
4. **Audit Trail**: All database updates are logged for compliance
5. **Confidence Scoring**: Data updates include confidence levels (0.0-1.0)
