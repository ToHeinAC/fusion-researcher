# Product Requirements Document: Fusion Research Intelligence Platform

**Version:** 1.1
**Date:** February 7, 2026
**Author:** Research & Development Team
**Status:** IN PROGRESS

---

## 1. Executive Summary

The **Fusion Research Intelligence Platform** is a specialized web application designed to aggregate, analyze, and update comprehensive research data on the global nuclear fusion industry. The platform ingests extensive market analysis documentation (Fusion_Research.md), structures it into a queryable database, and leverages Large Language Models (LLMs) via LangChain to enable natural language queries, automated research updates, and dynamic content generation.

**Target User:** Technical researchers and investment analysts requiring real-time fusion industry intelligence, company profiles, market trends, and technology assessments.

**Key Objectives:**
- Transform static research documents into dynamic, searchable knowledge base
- Enable natural language queries across fusion company profiles, market data, and technology assessments
- Automate research updates via LLM-powered web scraping and data synthesis
- Provide executive dashboards with market sizing, investment trends, and technology readiness levels (TRL)
- Support decision-making for investors, policy makers, and industry strategists

**Timeline:** 16 weeks (MVP by Week 8, production-ready by Week 16)

---

## 2. Mission

**Mission Statement:**  
*Democratize access to comprehensive, up-to-date fusion industry intelligence through an AI-powered research platform that transforms raw market analysis into actionable insights.*

**Core Values:**
- **Accuracy:** All data sourced from peer-reviewed sources, company filings, and academic research
- **Completeness:** 360-degree coverage of companies (startups, KMU, corporates, research institutes), geographies (Germany, DACH, BENELUX, global), and technologies (all fusion approaches)
- **Timeliness:** Automated updates ensure data currency; monthly refresh of financials, partnerships, regulatory changes
- **Transparency:** All data provenance tracked (source URL, retrieval date, confidence level)
- **Usability:** Natural language interface removes barriers for non-technical stakeholders

---

## 3. Target Users

**Primary User: Research Analyst / Investment Professional**
- **Role:** Aachen-based technical consultant/regulatory specialist in nuclear/radiation safety with advanced AI/ML development skills
- **Goals:**
  - Rapidly identify investment opportunities in fusion ecosystem
  - Track competitive positioning of German startups vs. global competitors
  - Monitor regulatory changes, funding rounds, and technology breakthroughs
  - Generate market reports and SWOT analyses programmatically
  - Support due diligence for venture capital / strategic investments
- **Technical Proficiency:** Advanced (comfortable with Python, APIs, databases, LLM concepts)
- **Typical Workflow:**
  1. Morning: Natural language query ("What's the latest funding activity in US-based tokamak companies?")
  2. Weekly: Deep-dive analysis on specific companies (Proxima Fusion trajectory, CFS supply chain risks)
  3. Monthly: Generate updated market sizing, competitive landscape visualizations
  4. Ad-hoc: Research-triggered queries (e.g., "How does Germany's HTS-magnet capacity compare to Japan?")

**Secondary Users (Future Iterations):**
- Policy makers (energy, industrial policy)
- Corporate strategists (utilities, tech companies evaluating Fusion M&A)
- Academic researchers (trend analysis, market dynamics)

**User Constraints:**
- Limited time availability → need rapid insights without deep exploration
- Prefers bullet-point summaries over narrative text (quick scans)
- Requires citation/source traceability for professional reports
- Operates in regulated environment → data security and audit trails critical

---

## 4. MVP Scope

### In Scope: Core Functionality

#### 4.1 Data Model & Ingestion
- **Structured Entity Ingestion:** Parse Fusion_Research.md into normalized database schema:
  - Companies (name, type, location, founding year, funding, technology, TRL, investors, partnerships, website, employees)
  - Technologies (approach, TRL range, leading companies, development stage, materials challenges)
  - Geographic Markets (region, market size USD, CAGR, growth drivers, regulatory environment)
  - Funding Rounds (company, amount, date, investors, stage, valuation)
  - Partnerships (source company, partner company/institute, type, value, timeline)
  - Regulatory Milestones (jurisdiction, policy, date, impact on industry)
- **Database Schema:** SQLite (.db) with 8-10 core tables normalized to 3NF
- **Data Refresh Trigger:** Manual upload of updated Fusion_Research.md + automated weekly LLM-powered scraping (news, company websites, LinkedIn)

#### 4.2 Query Interface
- **Natural Language Search:** "Show me all German startups with funding >EUR 100M" → translates to SQL via LangChain + GPT-4
- **Structured Filters:** UI-based filtering (country, TRL range, funding stage, technology type, employee count)
- **Time-Series Queries:** "Historical funding trends for Stellarator companies, 2020-2025"
- **Comparative Analysis:** "Compare CFS vs. Proxima Fusion on key metrics (funding, TRL, partnership breadth)"

#### 4.3 Data Visualization
- **Company Cards:** Profile summaries (funding, TRL, team size, key partnerships, competitive positioning)
- **Market Dashboard:** Pie charts (funding distribution by technology), bar charts (funding by region), trend lines (market sizing projection)
- **Technology TRL Matrix:** Heatmap of TRL by company/technology approach
- **Investment Landscape:** Sankey diagram (VCs → Fusion Companies) showing investment flows
- **Geographic Heatmap:** Interactive map with company density, funding concentration, regulatory openness

#### 4.4 Report Generation
- **Company Profile Report:** Auto-generated MD/PDF with company data, competitive positioning, risk assessment
- **Market Report:** Sections on market sizing, investment trends, technology landscape, Germany positioning
- **Investment Thesis:** Highlight opportunities for investor audience (market size, growth catalysts, entry barriers, valuation comps)

#### 4.5 LLM-Powered Features
- **Natural Language Queries:** "What are the top 5 risks for German fusion startups?" → LLM synthesizes insights from company data + pre-loaded research
- **SWOT Analysis Generator:** Input company name → auto-generate strengths/weaknesses/opportunities/threats
- **News Summarizer:** LLM fetches latest fusion news, summarizes, flags relevance to portfolio companies
- **Market Intelligence:** "How do Tokamak vs. Stellarator cost trajectories compare?" → LLM cross-references TRL, development timelines, cost estimates

### In Scope: Technical Infrastructure

#### 4.6 Backend Architecture
- **Framework:** Python 3.11+ with FastAPI (optional for future API expansion) or Streamlit-only for MVP
- **LLM Integration:** LangChain with OpenAI GPT-4 for NLP queries + semantic search
- **Database:** SQLite (.db file) for MVP; schema migration via Alembic (optional for MVP, planned for v1.1)
- **Data Pipeline:** 
  - Weekly scheduled task (APScheduler) to scrape news, regulatory updates
  - LangChain document loaders for Fusion_Research.md ingestion
  - Vector embeddings stored in Chroma DB (local) for semantic search
- **Package Manager:** uv for fast dependency resolution

