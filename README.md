# Fusion Research Intelligence Platform

AI-powered nuclear fusion market intelligence platform that transforms static research documents into dynamic, searchable knowledge bases with natural language query capabilities.

## Features

- **Natural Language Search**: Query fusion companies, funding, and technologies using plain English
- **Company Profiles**: Detailed profiles with funding history, partnerships, TRL, and competitive positioning
- **Market Dashboard**: KPIs, charts, and trends for the fusion industry
- **Technology Analysis**: TRL matrix, technology comparison, development trends
- **LLM-Powered Intelligence**: SWOT analysis, market insights, and automated research updates
- **Report Generation**: Auto-generated market reports and company profiles

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter directory
cd fusion-researcher

# Create virtual environment and install dependencies
uv sync

# Copy environment template and configure
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Configuration

Edit `.env` file with your settings:

```bash
# Ollama (Local LLM)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen3:8b  # Options: qwen3:8b, qwen3:14b, gpt-oss:20b
DATABASE_PATH=research/fusion_research.db
```

**Note:** Make sure Ollama is running locally with the required models:
```bash
ollama pull qwen3:8b
ollama pull qwen3:14b
ollama pull gpt-oss:20b
```

### Running the Application

```bash
# Initialize database and load research data
uv run python scripts/init_db.py
uv run python scripts/populate_sample_data.py

# Start Streamlit app
uv run streamlit run streamlit_app/app.py
```

### Running Tests

```bash
uv run pytest tests/
```

## Project Structure

```
fusion-researcher/
├── research/                    # Research data and database
│   ├── Fusion_Research.md       # Source research document
│   ├── fusion_research.db       # SQLite database (generated)
│   └── chroma_data/             # Vector embeddings
├── src/                         # Core application code
│   ├── config.py                # Configuration management
│   ├── models/                  # Data models
│   ├── data/                    # Database and parsers
│   ├── llm/                     # LLM integration
│   ├── services/                # Business logic
│   └── ui/                      # UI components
├── streamlit_app/               # Streamlit web application
│   ├── app.py                   # Main entry point
│   └── pages/                   # Multi-page app pages
├── scripts/                     # Utility scripts
├── tests/                       # Test suite
└── docs/                        # Documentation
```

## Technology Stack

- **Backend**: Python 3.11+, SQLAlchemy, Pydantic
- **LLM**: LangChain + OpenAI GPT-4
- **Database**: SQLite (MVP), ChromaDB for vector search
- **Frontend**: Streamlit, Plotly
- **Package Manager**: uv

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [API Reference](docs/API_REFERENCE.md)

## License

MIT License
