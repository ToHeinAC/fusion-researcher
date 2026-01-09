"""Company data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CompanyType(str, Enum):
    """Types of fusion companies."""
    STARTUP = "Startup"
    KMU = "KMU"  # Small/Medium Enterprise
    KONZERN = "Konzern"  # Corporation
    FORSCHUNG = "Forschung"  # Research Institute
    UNKNOWN = "Unknown"


class Company(BaseModel):
    """Fusion company entity."""
    
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    company_type: CompanyType = CompanyType.UNKNOWN
    country: str = Field(default="Unknown", max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    founded_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    website: Optional[str] = Field(default=None, max_length=500)
    team_size: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    technology_approach: Optional[str] = Field(default=None, max_length=100)
    trl: Optional[int] = Field(default=None, ge=1, le=9)
    trl_justification: Optional[str] = None
    total_funding_usd: Optional[float] = Field(default=None, ge=0)
    key_investors: Optional[str] = None
    key_partnerships: Optional[str] = None
    competitive_positioning: Optional[str] = None
    last_updated: Optional[datetime] = None
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    source_url: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def funding_display(self) -> str:
        """Format funding for display."""
        if self.total_funding_usd is None:
            return "Unknown"
        if self.total_funding_usd >= 1_000_000_000:
            return f"${self.total_funding_usd / 1_000_000_000:.1f}B"
        if self.total_funding_usd >= 1_000_000:
            return f"${self.total_funding_usd / 1_000_000:.1f}M"
        if self.total_funding_usd >= 1_000:
            return f"${self.total_funding_usd / 1_000:.1f}K"
        return f"${self.total_funding_usd:.0f}"
    
    @property
    def trl_display(self) -> str:
        """Format TRL for display with description."""
        trl_descriptions = {
            1: "Basic principles observed",
            2: "Technology concept formulated",
            3: "Experimental proof of concept",
            4: "Technology validated in lab",
            5: "Technology validated in relevant environment",
            6: "Technology demonstrated in relevant environment",
            7: "System prototype demonstration",
            8: "System complete and qualified",
            9: "Actual system proven in operational environment",
        }
        if self.trl is None:
            return "TRL: Unknown"
        desc = trl_descriptions.get(self.trl, "")
        return f"TRL {self.trl}: {desc}"


class CompanyDTO(BaseModel):
    """Data Transfer Object for company search results."""
    
    id: int
    name: str
    company_type: str
    country: str
    founded_year: Optional[int]
    total_funding_usd: Optional[float]
    trl: Optional[int]
    technology_approach: Optional[str]
    team_size: Optional[int]
    
    @property
    def funding_display(self) -> str:
        """Format funding for display."""
        if self.total_funding_usd is None:
            return "Unknown"
        if self.total_funding_usd >= 1_000_000_000:
            return f"${self.total_funding_usd / 1_000_000_000:.1f}B"
        if self.total_funding_usd >= 1_000_000:
            return f"${self.total_funding_usd / 1_000_000:.1f}M"
        return f"${self.total_funding_usd / 1_000:.1f}K"