#### 4.7 Frontend (Streamlit)
- Multi-page app:
  - **Home:** Dashboard with key metrics (market size, top investors, Germany positioning)
  - **Companies:** Searchable company database with filters, detail pages
  - **Technologies:** TRL matrix, technology comparison, development trends
  - **Markets:** Geographic analysis, investment flows by region
  - **Research:** Query interface, report generation
  - **Settings:** Data refresh status, configuration (API keys, data sources)
  - **News:** RSS feeds, Tavily web search, LLM-powered news digests
  - **Updater:** LLM-powered database update proposals with confidence scoring
  - **Network:** Interactive pyvis graph of company-investor-partner relationships
  - **Editor:** Dynamic CRUD forms for all entity types with audit logging
- Responsive design (mobile-friendly via Streamlit responsive containers)
- Real-time update indicators (last DB refresh, data currency status)

#### 4.8 Data Persistence
- **Local SQLite Database:** `research/fusion_research.db` (version-controlled, ~50MB at full scale)
- **Vector Store:** Chroma local index for semantic search (~100MB)
- **Config/Secrets:** `research/.env` for API keys, database credentials (git-ignored)

### Out of Scope (MVP)

**Explicitly Excluded:**
- ❌ Multi-user authentication / role-based access control (single-user assumption for MVP)
- ❌ Real-time data sync from external APIs (weekly batch sufficient)
- ❌ Advanced ML models (clustering, anomaly detection) → Phase 2
- ❌ Mobile app (Streamlit web responsive design covers 90% of use cases)
- ❌ Data export to Excel/PowerPoint (MD reports only, Phase 2)
- ❌ Regulatory compliance reporting (GDPR/HIPAA scope assessment post-MVP)
- ❌ Custom NLP model fine-tuning (use OpenAI GPT-4 out-of-box)
- ❌ Historical version control (data snapshots tracked manually, Phase 2)
- ❌ Integration with external data warehouses (self-contained MVP)

---

## 5. User Stories

### Epic 1: Data Exploration & Discovery

**US-1.1: As a researcher, I want to search for fusion companies by natural language query so that I can quickly answer ad-hoc questions without learning database syntax.**

- **Acceptance Criteria:**
  - Query: "German startups with more than EUR 100M funding" → Returns Proxima Fusion, Marvel Fusion, Focused Energy
  - Response time <2 seconds
  - Results include company name, funding, TRL, location, key metrics
  - Source citations included for each data point
- **Priority:** P0 (Core feature)
- **Effort:** 8 story points

**US-1.2: As a researcher, I want to filter companies by multiple criteria (country, technology, TRL, funding stage) so that I can narrow down investment opportunities.**

- **Acceptance Criteria:**
  - Filters: Country, Technology Approach, TRL Range (1-9), Funding Stage (Pre-seed → Series D+), Founded Year, Employee Count
  - Multi-select with AND/OR logic
  - Results update in <500ms
- **Priority:** P0
- **Effort:** 5 story points

**US-1.3: As a researcher, I want to view a company profile card with funding history, partnerships, technology, TRL, and competitive positioning so that I can assess opportunities quickly.**

- **Acceptance Criteria:**
  - Company name, founding date, location, team size
  - Funding timeline (all rounds with dates, amounts, investors)
  - Technology description with TRL + TRL justification
  - Key partnerships (max 5 shown, link to expand)
  - Competitive comparison (similar companies by TRL/funding)
  - "Last Updated" timestamp and data source links
- **Priority:** P0
- **Effort:** 8 story points

### Epic 2: Market Intelligence & Analysis

**US-2.1: As a researcher, I want to see a market dashboard with key metrics (total funding, company count, market sizing, investment trends) so that I can understand ecosystem health at a glance.**

- **Acceptance Criteria:**
  - KPIs: Total funding (global, by region, by technology), Company count (by type), Market size USD (2024-2040 projection)
  - Charts: Funding distribution pie (tech), funding by region bar, market size trendline
  - Filters: Time range, geography, technology
  - YoY/QoQ growth rates displayed
- **Priority:** P1
- **Effort:** 10 story points

**US-2.2: As a researcher, I want to compare two companies head-to-head (e.g., Proxima vs. Gauss) so that I can understand competitive dynamics.**

- **Acceptance Criteria:**
  - Side-by-side metrics: Funding, TRL, Team size, Partnerships, Technology differentiation
  - Radar chart (5-7 dimensions: tech maturity, funding, team, partnerships, market timing)
  - Narrative summary of strengths/weaknesses
- **Priority:** P1
- **Effort:** 6 story points

**US-2.3: As a researcher, I want to view a Technology Readiness Level (TRL) matrix (companies vs. TRL, colored by technology) so that I can assess which approaches are closest to commercialization.**

- **Acceptance Criteria:**
  - Y-axis: Companies (sorted by funding or founding date)
  - X-axis: TRL 1-9
  - Cell color-coded by technology approach (Tokamak, Stellarator, Laser, FRC)
  - Hover shows company name, TRL justification, nearest milestone
  - Sortable/filterable
- **Priority:** P1
- **Effort:** 8 story points

### Epic 3: LLM-Powered Intelligence

**US-3.1: As a researcher, I want to ask open-ended questions like "What are the top risks to German fusion startups?" and get synthesized insights from the research database.**

- **Acceptance Criteria:**
  - LLM processes query, references specific companies/data points
  - Cites sources (e.g., "Per Proxima Fusion Series A data, Lightspeed Ventures...")
  - Response length: 200-500 words (bullet points preferred)
  - Response time <5 seconds (with caching for popular queries)
- **Priority:** P1
- **Effort:** 8 story points

**US-3.2: As a researcher, I want to generate a SWOT analysis for any company (e.g., Proxima Fusion) by entering the company name so that I can quickly assess positioning.**

- **Acceptance Criteria:**
  - Input: Company name
  - Output: Markdown SWOT (Strengths, Weaknesses, Opportunities, Threats) with 3-4 bullets each
  - Data-backed: Each bullet references specific metrics/partnerships/tech
  - Downloadable as MD or copy-to-clipboard
- **Priority:** P2
- **Effort:** 6 story points

**US-3.3: As a researcher, I want to receive a weekly digest of fusion news filtered by relevance to my interests (German companies, funding, technology breakthroughs) so that I stay current without manual research.**

- **Acceptance Criteria:**
  - Scheduled task: Every Monday 9 AM CET
  - Pulls 10-20 latest news articles (via LangChain web loader)
  - LLM classifies by relevance (High/Medium/Low) + summarizes (3-4 sentences max)
  - Email/Slack notification with digest
- **Priority:** P2
- **Effort:** 10 story points

### Epic 4: Report Generation & Export

**US-4.1: As a researcher, I want to generate a market report on German fusion companies (funding, TRL, partnerships, competitive positioning) that I can share with stakeholders.**

- **Acceptance Criteria:**
  - Input: Report type (Market Overview, Company Profiles, Investment Thesis)
  - Output: Markdown file with sections, charts embedded as ASCII/image references
  - Content: 5-10 pages, data-sourced from DB, includes citations
  - Timestamp + data refresh date included
  - Downloadable as .md or .pdf (via Pandoc)
- **Priority:** P2
- **Effort:** 12 story points

**US-4.2: As a researcher, I want to export a CSV of companies matching my search criteria (for further analysis in Excel/Python) so that I can perform custom analysis.**

- **Acceptance Criteria:**
  - Search results → "Export as CSV" button
  - Columns: Company name, founding year, location, funding total, TRL, technology, investors, partnerships, employees, website
  - File downloaded to local machine
