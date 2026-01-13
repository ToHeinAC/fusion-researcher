"""Models for LLM-powered database update proposals and audit logging."""

import json
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class ProposalStatus(str, Enum):
    """Status of an update proposal."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPLIED = "auto_applied"


class EntityType(str, Enum):
    """Types of entities that can be updated."""
    COMPANY = "company"
    FUNDING = "funding"
    TECHNOLOGY = "technology"
    MARKET = "market"
    PARTNERSHIP = "partnership"


class ChangeSource(str, Enum):
    """Source of a data change."""
    MANUAL = "manual"
    AUTO_UPDATE = "auto_update"
    IMPORT = "import"
    USER_EDIT = "user_edit"


class SourceReliability(Enum):
    """Reliability tiers for data sources with associated confidence scores."""
    COMPANY_OFFICIAL = ("company_official", 0.95)
    FINANCIAL_DATABASE = ("financial_database", 0.90)
    MAJOR_NEWS = ("major_news", 0.85)
    INDUSTRY_PUBLICATION = ("industry_publication", 0.80)
    GENERAL_NEWS = ("general_news", 0.70)
    SOCIAL_MEDIA = ("social_media", 0.50)
    UNVERIFIED = ("unverified", 0.30)

    def __init__(self, label: str, score: float):
        self.label = label
        self.score = score


# Domain patterns for source reliability classification
SOURCE_DOMAIN_PATTERNS = {
    SourceReliability.COMPANY_OFFICIAL: [
        "proxima-fusion.com", "cfs.energy", "helionenergy.com",
        "tae.com", "generalfusion.com", "focused-energy.world",
        "marvelfusion.com", "gauss-fusion.com", "typeoneenergy.com",
        "firstlightfusion.com", "tokamak.energy", "zap.energy",
    ],
    SourceReliability.FINANCIAL_DATABASE: [
        "crunchbase.com", "pitchbook.com", "bloomberg.com",
        "dealroom.co", "cbinsights.com",
    ],
    SourceReliability.MAJOR_NEWS: [
        "reuters.com", "techcrunch.com", "ft.com", "wsj.com",
        "nytimes.com", "theguardian.com", "bbc.com", "bbc.co.uk",
        "cnbc.com", "businessinsider.com", "forbes.com",
    ],
    SourceReliability.INDUSTRY_PUBLICATION: [
        "fusionindustryassociation.org", "world-nuclear-news.org",
        "iter.org", "energy.gov", "nature.com", "science.org",
        "nucnet.org", "ans.org", "iaea.org",
    ],
    SourceReliability.GENERAL_NEWS: [
        "news.google.com", "yahoo.com", "msn.com", "bing.com",
    ],
    SourceReliability.SOCIAL_MEDIA: [
        "linkedin.com", "twitter.com", "x.com", "medium.com",
    ],
}


@dataclass
class DataSource:
    """A web source used for extracting update information."""
    url: str
    title: str
    reliability: SourceReliability
    snippet: str = ""
    fetched_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "title": self.title,
            "reliability": self.reliability.label,
            "reliability_score": self.reliability.score,
            "snippet": self.snippet,
            "fetched_at": self.fetched_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataSource":
        """Create from dictionary."""
        reliability = SourceReliability.UNVERIFIED
        for r in SourceReliability:
            if r.label == data.get("reliability"):
                reliability = r
                break
        return cls(
            url=data["url"],
            title=data["title"],
            reliability=reliability,
            snippet=data.get("snippet", ""),
            fetched_at=datetime.fromisoformat(data["fetched_at"])
            if data.get("fetched_at")
            else datetime.now(),
        )


@dataclass
class UpdateProposal:
    """A proposed update to an entity field."""
    entity_type: EntityType
    entity_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    confidence_score: float
    sources: list[DataSource]
    search_query: str
    status: ProposalStatus = ProposalStatus.PENDING
    id: Optional[int] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None

    def is_significant_change(self) -> bool:
        """Check if the proposed change is significant."""
        if self.old_value is None and self.new_value is None:
            return False
        if self.old_value == self.new_value:
            return False
        # For numeric values, check if change is >5%
        try:
            old_num = float(self.old_value) if self.old_value else 0
            new_num = float(self.new_value) if self.new_value else 0
            if old_num > 0:
                change_pct = abs(new_num - old_num) / old_num
                return change_pct > 0.05
            return new_num > 0
        except (ValueError, TypeError):
            # For text values, any change is significant
            return self.old_value != self.new_value

    @property
    def source_urls(self) -> list[str]:
        """Get list of source URLs."""
        return [s.url for s in self.sources]

    def sources_to_json(self) -> str:
        """Serialize sources to JSON string."""
        return json.dumps([s.to_dict() for s in self.sources])

    @classmethod
    def sources_from_json(cls, json_str: str) -> list[DataSource]:
        """Deserialize sources from JSON string."""
        if not json_str:
            return []
        data = json.loads(json_str)
        return [DataSource.from_dict(d) for d in data]

    def to_db_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "confidence_score": self.confidence_score,
            "sources": self.sources_to_json(),
            "search_query": self.search_query,
            "extracted_at": self.extracted_at.isoformat(),
            "status": self.status.value,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "notes": self.notes,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "UpdateProposal":
        """Create from database row."""
        return cls(
            id=row["id"],
            entity_type=EntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            field_name=row["field_name"],
            old_value=row["old_value"],
            new_value=row["new_value"],
            confidence_score=row["confidence_score"] or 0.0,
            sources=cls.sources_from_json(row["sources"]),
            search_query=row["search_query"] or "",
            extracted_at=datetime.fromisoformat(row["extracted_at"])
            if row["extracted_at"]
            else datetime.now(),
            status=ProposalStatus(row["status"]),
            reviewed_by=row["reviewed_by"],
            reviewed_at=datetime.fromisoformat(row["reviewed_at"])
            if row["reviewed_at"]
            else None,
            notes=row["notes"],
        )


@dataclass
class AuditLogEntry:
    """An entry in the audit log tracking data changes."""
    entity_type: EntityType
    entity_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    change_source: ChangeSource
    changed_by: str
    proposal_id: Optional[int] = None
    id: Optional[int] = None
    changed_at: datetime = field(default_factory=datetime.now)

    def to_db_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_source": self.change_source.value,
            "changed_at": self.changed_at.isoformat(),
            "changed_by": self.changed_by,
            "proposal_id": self.proposal_id,
        }

    @classmethod
    def from_db_row(cls, row: dict) -> "AuditLogEntry":
        """Create from database row."""
        return cls(
            id=row["id"],
            entity_type=EntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            field_name=row["field_name"],
            old_value=row["old_value"],
            new_value=row["new_value"],
            change_source=ChangeSource(row["change_source"]),
            changed_at=datetime.fromisoformat(row["changed_at"])
            if row["changed_at"]
            else datetime.now(),
            changed_by=row["changed_by"] or "unknown",
            proposal_id=row["proposal_id"],
        )


# Configuration for updateable fields
UPDATEABLE_FIELDS = {
    EntityType.COMPANY: {
        "total_funding_usd": {
            "search_template": "{company_name} funding round 2024 2025 million",
            "extract_type": "currency",
            "description": "Total funding raised (USD)",
        },
        "team_size": {
            "search_template": "{company_name} employees team size headcount",
            "extract_type": "integer",
            "description": "Number of employees",
        },
        "trl": {
            "search_template": "{company_name} technology readiness level milestone progress",
            "extract_type": "integer",
            "description": "Technology Readiness Level (1-9)",
        },
        "key_partnerships": {
            "search_template": "{company_name} partnership agreement collaboration",
            "extract_type": "text",
            "description": "Key partnerships and collaborations",
        },
        "key_investors": {
            "search_template": "{company_name} investors funding round led by",
            "extract_type": "text",
            "description": "Key investors",
        },
    },
    EntityType.FUNDING: {
        "amount_usd": {
            "search_template": "{company_name} funding raised series amount",
            "extract_type": "currency",
            "description": "Funding amount (USD)",
        },
        "lead_investor": {
            "search_template": "{company_name} funding led by investor",
            "extract_type": "text",
            "description": "Lead investor",
        },
    },
    EntityType.TECHNOLOGY: {
        "trl": {
            "search_template": "{company_name} technology readiness demonstration",
            "extract_type": "integer",
            "description": "Technology Readiness Level (1-9)",
        },
        "development_stage": {
            "search_template": "{company_name} development stage prototype commercial",
            "extract_type": "text",
            "description": "Development stage",
        },
    },
    EntityType.MARKET: {
        "market_size_2024_usd": {
            "search_template": "fusion energy market size 2024 billion",
            "extract_type": "currency",
            "description": "Market size 2024 (USD)",
        },
        "cagr_percent": {
            "search_template": "fusion energy market CAGR growth rate",
            "extract_type": "percentage",
            "description": "Compound Annual Growth Rate (%)",
        },
    },
}
