"""Funding and investor data models."""

from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FundingStage(str, Enum):
    """Funding round stages."""
    PRE_SEED = "Pre-seed"
    SEED = "Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    SERIES_D = "Series D+"
    GRANT = "Grant"
    DEBT = "Debt"
    IPO = "IPO"
    UNKNOWN = "Unknown"


class FundingRound(BaseModel):
    """Funding round entity."""
    
    id: Optional[int] = None
    company_id: int
    amount_usd: Optional[float] = Field(default=None, ge=0)
    amount_original: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=10)
    date: Optional[date] = None
    stage: FundingStage = FundingStage.UNKNOWN
    lead_investor: Optional[str] = Field(default=None, max_length=200)
    all_investors: Optional[str] = None
    valuation_usd: Optional[float] = Field(default=None, ge=0)
    source_url: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def amount_display(self) -> str:
        """Format amount for display."""
        if self.amount_usd is None:
            return "Undisclosed"
        if self.amount_usd >= 1_000_000_000:
            return f"${self.amount_usd / 1_000_000_000:.1f}B"
        if self.amount_usd >= 1_000_000:
            return f"${self.amount_usd / 1_000_000:.1f}M"
        if self.amount_usd >= 1_000:
            return f"${self.amount_usd / 1_000:.1f}K"
        return f"${self.amount_usd:.0f}"


class Investor(BaseModel):
    """Investor entity."""
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    investor_type: str = Field(default="Unknown", max_length=50)
    country: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=500)
    portfolio_focus: Optional[str] = None
    total_investments_count: int = Field(default=0, ge=0)
    total_invested_usd: Optional[float] = Field(default=None, ge=0)
    
    class Config:
        from_attributes = True


class InvestorType(str, Enum):
    """Types of investors."""
    GENERALIST_VC = "Generalist VC"
    SPECIALIZED_VC = "Specialized VC"
    CORPORATE_VC = "Corporate VC"
    FAMILY_OFFICE = "Family Office"
    GOVERNMENT = "Government"
    ANGEL = "Angel"
    STRATEGIC = "Strategic"
    UNKNOWN = "Unknown"