- **Priority:** P2
- **Effort:** 3 story points

### Epic 5: Data Management & Updates

**US-5.1: As a researcher, I want to upload an updated Fusion_Research.md file so that the database refreshes with latest company data, funding rounds, and market information.**

- **Acceptance Criteria:**
  - File upload UI (drag-drop or file select)
  - Parsing: Extract entities (companies, funding, partnerships)
  - Conflict resolution: If company exists, merge new data (append funding rounds, update partnerships)
  - Transaction rollback on parse error
  - Completion notification + data diff summary (e.g., "Added 5 new companies, updated 12 funding rounds")
- **Priority:** P0
- **Effort:** 8 story points

**US-5.2: As a researcher, I want to see data freshness indicators (last update time, refresh status) so that I know whether information is current.**

- **Acceptance Criteria:**
  - Dashboard badge: "Data updated 2 hours ago" (with red alert if >7 days stale)
  - Each company profile shows "Last Updated: [date]" and "Next Scheduled Update: [date]"
  - Manual refresh button available
- **Priority:** P1
- **Effort:** 2 story points

**US-5.3: As a researcher, I want to configure data sources (API keys for news scraping, web scraping frequency, LLM model selection) without editing code.**

- **Acceptance Criteria:**
  - Settings page with form fields:
    - OpenAI API key (masked input, tested on save)
    - News scraper frequency (daily/weekly)
    - LLM model selection (GPT-4, GPT-3.5, Claude)
    - Data export location
  - Settings saved to .env file (git-ignored)
  - Validation: Test API keys on save, notify if invalid
- **Priority:** P1
- **Effort:** 4 story points

---

## 6. Core Architecture & Patterns

### 6.1 Technology Stack Overview

