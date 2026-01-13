"""Pydantic models for markdown merge and database sync operations."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass, field


class MergeType(str, Enum):
    """Type of merge operation."""
    ADDITION = "addition"
    UPDATE = "update"
    CONFLICT = "conflict"
    NO_CHANGE = "no_change"


class DiffType(str, Enum):
    """Type of difference between sections."""
    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class MergeConfig:
    """Configuration for markdown merger."""
    chunk_size: int = 4000
    overlap_size: int = 500
    backup_suffix: str = ".backup"
    preserve_structure: bool = True
    llm_timeout: float = 120.0
    max_retries: int = 3
    research_dir: str = "research"


@dataclass
class MergeResult:
    """Result of a merge operation."""
    success: bool = False
    original_path: Optional[Path] = None
    backup_path: Optional[Path] = None
    merged_path: Optional[Path] = None
    sections_merged: int = 0
    companies_added: int = 0
    companies_updated: int = 0
    conflicts_resolved: int = 0
    errors: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)


@dataclass
class SectionDiff:
    """Difference between two markdown sections."""
    section_name: str
    original_content: Optional[str] = None
    update_content: Optional[str] = None
    diff_type: DiffType = DiffType.UNCHANGED

    @property
    def has_original(self) -> bool:
        return self.original_content is not None

    @property
    def has_update(self) -> bool:
        return self.update_content is not None


@dataclass
class CompanyDiff:
    """Difference between two company entries."""
    company_name: str
    location: str
    original_content: Optional[str] = None
    update_content: Optional[str] = None
    diff_type: DiffType = DiffType.UNCHANGED


@dataclass
class MergeOperation:
    """A single merge operation record."""
    merge_type: MergeType
    section_name: str
    entity_name: Optional[str] = None
    original_hash: Optional[str] = None
    merged_hash: Optional[str] = None
    confidence: float = 0.8
    notes: Optional[str] = None


@dataclass
class MergeReport:
    """Complete merge operation report."""
    timestamp: datetime = field(default_factory=datetime.now)
    base_file: str = ""
    update_file: str = ""
    output_file: str = ""
    operations: list[MergeOperation] = field(default_factory=list)
    total_sections: int = 0
    sections_merged: int = 0
    companies_added: int = 0
    companies_updated: int = 0
    conflicts: int = 0
    success: bool = True
    error_message: Optional[str] = None

    def add_operation(self, operation: MergeOperation) -> None:
        """Add a merge operation to the report."""
        self.operations.append(operation)


@dataclass
class SyncConfig:
    """Configuration for database sync."""
    auto_apply_threshold: float = 0.90
    require_review_threshold: float = 0.70
    batch_size: int = 10
    dry_run: bool = False


@dataclass
class SyncResult:
    """Result of database sync operation."""
    companies_processed: int = 0
    companies_added: int = 0
    companies_updated: int = 0
    fields_updated: int = 0
    proposals_created: int = 0
    proposals_auto_applied: int = 0
    conflicts_found: int = 0
    errors: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)


@dataclass
class FieldChange:
    """A proposed change to a field."""
    company_id: int
    company_name: str
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_type: Literal["add", "update", "delete"] = "update"
    confidence: float = 0.8
    source: str = "markdown_sync"
    validated: bool = False
    applied: bool = False

    def is_significant(self, tolerance: float = 0.0) -> bool:
        """Check if the change is significant based on tolerance."""
        if self.old_value is None and self.new_value is not None:
            return True
        if self.old_value is not None and self.new_value is None:
            return True
        if self.old_value == self.new_value:
            return False

        # For numeric values, check tolerance
        try:
            old_num = float(self.old_value) if self.old_value else 0
            new_num = float(self.new_value) if self.new_value else 0
            if old_num > 0:
                diff_pct = abs(new_num - old_num) / old_num
                return diff_pct > tolerance
            return old_num != new_num
        except (ValueError, TypeError):
            # For text values, any difference is significant
            return True


# Field comparison configuration
COMPARABLE_FIELDS = {
    "total_funding_usd": {"type": "currency", "tolerance": 0.10},
    "team_size": {"type": "integer", "tolerance": 0.15},
    "trl": {"type": "integer", "tolerance": 0.0},
    "technology_approach": {"type": "text", "tolerance": None},
    "key_investors": {"type": "text", "tolerance": None},
    "key_partnerships": {"type": "text", "tolerance": None},
    "description": {"type": "text", "tolerance": None},
    "founded_year": {"type": "integer", "tolerance": 0.0},
    "city": {"type": "text", "tolerance": None},
    "country": {"type": "text", "tolerance": None},
}
