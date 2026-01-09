"""Technology and TRL data models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TechnologyApproach(str, Enum):
    """Fusion technology approaches."""
    TOKAMAK = "Tokamak"
    STELLARATOR = "Stellarator"
    LASER_ICF = "Laser-ICF"
    FRC = "FRC"  # Field-Reversed Configuration
    MAGNETIZED_TARGET = "Magnetized Target"
    Z_PINCH = "Z-Pinch"
    INERTIAL_ELECTROSTATIC = "Inertial Electrostatic"
    MIRROR = "Mirror"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class Technology(BaseModel):
    """Technology entity linked to a company."""
    
    id: Optional[int] = None
    company_id: int
    approach: TechnologyApproach = TechnologyApproach.UNKNOWN
    name: Optional[str] = Field(default=None, max_length=200)
    trl: Optional[int] = Field(default=None, ge=1, le=9)
    trl_justification: Optional[str] = None
    description: Optional[str] = None
    key_materials: Optional[str] = None
    key_challenges: Optional[str] = None
    development_stage: Optional[str] = Field(default=None, max_length=100)
    target_commercialization_year: Optional[int] = Field(default=None, ge=2020, le=2100)
    
    class Config:
        from_attributes = True


class TRLLevel(BaseModel):
    """Technology Readiness Level definition."""
    
    level: int = Field(..., ge=1, le=9)
    name: str
    description: str
    typical_activities: str
    
    @classmethod
    def get_all_levels(cls) -> list["TRLLevel"]:
        """Get all TRL level definitions."""
        return [
            cls(
                level=1,
                name="Basic principles observed",
                description="Scientific research begins to be translated into applied R&D",
                typical_activities="Paper studies, scientific literature review"
            ),
            cls(
                level=2,
                name="Technology concept formulated",
                description="Practical applications can be invented",
                typical_activities="Concept development, feasibility studies"
            ),
            cls(
                level=3,
                name="Experimental proof of concept",
                description="Active R&D is initiated",
                typical_activities="Lab experiments, component validation"
            ),
            cls(
                level=4,
                name="Technology validated in lab",
                description="Basic technological components integrated",
                typical_activities="Component integration, lab testing"
            ),
            cls(
                level=5,
                name="Technology validated in relevant environment",
                description="Fidelity of technology increases significantly",
                typical_activities="Subsystem testing, simulated environment"
            ),
            cls(
                level=6,
                name="Technology demonstrated in relevant environment",
                description="Representative model or prototype system tested",
                typical_activities="Prototype demonstration, pilot plant"
            ),
            cls(
                level=7,
                name="System prototype demonstration",
                description="Prototype near or at planned operational system",
                typical_activities="Full-scale prototype, operational testing"
            ),
            cls(
                level=8,
                name="System complete and qualified",
                description="Technology proven to work in final form",
                typical_activities="System qualification, certification"
            ),
            cls(
                level=9,
                name="Actual system proven",
                description="Actual application of technology in operational environment",
                typical_activities="Commercial operation, deployment"
            ),
        ]