```
┌─────────────────────────────────────────────────────────┐
│ Streamlit Frontend (Multi-page, responsive)             │
│ - Home Dashboard                                        │
│ - Company Search & Browse                               │
│ - Technology Analysis                                   │
│ - Market Intelligence                                   │
│ - Report Generation                                     │
│ - Settings & Data Management                            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Application Layer (Python)                              │
│ - Data Processing (Pandas, NumPy)                       │
│ - LLM Integration (LangChain)                           │
│ - Query Processing (Natural Language → SQL)             │
│ - Report Generation (Jinja2 templates)                  │
│ - Configuration Management                              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Data Layer                                              │
│ - SQLite Database (research/fusion_research.db)         │
│ - Vector Store (Chroma local index)                     │
│ - File Cache (parsed MD, configs, temp files)          │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Design Patterns

**Pattern 1: Repository Pattern**
- **Purpose:** Abstract database layer from business logic
- **Implementation:**
  ```python
  class CompanyRepository:
      def __init__(self, db_path: str):
          self.db = sqlite3.connect(db_path)
      
      def get_by_id(self, company_id: int) -> Company:
          # Query implementation
          pass
      
      def search_by_criteria(self, filters: Dict) -> List[Company]:
          # Filtered query implementation
          pass
  ```
- **Benefit:** Easy testing, future migration to PostgreSQL/MongoDB without UI changes

**Pattern 2: LangChain Integration Pattern**
- **Purpose:** Bridge natural language queries to structured database
- **Implementation:**
  ```python
  class NLQueryProcessor:
      def __init__(self, llm: ChatOpenAI, db: SQLDatabase):
          self.chain = create_sql_query_chain(llm, db)
      
      def process_query(self, nl_query: str) -> QueryResult:
          # Convert NL → SQL → Execute → Parse → Return
          sql = self.chain.invoke({"query": nl_query})
          results = self.db.execute(sql)
          return QueryResult(results)
  ```
- **Benefit:** Flexible query interface without manual SQL engineering

**Pattern 3: Adapter Pattern (Data Ingestion)**
- **Purpose:** Flexibly support multiple input formats (MD, CSV, JSON)
- **Implementation:**
  ```python
  class DataAdapter(ABC):
      @abstractmethod
      def parse(self, source: str) -> List[Entity]:
          pass
  
  class MarkdownAdapter(DataAdapter):
      def parse(self, md_content: str) -> List[Entity]:
          # Parse Fusion_Research.md
          pass
  
  class DataIngestionService:
      def __init__(self):
          self.adapters = {
              "md": MarkdownAdapter(),
              "csv": CSVAdapter(),
              "json": JSONAdapter()
          }
  ```
- **Benefit:** Extensible to new input formats without core changes

**Pattern 4: Service Layer Pattern**
- **Purpose:** Encapsulate business logic (search, analysis, reporting)
- **Implementation:**
  ```python
  class CompanyService:
      def __init__(self, repo: CompanyRepository, llm: ChatOpenAI):
          self.repo = repo
          self.llm = llm
      
      def search(self, criteria: SearchCriteria) -> List[CompanyDTO]:
          # Business logic for search
          pass
      
      def generate_swot(self, company_id: int) -> SWOTAnalysis:
          # LLM-powered SWOT generation
          pass
  ```
- **Benefit:** Testable, reusable business logic

**Pattern 5: Caching Pattern (Performance)**
- **Purpose:** Reduce LLM API costs and latency
- **Implementation:**
  ```python
  from functools import lru_cache
  import hashlib
  
  class QueryCache:
      def __init__(self, ttl: int = 3600):
          self.cache = {}
          self.ttl = ttl
      
      def get(self, query: str) -> Optional[Result]:
          key = hashlib.md5(query.encode()).hexdigest()
          if key in self.cache:
              cached_result, timestamp = self.cache[key]
              if time.time() - timestamp < self.ttl:
                  return cached_result
          return None
      
      def set(self, query: str, result: Result):
          key = hashlib.md5(query.encode()).hexdigest()
          self.cache[key] = (result, time.time())
  ```
- **Benefit:** 50-80% reduction in LLM API costs for frequent queries

### 6.3 Directory Structure

```
fusion-research-platform/
├── research/
│   ├── Fusion_Research.md           # Source research document
│   ├── fusion_research.db           # SQLite database (generated)
│   ├── chroma_data/                 # Vector embeddings
│   └── .env                         # Configuration (git-ignored)
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # Configuration management (pydantic)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py               # Company, Startup, KMU, Corporation
│   │   ├── funding.py               # FundingRound, Investor
│   │   ├── technology.py            # Technology, TRL
│   │   ├── market.py                # Market, Region, Trend
│   │   └── partnership.py           # Partnership, Collaboration
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py              # SQLite connection + migration
│   │   ├── repositories.py          # Repository pattern implementations
│   │   ├── parsers/
│   │   │   ├── markdown_parser.py   # Fusion_Research.md → Entities
│   │   │   ├── relationship_parser.py  # Extract investors/partners/collaborations
│   │   │   ├── csv_parser.py
│   │   │   └── json_parser.py
│   │   └── ingestion_service.py     # Data import orchestration
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── chain_factory.py         # LangChain setup
│   │   ├── query_processor.py       # NL Query → SQL
│   │   ├── analyzer.py              # SWOT, comparison, insights
│   │   └── cache.py                 # Query caching
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── company_service.py       # Company business logic
│   │   ├── market_service.py        # Market analysis
│   │   ├── technology_service.py    # Technology TRL analysis
│   │   ├── report_service.py        # Report generation
│   │   ├── news_service.py          # News ingestion + summarization
│   │   ├── semantic_search_service.py  # ChromaDB semantic search
│   │   ├── network_service.py       # Investor/partner network (pyvis)
│   │   ├── updater_service.py       # LLM-powered database updates
│   │   ├── audit_service.py         # Audit logging for data changes
│   │   ├── crud_service.py          # Unified CRUD for all entity types
│   │   ├── markdown_merger_service.py  # LLM-powered markdown merge
│   │   └── database_sync_service.py # Sync database from merged markdown
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                # Logging configuration
│   │   ├── validators.py            # Input validation
│   │   └── formatters.py            # Output formatting (markdown, charts)
│   │
│   └── ui/
│       ├── __init__.py
│       ├── components.py            # Reusable Streamlit components
│       ├── charts.py                # Chart generation (Plotly)
│       └── styles.py                # CSS/styling utilities
│
├── streamlit_app/
│   ├── __init__.py
│   ├── app.py                       # Main Streamlit app
│   ├── pages/
│   │   ├── 1_🏠_home.py             # Dashboard
│   │   ├── 2_🔍_companies.py        # Company search & browse
│   │   ├── 3_🔬_technologies.py     # Technology analysis
│   │   ├── 4_📊_markets.py          # Market intelligence
│   │   ├── 5_📝_research.py         # Query interface & reports
│   │   ├── 6_⚙️_settings.py         # Configuration
│   │   ├── 7_📰_News.py             # News digests & search
│   │   ├── 8_🔄_Updater.py          # LLM-powered update proposals
│   │   ├── 9_🔗_Network.py          # Interactive network graph
│   │   └── 10_✏️_Editor.py          # CRUD editor for all entities
│   └── secrets.toml                 # Streamlit secrets (git-ignored)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest configuration
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_parsers.py
│   │   ├── test_services.py
│   │   └── test_llm_chain.py
│   ├── integration/
│   │   ├── test_data_pipeline.py
│   │   ├── test_query_processor.py
│   │   └── test_report_generation.py
│   └── fixtures/
│       ├── sample_companies.json
│       └── sample_research.md
│
├── scripts/
│   ├── init_db.py                   # Initialize database schema
│   ├── populate_sample_data.py      # Load Fusion_Research.md
│   ├── populate_vector_store.py     # Build ChromaDB vector store
│   ├── normalize_relationships.py   # Populate normalized relationship tables
│   ├── generate_news_digest.py      # CLI news digest generator
│   ├── merge_research_updates.py    # Merge research update documents
│   ├── sync_database_from_markdown.py # Sync DB from merged markdown
│   └── run_full_update_pipeline.py  # Full update pipeline orchestration
│
├── pyproject.toml                   # uv + pip config
├── uv.lock                          # uv dependency lock
├── .env.example                     # Example environment variables
├── .gitignore                       # Git ignore rules
├── README.md                        # Getting started
└── LICENSE                          # MIT / Apache 2.0
```

---

## 7. Features

### 7.1 Core Search & Discovery

**Feature: Natural Language Query Engine**
- User enters: "Show German startups founded after 2020 with Stellarator technology"
- System: Parses NL → SQL via LangChain, executes, returns company cards
- Benefits: No SQL knowledge required; intuitive for analysts
- Related US: US-1.1

**Feature: Advanced Filtering**
- Multi-select filters: Country, Technology, TRL Range, Funding Stage, Founding Year, Employee Count, Investor
- Filters combine with AND logic (e.g., "Germany AND Stellarator AND TRL 5-6")
- Real-time result count updates
- Related US: US-1.2

**Feature: Company Profile Cards**
- Summary view: Logo/Name, Founded, Location, Team Size, Website
- Funding history timeline (bar chart with round amounts, investors, dates)
- Technology: Approach, TRL, TRL justification, key materials/challenges
- Key partnerships (5 most important, expandable)
- Competitive positioning (radar chart vs. similar companies)
- Investment risk score (1-10) based on TRL, funding, partnerships
- Related US: US-1.3

### 7.2 Market Intelligence

**Feature: Dashboard KPIs**
- Metrics: Total fusion funding (YTD, all-time), Company count (by type, by technology), Market size projections (2024-2040)
- Growth rates: YoY funding growth, CAGRby technology
- Highlights: Largest recent funding round, most-connected startup, fastest-growing technology approach
- Related US: US-2.1

**Feature: Competitive Comparison**
- Input: Select 2 companies (e.g., CFS vs. Proxima)
- Output: Side-by-side metrics, radar chart (tech maturity, funding, team, partnerships, market timing), narrative summary
- Benchmark data: How do they rank globally in each dimension?
- Related US: US-2.2

**Feature: Technology TRL Heatmap**
- Rows: Companies (sorted by founding date or funding)
- Columns: TRL 1-9
- Cell colors: By technology approach (Tokamak=blue, Stellarator=green, Laser=red, FRC=orange)
- Hover info: Company name, TRL justification, nearest milestone
- Sortable/filterable by technology, region, funding
- Related US: US-2.3

**Feature: Geographic Heat Map**
- Interactive map: Color intensity by company density, funding concentration
- Layers: Companies, research institutes, investors
- Click to zoom/detail on specific countries or regions
- Heatmap overlays: Regulatory openness score, talent availability, supply chain readiness

**Feature: Investment Landscape Visualization**
- Sankey diagram: Venture Capital firms → Fusion companies (flow thickness = investment amount)
- Filter by VC type (Generalist VC, Specialized VC, Corporate VC, Family Office, Government)
- Hover shows investment details (amount, date, round type)

### 7.3 LLM-Powered Intelligence

**Feature: Open-Ended Question Answering**
- User asks: "What are the biggest risks for German fusion startups in the next 3 years?"
- LLM synthesizes insights from company data, market trends, regulatory environment
- Response: 300-500 word answer with bullet points, includes citations ("Per Proxima Fusion Series A data...")
- Response caching: Popular queries cached for 24h to reduce API costs
- Related US: US-3.1

**Feature: SWOT Analysis Generator**
- Input: Company name
- Output: 
  - Strengths (3-4 items): Tech differentiation, team quality, partnerships, regulatory tailwinds
  - Weaknesses (3-4 items): Funding gap vs. competitors, less-proven technology, key person risk
  - Opportunities (3-4 items): Market timing, supply chain partnerships, regulation changes
  - Threats (3-4 items): Competitive pressure, technology risk, geopolitical/supply chain
- Data-backed: Each bullet includes specific metrics (e.g., "Proxima has EUR 130M Series A (1.3x Focused Energy)")
- Downloadable as MD or copy-to-clipboard
- Related US: US-3.2

**Feature: Weekly News Digest**
- Scheduled task: Mondays 9 AM CET
- Sources: FusionIndustryAssociation.org, CrunchBase, FusionEnergyBase.com, Company websites, News aggregators (Bing News, Google News API)
- Processing:
  1. Fetch 20-30 latest articles
  2. LLM classifies relevance (High: German companies, funding, TRL breakthroughs; Medium: Global market trends; Low: Adjacent renewable energy)
  3. Summarize to 2-3 sentences per article
  4. Highlight: New funding rounds, partnerships, regulatory changes, technology milestones
- Delivery: Email or Slack notification with digest link
- Related US: US-3.3

**Feature: Market Trend Analysis**
- "How has Tokamak vs. Stellarator funding evolved 2020-2025?" → Line chart with trend arrows
- "What regulatory changes are accelerating fusion commercialization?" → Timeline of key milestones
- "Which VCs are most active in fusion?" → VC ranking by capital deployed, portfolio diversity

### 7.4 Report Generation & Export

**Feature: Market Report Generator**
- Template options:
  1. **Market Overview:** Market size (2024-2040), CAGR, regional breakdown, technology distribution
  2. **Company Profiles:** Top 10-20 companies by funding/TRL, detailed profiles, competitive matrix
  3. **Investment Thesis:** Market opportunity, key drivers, entry barriers, valuation comparables
  4. **Germany Competitive Analysis:** German startups vs. global leaders, SWOT, positioning
- Output: 
  - Format: Markdown (default), PDF (via Pandoc), DOCX (future)
  - Length: 5-15 pages depending on scope
  - Includes charts (ASCII or image references), tables, data citations
  - Timestamp + data refresh date
- Related US: US-4.1

**Feature: Data Export (CSV)**
- Search results → "Export as CSV" button
- Columns: Company, Founding Year, Location, Funding Total, TRL, Technology, Key Investors, Partnerships, Employees, Website, Last Updated
- Download to local machine
- Related US: US-4.2

**Feature: Custom Report Builder** (Future)
- Drag-and-drop interface to select sections (Market Overview, Company Profiles, Technology Analysis, etc.)
- Customize: Date range, company filters, metrics to include
- Preview before generation

### 7.5 Data Management

**Feature: Data Upload & Refresh**
- UI: Drag-drop or file select for updated Fusion_Research.md
- Processing:
  1. Parse MD into entities (companies, funding, partnerships)
  2. Conflict resolution: Merge new data with existing (append funding rounds, update partnerships)
  3. Validation: Check data integrity, flag missing fields
  4. Transaction rollback if parse errors
- Completion notification: "Updated 5 new companies, 12 funding rounds, 8 partnerships. Failed to parse: 2 entries (see log)"
- Related US: US-5.1

**Feature: Data Freshness Indicators**
- Dashboard badge: "Data updated 2 hours ago" (green if <7 days, red if >7 days)
- Company profile: "Last Updated: [date], Next Scheduled Update: [date]"
- Manual refresh button available
- Audit log: Show all data changes (user, timestamp, before/after)
- Related US: US-5.2

**Feature: Configuration Management UI**
- Settings page with form fields:
  - OpenAI API key (masked input, test on save)
  - News scraper frequency (daily/weekly/manual)
  - LLM model selection (GPT-4, GPT-3.5, Claude—placeholder for multi-model support)
  - Data export location (default: research/ folder)
  - Max query response length (words)
  - Cache TTL (seconds)
- Validation: Test API keys, notify if invalid
- Save confirmation
- Related US: US-5.3

### 7.6 Analytics & Insights (Phase 2)

- **Trend Analysis:** How funding for Stellarators is growing YoY
- **Anomaly Detection:** Sudden funding spike, unexpected partnership, competitor move
- **Predictive Insights:** Market size forecast, likely TRL progression, exit timeline
- **Benchmarking:** How a company compares to peer group (percentile rankings)

---

## 8. Technology Stack

### 8.1 Backend / Core Application

| Layer | Technology | Version | Purpose | Rationale |
|-------|-----------|---------|---------|-----------|
| **Language** | Python | 3.11+ | Core language | Modern, ML/data ecosystem; async support |
| **Package Manager** | uv | Latest | Dependency management | 10-100x faster than pip; Rust-based |
| **Framework** | Streamlit | 1.28+ | Web UI | Rapid development; built for data apps |
| **LLM Framework** | LangChain | 0.1+ | LLM orchestration | SQL chains, semantic search, caching |
| **LLM API** | OpenAI GPT-4 | Latest | Natural language processing | Mature, best-in-class reasoning (for MVP) |
| **Database (Local)** | SQLite | 3.43+ | Persistent storage | Zero-config, file-based; sufficient for MVP |
| **Database (Vector)** | Chroma | 0.4+ | Semantic search | Local, open-source vector DB |
| **ORM (Optional)** | SQLAlchemy | 2.0+ | SQL abstraction | Prepare for future PostgreSQL migration |
| **Data Processing** | Pandas | 2.0+ | CSV/tabular data | Industry standard for data munging |
| **Numerical** | NumPy | 1.24+ | Array operations | Foundation for Pandas, ML libraries |
| **MD Parsing** | markdown-it-py | 3.0+ | Parse Fusion_Research.md | Structured table/list extraction |
| **Task Scheduling** | APScheduler | 3.10+ | Weekly jobs (news digest) | Reliable background task runner |
| **HTTP Client** | httpx | 0.25+ | Web scraping, API calls | Async support, timeouts |
| **HTML Parsing** | BeautifulSoup4 | 4.12+ | News page scraping | Robust DOM navigation |
| **Config Management** | Pydantic | 2.0+ | Settings validation | Type-safe config, .env support |
| **Testing** | pytest | 7.4+ | Unit/integration tests | Industry standard |
| **Logging** | Python logging | Built-in | Event logging | Standard library suffices for MVP |

### 8.2 Frontend / UI

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | Streamlit | 1.28+ | Multi-page app, interactive components |
| **Charting** | Plotly | 5.17+ | Interactive visualizations (heatmaps, Sankey) |
| **Markdown Rendering** | streamlit-markdown | Built-in | Display reports, citations |
| **Icons/Emojis** | Streamlit native | Built-in | Page navigation emojis (🏠, 🔍, etc.) |
| **Data Tables** | streamlit-aggrid (Optional) | 0.3+ | Advanced filtering/sorting (Phase 2) |

### 8.3 Deployment & Infrastructure (MVP = Local)

| Component | Technology | Purpose | MVP |
|-----------|-----------|---------|-----|
| **Local Development** | Python venv + uv | Isolated environment | ✅ |
| **Database** | SQLite file (research/fusion_research.db) | Persistent storage | ✅ |
| **Secrets/Config** | .env file | API keys, settings | ✅ |
| **Deployment** | Streamlit Cloud or Docker | Production hosting | Phase 2 |
| **Backup** | Manual .db export or GitHub Actions | Data backup | Phase 2 |

### 8.4 Development Workflow

**Installation & Setup:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repo
git clone <repo>
cd fusion-research-platform

# Create venv + install deps
uv sync

# Run Streamlit app locally
uv run streamlit run streamlit_app/app.py

# Run tests
uv run pytest tests/

# Run specific feature
uv run python -m src.scripts.populate_sample_data
```

