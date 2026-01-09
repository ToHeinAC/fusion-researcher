"""Market and region data models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MarketRegion(str, Enum):
    """Geographic market regions."""
    GERMANY = "Germany"
    DACH = "DACH"  # Germany, Austria, Switzerland
    BENELUX = "BENELUX"
    EUROPE = "Europe"
    USA = "USA"
    NORTH_AMERICA = "North America"
    CHINA = "China"
    JAPAN = "Japan"
    ASIA_PACIFIC = "Asia-Pacific"
    GLOBAL = "Global"
    OTHER = "Other"


class Market(BaseModel):
    """Market entity for geographic regions."""
    
    id: Optional[int] = None
    region: MarketRegion = MarketRegion.GLOBAL
    region_name: str = Field(default="Global", max_length=100)
    market_size_2024_usd: Optional[float] = Field(default=None, ge=0)
    market_size_2030_usd: Optional[float] = Field(default=None, ge=0)
    market_size_2040_usd: Optional[float] = Field(default=None, ge=0)
    cagr_percent: Optional[float] = Field(default=None, ge=-100, le=1000)
    company_count: int = Field(default=0, ge=0)
    total_funding_usd: Optional[float] = Field(default=None, ge=0)
    regulatory_environment: Optional[str] = None
    growth_drivers: Optional[str] = None
    key_challenges: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def market_size_2024_display(self) -> str:
        """Format 2024 market size for display."""
        if self.market_size_2024_usd is None:
            return "Unknown"
        if self.market_size_2024_usd >= 1_000_000_000:
            return f"${self.market_size_2024_usd / 1_000_000_000:.1f}B"
        if self.market_size_2024_usd >= 1_000_000:
            return f"${self.market_size_2024_usd / 1_000_000:.1f}M"
        return f"${self.market_size_2024_usd / 1_000:.1f}K"


class MarketTrend(BaseModel):
    """Market trend data point."""
    
    id: Optional[int] = None
    market_id: int
    year: int = Field(..., ge=2000, le=2100)
    metric_name: str = Field(..., max_length=100)
    metric_value: float
    metric_unit: str = Field(default="USD", max_length=50)
    source: Optional[str] = None
    
    class Config:
        from_attributes = True


class RegulatoryMilestone(BaseModel):
    """Regulatory milestone entity."""
    
    id: Optional[int] = None
    jurisdiction: str = Field(..., max_length=100)
    policy_name: str = Field(..., max_length=200)
    date: Optional[str] = None
    description: Optional[str] = None
    impact_assessment: Optional[str] = None
    affected_companies: Optional[str] = None
    source_url: Optional[str] = None
    
    class Config:
        from_attributes = True
