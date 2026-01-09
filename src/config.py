"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    llm_model: str = Field(default="qwen3:8b", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    max_response_tokens: int = Field(default=2000, alias="MAX_RESPONSE_TOKENS")

    # Tavily Web Search
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    
    # Database
    database_path: str = Field(default="research/fusion_research.db", alias="DATABASE_PATH")
    chroma_db_path: str = Field(default="research/chroma_data", alias="CHROMA_DB_PATH")
    
    # News Scraping
    news_scrape_frequency: str = Field(default="weekly", alias="NEWS_SCRAPE_FREQUENCY")
    news_sources: str = Field(
        default="fusionindustryassociation,crunchbase,fusionenergybase",
        alias="NEWS_SOURCES"
    )
    
    # Caching
    query_cache_ttl: int = Field(default=3600, alias="QUERY_CACHE_TTL")
    cache_max_size: int = Field(default=100, alias="CACHE_MAX_SIZE")
    
    # Streamlit
    streamlit_server_headless: bool = Field(default=True, alias="STREAMLIT_SERVER_HEADLESS")
    streamlit_server_port: int = Field(default=8501, alias="STREAMLIT_SERVER_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def database_path_resolved(self) -> Path:
        """Get resolved database path."""
        return Path(self.database_path).resolve()
    
    @property
    def chroma_db_path_resolved(self) -> Path:
        """Get resolved ChromaDB path."""
        return Path(self.chroma_db_path).resolve()
    
    @property
    def news_sources_list(self) -> list[str]:
        """Get news sources as a list."""
        return [s.strip() for s in self.news_sources.split(",")]


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Convenience function for optional loading (when .env might not exist)
def get_settings_optional() -> Optional[Settings]:
    """Get settings, returning None if configuration is missing."""
    try:
        return Settings()
    except Exception:
        return None