**Dependency Management:**
```bash
# Add new dependency
uv pip install langchain-openai
uv pip freeze > requirements.txt  # For CI/CD

# Update all
uv sync --upgrade

# Lock dependencies
uv lock
```

### 8.5 Environment Configuration

**`.env` Structure:**
```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4  # or gpt-3.5-turbo
LLM_TEMPERATURE=0.3
MAX_RESPONSE_TOKENS=2000

# Database
DATABASE_PATH=research/fusion_research.db
CHROMA_DB_PATH=research/chroma_data

# News Scraping
NEWS_SCRAPE_FREQUENCY=weekly  # daily, weekly, manual
NEWS_SOURCES=fusionindustryassociation,crunchbase,fusionenergybase

# Caching
QUERY_CACHE_TTL=3600  # seconds
CACHE_MAX_SIZE=100  # number of queries

# Streamlit Secrets (also stored in streamlit_app/secrets.toml)
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501

# Email/Notifications (for digest delivery—Phase 2)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**`pyproject.toml` (uv config):**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fusion-research-platform"
version = "0.1.0"
description = "AI-powered nuclear fusion market intelligence platform"
authors = [{name = "Research Team", email = "research@example.com"}]
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    "streamlit>=1.28",
    "langchain>=0.1",
    "langchain-openai>=0.0.5",
    "pandas>=2.0",
    "numpy>=1.24",
    "plotly>=5.17",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
    "httpx>=0.25",
    "beautifulsoup4>=4.12",
    "markdown-it-py>=3.0",
    "apscheduler>=3.10",
    "python-dotenv>=1.0",
    "chromadb>=0.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.4",
]

[tool.uv]
dev-dependencies = ["dev"]
```

