"""Database sync service for updating DB from merged markdown using local LLM."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser

from src.data.database import Database, get_database
from src.data.repositories import CompanyRepository
from src.data.parsers.markdown_parser import parse_fusion_research, MarkdownParser
from src.models.company import Company
from src.models.merge_models import (
    SyncConfig,
    SyncResult,
    FieldChange,
    COMPARABLE_FIELDS,
)
from src.models.update_proposal import (
    UpdateProposal,
    AuditLogEntry,
    DataSource,
    EntityType,
    ProposalStatus,
    ChangeSource,
    SourceReliability,
)
from src.llm.merge_prompts import (
    VALIDATE_CHANGE_PROMPT,
    FUZZY_MATCH_PROMPT,
)
from src.llm.chain_factory import get_llm


class DatabaseSyncService:
    """Service for syncing database from markdown with LLM validation."""

    def __init__(
        self,
        db: Optional[Database] = None,
        llm: Optional[ChatOllama] = None,
        config: Optional[SyncConfig] = None,
        db_path: str = "research/fusion_research.db",
    ):
        self.db = db if db else get_database(db_path)
        self.llm = llm
        self.config = config or SyncConfig()
        self.company_repo = CompanyRepository(self.db)

    def _get_llm(self) -> ChatOllama:
        """Get or create LLM instance."""
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    def sync_from_markdown(
        self,
        markdown_path: str = "research/Fusion_Research.md",
    ) -> SyncResult:
        """
        Sync database from markdown file.

        Args:
            markdown_path: Path to the markdown file

        Returns:
            SyncResult with operation details
        """
        result = SyncResult()

        try:
            # Parse markdown
            parsed_data = parse_fusion_research(markdown_path)

            # Get all existing companies from DB
            db_companies = {c.name: c for c in self.company_repo.get_all(limit=1000)}

            # Process companies in batches
            for i in range(0, len(parsed_data.companies), self.config.batch_size):
                batch = parsed_data.companies[i:i + self.config.batch_size]
                batch_changes = self._process_company_batch(batch, db_companies)

                for change in batch_changes:
                    if change.confidence >= self.config.auto_apply_threshold:
                        if not self.config.dry_run:
                            self._apply_change(change)
                        result.proposals_auto_applied += 1
                        result.fields_updated += 1
                    elif change.confidence >= self.config.require_review_threshold:
                        if not self.config.dry_run:
                            self._create_proposal(change)
                        result.proposals_created += 1
                    else:
                        result.conflicts_found += 1

                result.companies_processed += len(batch)

            # Detect and add new companies
            new_companies = self._detect_new_companies(parsed_data.companies, db_companies)
            for company in new_companies:
                if not self.config.dry_run:
                    self._add_new_company(company)
                result.companies_added += 1

            if not self.config.dry_run:
                self.db.commit()

        except Exception as e:
            result.add_error(f"Sync failed: {str(e)}")

        return result

    def _process_company_batch(
        self,
        companies: list[Company],
        db_companies: dict[str, Company],
    ) -> list[FieldChange]:
        """Process a batch of companies and detect changes."""
        changes = []

        for parsed_company in companies:
            # Find matching company in DB (exact or fuzzy match)
            db_company = self._find_matching_company(parsed_company, db_companies)

            if db_company:
                # Compare fields
                field_changes = self._compare_company(parsed_company, db_company)
                changes.extend(field_changes)

        return changes

    def _find_matching_company(
        self,
        parsed_company: Company,
        db_companies: dict[str, Company],
    ) -> Optional[Company]:
        """Find matching company in database, using fuzzy matching if needed."""
        # Exact match
        if parsed_company.name in db_companies:
            return db_companies[parsed_company.name]

        # Try fuzzy matching for similar names
        for db_name, db_company in db_companies.items():
            if self._is_fuzzy_match(parsed_company.name, db_name):
                return db_company

        return None

    def _is_fuzzy_match(self, name1: str, name2: str) -> bool:
        """Check if two company names refer to the same company."""
        # Basic normalization
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()

        if n1 == n2:
            return True

        # Remove common suffixes
        suffixes = [" gmbh", " inc", " ltd", " ag", " corp", " llc"]
        for suffix in suffixes:
            n1 = n1.replace(suffix, "")
            n2 = n2.replace(suffix, "")

        if n1 == n2:
            return True

        # Check if one is a substring of the other
        if n1 in n2 or n2 in n1:
            return True

        # Use LLM for complex cases (optional, expensive)
        # return self._llm_fuzzy_match(name1, name2)
        return False

    def _llm_fuzzy_match(self, name1: str, name2: str) -> bool:
        """Use LLM to determine if names refer to same company."""
        try:
            llm = self._get_llm()
            chain = FUZZY_MATCH_PROMPT | llm | StrOutputParser()

            result = chain.invoke({
                "name1": name1,
                "name2": name2,
            })

            # Parse JSON response
            data = json.loads(result)
            return data.get("same_company", False) and data.get("confidence", 0) > 0.8

        except Exception:
            return False

    def _compare_company(
        self,
        parsed: Company,
        db: Company,
    ) -> list[FieldChange]:
        """Compare parsed company with database record."""
        changes = []

        for field_name, field_config in COMPARABLE_FIELDS.items():
            parsed_value = getattr(parsed, field_name, None)
            db_value = getattr(db, field_name, None)

            # Convert to strings for comparison
            parsed_str = str(parsed_value) if parsed_value is not None else None
            db_str = str(db_value) if db_value is not None else None

            if parsed_str != db_str and parsed_str is not None:
                change = FieldChange(
                    company_id=db.id,
                    company_name=db.name,
                    field_name=field_name,
                    old_value=db_str,
                    new_value=parsed_str,
                    change_type="update",
                    source="markdown_sync",
                )

                # Check if significant based on tolerance
                tolerance = field_config.get("tolerance", 0.0)
                if change.is_significant(tolerance or 0.0):
                    # Validate with LLM
                    is_valid, confidence = self._validate_change(change)
                    change.confidence = confidence
                    change.validated = is_valid

                    if is_valid:
                        changes.append(change)

        return changes

    def _validate_change(self, change: FieldChange) -> tuple[bool, float]:
        """Use LLM to validate a proposed change."""
        try:
            llm = self._get_llm()
            chain = VALIDATE_CHANGE_PROMPT | llm | StrOutputParser()

            result = chain.invoke({
                "company_name": change.company_name,
                "field_name": change.field_name,
                "old_value": change.old_value or "None",
                "new_value": change.new_value or "None",
            })

            # Parse JSON response
            data = json.loads(result)
            is_valid = data.get("valid", False)
            confidence = data.get("confidence", 0.5)

            return is_valid, confidence

        except Exception as e:
            print(f"LLM validation failed: {e}")
            # Default to moderate confidence without LLM
            return True, 0.75

    def _detect_new_companies(
        self,
        parsed_companies: list[Company],
        db_companies: dict[str, Company],
    ) -> list[Company]:
        """Find companies in markdown but not in database."""
        new_companies = []

        for parsed in parsed_companies:
            if not self._find_matching_company(parsed, db_companies):
                new_companies.append(parsed)

        return new_companies

    def _apply_change(self, change: FieldChange) -> bool:
        """Apply a change to the database with audit logging."""
        try:
            # Update the company field
            self.db.execute(
                f"UPDATE companies SET {change.field_name} = ?, last_updated = ? WHERE id = ?",
                (change.new_value, datetime.now().isoformat(), change.company_id),
            )

            # Create audit log entry
            self._save_audit_entry(
                entity_type=EntityType.COMPANY,
                entity_id=change.company_id,
                field_name=change.field_name,
                old_value=change.old_value,
                new_value=change.new_value,
                change_source=ChangeSource.MARKDOWN_SYNC,
                changed_by="markdown_sync_service",
            )

            change.applied = True
            return True

        except Exception as e:
            print(f"Failed to apply change: {e}")
            return False

    def _create_proposal(self, change: FieldChange) -> int:
        """Create an update proposal for review."""
        # Create a DataSource for the markdown
        source = DataSource(
            url=f"file://research/Fusion_Research.md",
            title="Fusion Research Document",
            reliability=SourceReliability.INDUSTRY_PUBLICATION,
            snippet=f"Field {change.field_name} updated to {change.new_value}",
        )

        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=change.company_id,
            field_name=change.field_name,
            old_value=change.old_value,
            new_value=change.new_value,
            confidence_score=change.confidence,
            sources=[source],
            search_query=f"markdown_sync:{change.company_name}:{change.field_name}",
        )

        return self._save_proposal(proposal)

    def _save_proposal(self, proposal: UpdateProposal) -> int:
        """Save an update proposal to the database."""
        data = proposal.to_db_dict()

        cursor = self.db.execute(
            """
            INSERT INTO update_proposals (
                entity_type, entity_id, field_name, old_value, new_value,
                confidence_score, sources, search_query, extracted_at,
                status, reviewed_by, reviewed_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["entity_type"],
                data["entity_id"],
                data["field_name"],
                data["old_value"],
                data["new_value"],
                data["confidence_score"],
                data["sources"],
                data["search_query"],
                data["extracted_at"],
                data["status"],
                data["reviewed_by"],
                data["reviewed_at"],
                data["notes"],
            ),
        )
        return cursor.lastrowid

    def _add_new_company(self, company: Company) -> int:
        """Add a new company to the database."""
        cursor = self.db.execute(
            """
            INSERT INTO companies (
                name, company_type, country, city, founded_year, website,
                team_size, description, technology_approach, trl, trl_justification,
                total_funding_usd, key_investors, key_partnerships,
                competitive_positioning, confidence_score, source_url,
                created_at, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company.name,
                company.company_type.value if company.company_type else None,
                company.country,
                company.city,
                company.founded_year,
                company.website,
                company.team_size,
                company.description,
                company.technology_approach,
                company.trl,
                company.trl_justification,
                company.total_funding_usd,
                company.key_investors,
                company.key_partnerships,
                company.competitive_positioning,
                company.confidence_score or 0.85,
                "markdown_sync",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        company_id = cursor.lastrowid

        # Log the addition
        self._save_audit_entry(
            entity_type=EntityType.COMPANY,
            entity_id=company_id,
            field_name="*",
            old_value=None,
            new_value=f"New company: {company.name}",
            change_source=ChangeSource.MARKDOWN_SYNC,
            changed_by="markdown_sync_service",
        )

        return company_id

    def _save_audit_entry(
        self,
        entity_type: EntityType,
        entity_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        change_source: ChangeSource,
        changed_by: str,
        proposal_id: Optional[int] = None,
    ) -> int:
        """Save an audit log entry."""
        cursor = self.db.execute(
            """
            INSERT INTO audit_log (
                entity_type, entity_id, field_name, old_value, new_value,
                change_source, changed_at, changed_by, proposal_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_type.value,
                entity_id,
                field_name,
                old_value,
                new_value,
                change_source.value,
                datetime.now().isoformat(),
                changed_by,
                proposal_id,
            ),
        )
        return cursor.lastrowid

    def get_pending_proposals(self, limit: int = 50) -> list[UpdateProposal]:
        """Get all pending proposals from markdown sync."""
        cursor = self.db.execute(
            """
            SELECT * FROM update_proposals
            WHERE status = 'pending' AND search_query LIKE 'markdown_sync:%'
            ORDER BY confidence_score DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [UpdateProposal.from_db_row(dict(row)) for row in cursor.fetchall()]

    def approve_proposal(self, proposal_id: int, reviewed_by: str = "user") -> bool:
        """Approve and apply a pending proposal."""
        cursor = self.db.execute(
            "SELECT * FROM update_proposals WHERE id = ?",
            (proposal_id,),
        )
        row = cursor.fetchone()
        if not row:
            return False

        proposal = UpdateProposal.from_db_row(dict(row))
        if proposal.status != ProposalStatus.PENDING:
            return False

        try:
            # Apply the change
            table_name = "companies" if proposal.entity_type == EntityType.COMPANY else f"{proposal.entity_type.value}s"

            self.db.execute(
                f"UPDATE {table_name} SET {proposal.field_name} = ?, last_updated = ? WHERE id = ?",
                (proposal.new_value, datetime.now().isoformat(), proposal.entity_id),
            )

            # Update proposal status
            self.db.execute(
                """
                UPDATE update_proposals
                SET status = ?, reviewed_by = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (
                    ProposalStatus.APPROVED.value,
                    reviewed_by,
                    datetime.now().isoformat(),
                    proposal_id,
                ),
            )

            # Create audit log
            self._save_audit_entry(
                entity_type=proposal.entity_type,
                entity_id=proposal.entity_id,
                field_name=proposal.field_name,
                old_value=proposal.old_value,
                new_value=proposal.new_value,
                change_source=ChangeSource.MARKDOWN_SYNC,
                changed_by=reviewed_by,
                proposal_id=proposal_id,
            )

            self.db.commit()
            return True

        except Exception as e:
            print(f"Failed to approve proposal: {e}")
            self.db.connection.rollback()
            return False

    def reject_proposal(
        self,
        proposal_id: int,
        reviewed_by: str = "user",
        notes: str = "",
    ) -> bool:
        """Reject a pending proposal."""
        try:
            self.db.execute(
                """
                UPDATE update_proposals
                SET status = ?, reviewed_by = ?, reviewed_at = ?, notes = ?
                WHERE id = ?
                """,
                (
                    ProposalStatus.REJECTED.value,
                    reviewed_by,
                    datetime.now().isoformat(),
                    notes,
                    proposal_id,
                ),
            )
            self.db.commit()
            return True
        except Exception as e:
            print(f"Failed to reject proposal: {e}")
            return False


def get_database_sync_service(
    db: Optional[Database] = None,
    llm: Optional[ChatOllama] = None,
    config: Optional[SyncConfig] = None,
    db_path: str = "research/fusion_research.db",
) -> DatabaseSyncService:
    """Factory function to get a database sync service instance."""
    return DatabaseSyncService(
        db=db,
        llm=llm,
        config=config,
        db_path=db_path,
    )
