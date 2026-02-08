"""Unified CRUD service wrapping all entity repositories with audit logging."""

from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from src.data.database import Database, get_database
from src.data.repositories import (
    CollaborationRepository,
    CompanyRepository,
    FundingRepository,
    InvestorRepository,
    MarketRepository,
    PartnershipRepository,
    TechnologyRepository,
)
from src.models.company import Company, CompanyType
from src.models.funding import FundingRound, FundingStage, Investor
from src.models.market import Market, MarketRegion
from src.models.partnership import Collaboration, Partnership, PartnershipType
from src.models.technology import Technology, TechnologyApproach
from src.models.update_proposal import ChangeSource, EntityType
from src.services.audit_service import AuditService

# Maps entity type string to (model class, EntityType enum)
ENTITY_CONFIG: dict[str, dict[str, Any]] = {
    "companies": {
        "model": Company,
        "entity_type": EntityType.COMPANY,
        "label": "Company",
    },
    "funding": {
        "model": FundingRound,
        "entity_type": EntityType.FUNDING,
        "label": "Funding Round",
    },
    "technologies": {
        "model": Technology,
        "entity_type": EntityType.TECHNOLOGY,
        "label": "Technology",
    },
    "markets": {
        "model": Market,
        "entity_type": EntityType.MARKET,
        "label": "Market",
    },
    "partnerships": {
        "model": Partnership,
        "entity_type": EntityType.PARTNERSHIP,
        "label": "Partnership",
    },
    "investors": {
        "model": Investor,
        "entity_type": EntityType.INVESTOR,
        "label": "Investor",
    },
    "collaborations": {
        "model": Collaboration,
        "entity_type": EntityType.COLLABORATION,
        "label": "Collaboration",
    },
}


class CrudService:
    """Unified CRUD interface for all entity types with audit logging."""

    def __init__(self, db: Database | None = None):
        self.db = db or get_database()
        self.audit = AuditService(self.db)

        self._repos = {
            "companies": CompanyRepository(self.db),
            "funding": FundingRepository(self.db),
            "technologies": TechnologyRepository(self.db),
            "markets": MarketRepository(self.db),
            "partnerships": PartnershipRepository(self.db),
            "investors": InvestorRepository(self.db),
            "collaborations": CollaborationRepository(self.db),
        }

    @staticmethod
    def entity_types() -> list[str]:
        return list(ENTITY_CONFIG.keys())

    @staticmethod
    def get_model_class(entity_type: str) -> type[BaseModel]:
        return ENTITY_CONFIG[entity_type]["model"]

    @staticmethod
    def get_label(entity_type: str) -> str:
        return ENTITY_CONFIG[entity_type]["label"]

    def list_entities(self, entity_type: str, limit: int = 200) -> list[BaseModel]:
        """List all entities of the given type."""
        repo = self._repos[entity_type]
        return repo.get_all(limit=limit)

    def get_entity(self, entity_type: str, entity_id: int) -> Optional[BaseModel]:
        """Get a single entity by type and ID."""
        repo = self._repos[entity_type]
        return repo.get_by_id(entity_id)

    def create_entity(self, entity_type: str, data: dict) -> int:
        """Create a new entity. Returns new ID."""
        model_cls = ENTITY_CONFIG[entity_type]["model"]
        entity = model_cls(**data)

        repo = self._repos[entity_type]
        new_id = repo.create(entity)

        self.audit.log_change(
            entity_type=ENTITY_CONFIG[entity_type]["entity_type"],
            entity_id=new_id,
            field_name="*",
            old_value=None,
            new_value=f"Created {ENTITY_CONFIG[entity_type]['label']}",
            change_source=ChangeSource.USER_EDIT,
            changed_by="user",
        )
        return new_id

    def update_entity(self, entity_type: str, entity_id: int, data: dict) -> bool:
        """Update an existing entity. Logs changed fields."""
        repo = self._repos[entity_type]
        old_entity = repo.get_by_id(entity_id)
        if old_entity is None:
            return False

        model_cls = ENTITY_CONFIG[entity_type]["model"]
        data["id"] = entity_id
        updated = model_cls(**data)

        result = repo.update(updated)
        if not result:
            return False

        # Log changed fields
        et = ENTITY_CONFIG[entity_type]["entity_type"]
        old_dict = old_entity.model_dump()
        new_dict = updated.model_dump()
        for field_name in new_dict:
            if field_name == "id":
                continue
            old_val = old_dict.get(field_name)
            new_val = new_dict.get(field_name)
            if str(old_val) != str(new_val):
                self.audit.log_change(
                    entity_type=et,
                    entity_id=entity_id,
                    field_name=field_name,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                    change_source=ChangeSource.USER_EDIT,
                    changed_by="user",
                )
        return True

    def delete_entity(self, entity_type: str, entity_id: int) -> bool:
        """Delete an entity by type and ID."""
        repo = self._repos[entity_type]
        old_entity = repo.get_by_id(entity_id)
        if old_entity is None:
            return False

        result = repo.delete(entity_id)
        if result:
            self.audit.log_change(
                entity_type=ENTITY_CONFIG[entity_type]["entity_type"],
                entity_id=entity_id,
                field_name="*",
                old_value=str(getattr(old_entity, "name", None) or entity_id),
                new_value=None,
                change_source=ChangeSource.USER_EDIT,
                changed_by="user",
            )
        return result

    def get_company_names(self) -> dict[int, str]:
        """Helper: return {id: name} for all companies (for FK dropdowns)."""
        companies = self._repos["companies"].get_all(limit=500)
        return {c.id: c.name for c in companies}