---

## 9. Security & Configuration

### 9.1 Security Scope

**In Scope (MVP):**
- ✅ Input validation on all user inputs (NL queries, file uploads, filter parameters)
- ✅ SQL injection prevention via parameterized queries (SQLAlchemy ORM)
- ✅ API key management via environment variables (never hardcoded)
- ✅ .env file excluded from git
- ✅ File upload validation (only .md files allowed, max 10MB)
- ✅ OpenAI API rate limiting (max 100 calls/day per user during MVP)
- ✅ Logging of all data access (audit trail for compliance)

**Out of Scope (Phase 2+):**
- ❌ Multi-user authentication (single-user assumed for MVP)
- ❌ Role-based access control (not applicable to single user)
- ❌ Encryption at rest (local .db file, not a regulated data store)
- ❌ HTTPS/TLS (only for production deployment phase)
- ❌ GDPR/HIPAA compliance (not PII-heavy; personal data minimal)
- ❌ WAF (Web Application Firewall)
- ❌ DDoS protection

### 9.2 Input Validation

**Validation Layer (Pydantic Models):**

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List

class SearchQuery(BaseModel):
    """Natural language search query validation"""
    query: str = Field(..., min_length=3, max_length=500)
    filters: Optional[dict] = None
    
    @validator('query')
    def query_no_injection(cls, v):
        # Prevent SQL injection attempts in NL query
        dangerous_patterns = ['DROP', 'DELETE', ';', '--', '/*']
        if any(pattern in v.upper() for pattern in dangerous_patterns):
            raise ValueError("Query contains invalid patterns")
        return v

class CompanyFilter(BaseModel):
    country: Optional[str] = None
    technology: Optional[str] = None
    trl_min: Optional[int] = Field(None, ge=1, le=9)
    trl_max: Optional[int] = Field(None, ge=1, le=9)
    funding_min_usd: Optional[float] = Field(None, ge=0)
    
    @validator('country')
    def validate_country(cls, v):
        valid_countries = ['Germany', 'USA', 'UK', 'Japan', 'China', ...]
        if v not in valid_countries:
            raise ValueError(f"Invalid country: {v}")
        return v

class FileUpload(BaseModel):
    filename: str
    max_size_mb: int = 10
    
    @validator('filename')
    def validate_extension(cls, v):
        if not v.endswith('.md'):
            raise ValueError("Only .md files allowed")
        return v
```

### 9.3 SQL Injection Prevention

**SQLAlchemy ORM (Automatic):**
```python
# ✅ SAFE: Parameterized query via ORM
from sqlalchemy import select

query = select(Company).where(Company.country == user_input)
results = session.execute(query).scalars().all()

# ❌ UNSAFE: String interpolation (not used)
query = f"SELECT * FROM companies WHERE country = '{user_input}'"

# ✅ SAFE: Explicit parameterization (if raw SQL needed)
query = text("SELECT * FROM companies WHERE country = :country")
results = session.execute(query, {"country": user_input})
```

### 9.4 API Key Management

**Environment Variables Only:**
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    database_path: str = "research/fusion_research.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Usage in LLM chain
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4")
```

**.env.example (for reference, real .env git-ignored):**
```bash
OPENAI_API_KEY=sk-YOUR_KEY_HERE
DATABASE_PATH=research/fusion_research.db
```

**`.gitignore` configuration:**
```bash
# Environment
.env
.env.local
.env.*.local

# Secrets
streamlit_app/secrets.toml

# Database
*.db
research/chroma_data/

# IDE
.vscode/
.idea/
*.swp

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/
```

### 9.5 File Upload Validation

**Secure file handling:**
```python
import os
from pathlib import Path

class FileUploadService:
    MAX_FILE_SIZE_MB = 10
    ALLOWED_EXTENSIONS = {'.md', '.csv', '.json'}
    UPLOAD_DIR = Path("research/uploads")
    
    def validate_upload(self, file_path: str) -> bool:
        """Validate uploaded file"""
        file = Path(file_path)
        
        # Check extension
        if file.suffix not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid extension: {file.suffix}")
        
        # Check size
        file_size_mb = file.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB")
        
        # Check path traversal attempts
        if ".." in str(file):
            raise ValueError("Invalid file path")
        
        # Ensure upload dir is safe
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        return True
```

### 9.6 Rate Limiting (API)

**OpenAI API rate limiting:**
```python
from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int, time_window_seconds: int):
        self.max_calls = max_calls
        self.time_window = timedelta(seconds=time_window_seconds)
        self.call_times = deque()
    
    def is_allowed(self) -> bool:
        now = datetime.now()
        # Remove old calls outside window
        while self.call_times and self.call_times[0] < now - self.time_window:
            self.call_times.popleft()
        
        if len(self.call_times) < self.max_calls:
            self.call_times.append(now)
            return True
        return False

# Usage
limiter = RateLimiter(max_calls=100, time_window_seconds=86400)  # 100 calls/day

if not limiter.is_allowed():
    raise Exception("Rate limit exceeded")
```

### 9.7 Audit Logging

**Track all data access:**
```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="logs/audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
audit_logger = logging.getLogger("audit")

class DataAccessLogger:
    @staticmethod
    def log_query(user: str, query: str, result_count: int):
        audit_logger.info(f"USER={user} | QUERY={query[:100]} | RESULTS={result_count}")
    
    @staticmethod
    def log_data_modification(user: str, operation: str, table: str, details: str):
        audit_logger.info(f"USER={user} | OP={operation} | TABLE={table} | DETAILS={details}")

# Usage
DataAccessLogger.log_query("analyst@example.com", "German startups with >100M funding", 4)
DataAccessLogger.log_data_modification("admin", "INSERT", "companies", "Added Proxima Fusion")
```

---

## 10. Success Criteria

### 10.1 Functional Success Metrics

