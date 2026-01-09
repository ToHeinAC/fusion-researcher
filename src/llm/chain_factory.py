"""LangChain factory for LLM integration with Ollama."""

from typing import Optional, Literal
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate

# Available Ollama models
AVAILABLE_MODELS = ["qwen3:8b", "qwen3:14b", "gpt-oss:20b"]
DEFAULT_MODEL = "qwen3:8b"


def get_llm(
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    base_url: str = "http://localhost:11434",
) -> ChatOllama:
    """Create a ChatOllama instance for local LLM."""
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=base_url,
    )


class ChainFactory:
    """Factory for creating LangChain chains with Ollama."""
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        db_path: str = "research/fusion_research.db",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.temperature = temperature
        self.db_path = db_path
        self.base_url = base_url
        self._llm: Optional[ChatOllama] = None
        self._db: Optional[SQLDatabase] = None
    
    @property
    def llm(self) -> ChatOllama:
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = get_llm(
                model=self.model,
                temperature=self.temperature,
                base_url=self.base_url,
            )
        return self._llm
    
    @property
    def db(self) -> SQLDatabase:
        """Get or create SQLDatabase instance."""
        if self._db is None:
            self._db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        return self._db
    
    def create_sql_chain(self):
        """Create SQL query chain for natural language to SQL conversion."""
        from langchain_experimental.sql import SQLDatabaseChain
        return SQLDatabaseChain.from_llm(self.llm, self.db, verbose=False)
    
    def create_qa_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for Q&A."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert analyst specializing in the nuclear fusion industry.
You have access to comprehensive data about fusion companies, technologies, funding, and market trends.
Provide accurate, data-driven answers with specific citations when available.
Format responses with bullet points for clarity.
If you don't have specific data, acknowledge the limitation."""),
            ("human", "{question}"),
        ])
    
    def create_swot_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for SWOT analysis."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a strategic analyst specializing in the nuclear fusion industry.
Generate a comprehensive SWOT analysis based on the provided company data.
Each section should have 3-4 bullet points with specific data references.
Format as Markdown with clear sections."""),
            ("human", """Generate a SWOT analysis for {company_name}.

Company Data:
{company_data}

Market Context:
{market_context}

Provide:
## Strengths
- (3-4 data-backed points)

## Weaknesses
- (3-4 data-backed points)

## Opportunities
- (3-4 data-backed points)

## Threats
- (3-4 data-backed points)"""),
        ])
    
    def create_comparison_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for company comparison."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert analyst comparing fusion companies.
Provide objective, data-driven comparisons across key metrics.
Highlight relative strengths and weaknesses.
Format as a structured comparison table and narrative summary."""),
            ("human", """Compare these fusion companies:

Company A: {company_a_name}
{company_a_data}

Company B: {company_b_name}
{company_b_data}

Provide:
1. Side-by-side metrics comparison table
2. Key differentiators
3. Competitive positioning analysis
4. Investment considerations"""),
        ])
    
    def create_market_analysis_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for market analysis."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a market analyst specializing in the fusion energy sector.
Provide data-driven market insights with specific numbers and trends.
Include regional analysis and technology segmentation.
Format with clear sections and bullet points."""),
            ("human", """Analyze the fusion energy market based on this data:

{market_data}

Focus on:
1. Market size and growth projections
2. Regional distribution
3. Technology trends
4. Investment landscape
5. Key drivers and challenges"""),
        ])
