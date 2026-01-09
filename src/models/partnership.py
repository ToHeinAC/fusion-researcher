"""Partnership and collaboration data models."""

from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PartnershipType(str, Enum):
    """Types of partnerships."""
    TECHNOLOGY = "Technology"
    RESEARCH = "Research"
    DISTRIBUTION = "Distribution"
    SUPPLY_CHAIN = "Supply Chain"
    INVESTMENT = "Investment"
    JOINT_VENTURE = "Joint Venture"
    LICENSING = "Licensing"
    STRATEGIC = "Strategic"
    ACADEMIC = "Academic"
    GOVERNMENT = "Government"
    OTHER = "Other"


class Partnership(BaseModel):
    """Partnership entity between companies/organizations."""
    
    id: Optional[int] = None
    company_id_a: int
    company_id_b: Optional[int] = None
    partner_name: Optional[str] = Field(default=None, max_length=200)
    partner_type: PartnershipType = PartnershipType.OTHER
    description: Optional[str] = None
    value_usd: Optional[float] = Field(default=None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="Active", max_length=50)
    key_deliverables: Optional[str] = None
    source_url: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @property
    def is_active(self) -> bool:
        """Check if partnership is currently active."""
        if self.status.lower() != "active":
            return False
        if self.end_date and self.end_date < date.today():
            return False
        return True


class Collaboration(BaseModel):
    """Research collaboration entity."""
    
    id: Optional[int] = None
    company_id: int
    institution_name: str = Field(..., max_length=200)
    institution_type: str = Field(default="Research Institute", max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    collaboration_type: str = Field(default="Research", max_length=100)
    description: Optional[str] = None
    funding_amount_usd: Optional[float] = Field(default=None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    key_outcomes: Optional[str] = None
    
    class Config:
        from_attributes = True