| Criterion | Target | Measurement | Acceptance |
|-----------|--------|-------------|-----------|
| **Search Accuracy** | >95% relevant results | Manually validate 50 searches | All top 3 results relevant to query intent |
| **Query Response Time** | <2 seconds | Benchmark 100 NL queries | P99 latency <2s (excludes LLM cold start) |
| **Data Completeness** | 60+ companies, 8 metadata fields | Database row count | All companies from Fusion_Research.md parsed + zero data loss |
| **LLM Response Quality** | 4.5/5 stars (user rating) | User feedback survey | SWOT, market analysis, Q&A responses are accurate & actionable |
| **Report Generation** | 3 report types | Execute each template | Output is well-formatted, citable, includes visualizations |
| **Data Freshness** | <7 days | DB last-updated timestamp | All records within 7 days; automated weekly refresh runs |
| **Visualization Clarity** | 4.5/5 stars | User feedback | Charts are readable, legends clear, insights obvious |

### 10.2 Technical Success Metrics

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **Code Coverage** | >80% | pytest coverage report |
| **Test Suite Execution** | 100% pass rate | CI/CD pipeline |
| **Database Schema** | Normalized to 3NF | Schema review |
| **LangChain Integration** | Zero hallucinations on simple queries | Manual testing |
| **Performance** | <500ms UI response for filter changes | Browser profiling |
| **Uptime** | 99% (MVP local environment) | Manual log review |

### 10.3 User Adoption Metrics (Phase 1 → Phase 2 Gate)

| Metric | Target | Timeline |
|--------|--------|----------|
| **Daily Active Usage** | 4-5 days/week | By Week 8 (end of MVP) |
| **Queries per Session** | 3-5 | By Week 8 |
| **Time Saved vs. Manual Research** | 60% reduction | Subjective feedback |
| **Feature Usage Distribution** | >50% of features used | Analytics tracking (Phase 2) |

### 10.4 Phase Gate Criteria (MVP Completion)

**Gates to move from MVP (Week 8) → Production (Week 16):**

| Gate | Criteria | Owner |
|------|----------|-------|
| **Functional Completeness** | ✅ All US-1.x & US-2.x stories done; US-3.x & US-4.x >80% done | Product Owner |
| **Quality** | ✅ >80% test coverage; zero critical bugs | QA Lead |
| **Data** | ✅ 60+ companies, 8+ fields; Fusion_Research.md fully parsed | Data Lead |
| **Performance** | ✅ <2s query response; <500ms UI response | Tech Lead |
| **Security** | ✅ Input validation + SQL injection prevention verified | Security Lead |
| **User Feedback** | ✅ Positive feedback from initial user testing (4/5 satisfaction) | PM |

---

## 11. Risks & Mitigations

### 11.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **LangChain SQL Chain Hallucination** | Medium | High | Use few-shot examples, validate generated SQL against schema before execution, fallback to manual query if errors |
| **OpenAI API Rate Limits** | Low | Medium | Implement caching layer (24h TTL), batch queries, monitor usage, fallback to GPT-3.5 if GPT-4 exhausted |
| **SQLite Scalability** | Low | Medium | Pre-plan PostgreSQL migration path; document sharding strategy for 1000+ companies |
| **Markdown Parser Edge Cases** | Medium | Low | Use robust parser (markdown-it-py), add extensive test fixtures, manual review of parsed data |
| **LLM Bias/Inaccuracy** | Medium | High | Add human review step for critical reports, include uncertainty estimates ("High confidence: 95%"), cite sources |
| **Vector DB Index Staleness** | Low | Medium | Rebuild Chroma index on every data upload; set weekly refresh schedule |

### 11.2 Data Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Outdated Research Data** | High | High | Implement automated weekly news scraping + LLM summarization; flag stale data (>7 days) in UI |
| **Data Inconsistencies** | Medium | Medium | Validation rules on insert (Pydantic), foreign key constraints, data quality dashboard |
| **Source Attribution Loss** | Medium | Medium | Store metadata for every record (source URL, retrieval date, confidence), display in UI |
| **Parsing Errors in MD Ingestion** | Low | Medium | Extensive test coverage of parser; transaction rollback on errors; detailed error logs |
| **Sensitive Data Exposure** | Low | Critical | No PII stored (company names, website URLs are public); apply principle of least privilege to API keys |

### 11.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **OpenAI API Outage** | Low | Medium | Graceful degradation (disable NL query, show cached results), fallback to Claude via LangChain abstraction |
| **Single-User Productivity Bottleneck** | Low | Low | Code-first design allows easy multi-user onboarding in Phase 2 (add Streamlit auth) |
| **Data Backup Loss** | Low | Critical | Automated daily backups (GitHub Actions → S3), .db version control, rollback capability |
| **Unclear Requirements → Scope Creep** | Medium | High | Strict MVP scope enforcement (Section 4), regular stakeholder reviews, "out of scope" list visible |

### 11.4 Risk Mitigation Strategies

**Generic Mitigations (All Risks):**
- **Testing:** Unit tests (parsers, services), integration tests (end-to-end workflows), manual UAT with user
- **Documentation:** Architecture decision records (ADR), runbooks for common issues, troubleshooting guide
- **Monitoring:** Health checks (DB connectivity, LLM API availability), error alerting
- **Rollback Plan:** Database snapshots, git history, manual restore procedures
- **Contingency Staffing:** Document critical functions; bus factor > 1

**Specific Mitigation Workflows:**

**Risk: LangChain SQL Chain Hallucination**
```python
# Mitigation: Validate SQL before execution
from langchain_experimental.sql import SQLDatabaseChain

def safe_sql_query(nl_query: str, db: SQLDatabase):
    chain = SQLDatabaseChain.from_llm(llm, db)
    
    # Generate SQL
    sql = chain.run(nl_query)
    
    # Validate SQL
    if not is_valid_sql(sql, db.get_table_names()):
        raise ValueError("Generated SQL invalid")
    
    # Execute with timeout
    try:
        results = db.run(sql, timeout=5)
        return results
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return "Unable to execute query. Please refine your question."

def is_valid_sql(sql: str, allowed_tables: List[str]) -> bool:
    # Check for dangerous patterns
    dangerous = ['DROP', 'DELETE', 'UPDATE']
    if any(word in sql.upper() for word in dangerous):
        return False
    
    # Check table names
    parsed = sqlparse.parse(sql)[0]
    tables_in_query = extract_table_names(parsed)
    if not all(t in allowed_tables for t in tables_in_query):
        return False
    
    return True
```

**Risk: Outdated Research Data**
```python
# Mitigation: Automated news ingestion + age tracking
class NewsDigestTask:
    @staticmethod
    @scheduled_task(cron='0 9 * * MON')  # Monday 9 AM
    def fetch_and_summarize():
        news_items = scrape_fusion_news()  # Via httpx + BeautifulSoup
        summaries = [llm_summarize(item) for item in news_items]
        
        # Update company_updates table
        for summary in summaries:
            db.insert_update(
                company_id=extract_company_id(summary),
                content=summary['text'],
                source_url=summary['url'],
                fetched_at=datetime.now()
            )
        
        # Flag old data
        old_records = db.query(
            "SELECT * FROM companies WHERE last_updated < date('now', '-7 days')"
        )
        for record in old_records:
            flag_as_stale(record.id)

# UI displays stale data indicators
def company_card_ui(company):
    if is_stale(company):
        st.warning(f"Data >7 days old. Last updated: {company.last_updated}")
```

**Risk: Data Backup Loss**
```yaml
# GitHub Actions workflow: .github/workflows/backup.yml
name: Daily DB Backup
on:
  schedule:
    - cron: '0 1 * * *'  # 1 AM UTC daily

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Backup SQLite DB
        run: |
          cd research
          cp fusion_research.db fusion_research.db.backup
          tar -czf fusion_research_$(date +%Y%m%d).tar.gz fusion_research.db*
      
      - name: Upload to S3
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 cp fusion_research_*.tar.gz s3://fusion-research-backups/
      
      - name: Cleanup old backups
        run: |
          aws s3 rm s3://fusion-research-backups/ --exclude "*" \
            --include "fusion_research_*.tar.gz" \
            --region us-east-1 \
            --force \
            --recursive \
            --dryrun |
            grep "delete:" |
            awk '{print $NF}' |
            sort -r |
            tail -n +8 |  # Keep 7 recent backups
            xargs -I {} aws s3 rm s3://fusion-research-backups/{}
```

---

## Appendix A: Data Schema Summary

**Core Tables:**

```sql
-- Companies
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    company_type TEXT,  -- 'Startup', 'KMU', 'Konzern', 'Forschung'
    country TEXT,
    founded_year INTEGER,
    website TEXT,
    team_size INTEGER,
    description TEXT,
    last_updated TIMESTAMP,
    confidence_score REAL  -- 0.0-1.0
);

-- Funding
CREATE TABLE funding_rounds (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    amount_usd REAL,
    currency TEXT,
    date DATE,
    stage TEXT,  -- 'Pre-seed', 'Seed', 'Series A', etc.
    lead_investor TEXT,
    source_url TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

-- Technology
CREATE TABLE technologies (
    id INTEGER PRIMARY KEY,
    name TEXT,  -- 'Tokamak', 'Stellarator', 'Laser-ICF', 'FRC'
    trl INTEGER,  -- 1-9
    company_id INTEGER,
    description TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

-- Partnerships
CREATE TABLE partnerships (
    id INTEGER PRIMARY KEY,
    company_id_a INTEGER NOT NULL,
    company_id_b INTEGER,
    partner_type TEXT,  -- 'Technology', 'Distribution', 'Research'
    description TEXT,
    start_date DATE,
    end_date DATE,
    FOREIGN KEY(company_id_a) REFERENCES companies(id),
    FOREIGN KEY(company_id_b) REFERENCES companies(id)
);

-- Markets
CREATE TABLE markets (
    id INTEGER PRIMARY KEY,
    region TEXT,  -- 'Germany', 'DACH', 'BENELUX', 'Europe', 'USA', 'Global'
    market_size_2024_usd REAL,
    market_size_2040_usd REAL,
    cagr_percent REAL,
    regulatory_environment TEXT
);

-- Investors (normalized)
CREATE TABLE investors (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    investor_type TEXT,  -- 'VC', 'Corporate', 'Government', 'Family Office'
    country TEXT,
    description TEXT
);

-- Collaborations (normalized)
CREATE TABLE collaborations (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    partner_name TEXT NOT NULL,
    collaboration_type TEXT,  -- 'Research', 'Technology', 'Supply Chain'
    description TEXT,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

-- Funding-Investor junction table
CREATE TABLE funding_investors (
    id INTEGER PRIMARY KEY,
    funding_round_id INTEGER NOT NULL,
    investor_id INTEGER NOT NULL,
    is_lead INTEGER DEFAULT 0,
    FOREIGN KEY(funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY(investor_id) REFERENCES investors(id)
);
```

---

## Appendix B: Development Milestones (16-week Timeline)

| Week | Milestone | Deliverable | Notes |
|------|-----------|-------------|-------|
| 1-2 | Project Setup | Repo, dependencies, DB schema | Base infrastructure ready |
| 3-4 | MD Parser | Parse Fusion_Research.md → DB | 60+ companies ingested |
| 5-6 | Search & Filters | UI for company search, filters | US-1.1, US-1.2 complete |
| 6-7 | Company Profiles | Detail pages, competitive ranking | US-1.3 complete |
| 8 | **MVP GATE** | Dashboard, basic LLM Q&A | Functional completeness check |
| 9-10 | Market Dashboard | KPIs, charts, trends | US-2.1 complete |
| 11 | Report Generation | Template-based market reports | US-4.1 complete |
| 12-13 | News Digest | Automated scraping + summarization | US-3.3 complete |
| 14-15 | Polish & Testing | Bug fixes, performance tuning, UAT | >80% test coverage |
| 16 | **Production Gate** | Documentation, deployment runbook | Ready for release |

---

## Appendix C: Future Enhancements (Phase 2+)

- **Multi-user Auth:** Streamlit authentication, role-based dashboards (admin, analyst, viewer)
- **Advanced Analytics:** Clustering (similar companies), anomaly detection, predictive modeling
- **Data Export:** Excel/PowerPoint reports, CSV bulk export
- **Custom Alerting:** Notify on funding rounds, partnership announcements, TRL advances
- **Integration:** Slack bot, email integration, REST API for external tools
- **ML Ranking:** Recommendation engine ("Companies similar to Proxima Fusion")
- **Version History:** Track company profile changes over time
- **Collaborative Workspace:** Shared annotations, saved searches, team dashboards

---

**Document Version:** 1.1
**Last Updated:** February 7, 2026

## Appendix D: Interconnections

### Network JSON for Python Visualization

The supply chain network has been exported as `fusion_smr_network.json` with the following structure:

```json
{
  "metadata": {
    "title": "Fusion & SMR Industry Supply Chain Network",
    "source": "binding.energy 2026 Conference",
    "last_updated": "2026-02-06"
  },
  "nodes": [
    {
      "id": "marvel_fusion",
      "label": "Marvel Fusion",
      "type": "fusion_company",
      "country": "DE",
      "technology": "ICF_laser",
      "funding_eur_m": 385
    }
    // ... 74 more nodes
  ],
  "edges": [
    {
      "source": "marvel_fusion",
      "target": "siemens_energy",
      "type": "technology_partner",
      "since": 2022
    }
    // ... 75 more edges
  ]
}
```

**Node Types:**
- `fusion_company`, `smr_company`, `transmutation_company`
- `industrial_partner`, `research_institution`
- `investor`, `government`, `funding_program`
- `utility`, `consulting`, `site`, `fuel_company`

**Edge Types:**
- `investor`, `technology_partner`, `academic_partner`
- `spin_out`, `funding`, `supply_chain`
- `joint_venture`, `mou_partner`, `site_partner`

### Python Visualization Code

```python
import networkx as nx
import json

# Load network data
with open("fusion_smr_network.json", "r") as f:
    data = json.load(f)

# Create NetworkX graph
G = nx.Graph()

# Add nodes with attributes
for node in data["nodes"]:
    G.add_node(node["id"], **node)

# Add edges with attributes
for edge in data["edges"]:
    G.add_edge(edge["source"], edge["target"], **edge)

# Visualization with pyvis or matplotlib
from pyvis.network import Network
net = Network(height="800px", width="100%", notebook=True)
net.from_nx(G)
net.show("fusion_network.html")
```

---