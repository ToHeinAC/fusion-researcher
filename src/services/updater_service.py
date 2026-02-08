"""LLM-powered database update service."""

import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from tavily import TavilyClient
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.data.database import get_database, Database
from src.services.audit_service import AuditService
from src.models.update_proposal import (
    UpdateProposal,
    AuditLogEntry,
    DataSource,
    EntityType,
    ProposalStatus,
    ChangeSource,
    SourceReliability,
    SOURCE_DOMAIN_PATTERNS,
    UPDATEABLE_FIELDS,
)


@dataclass
class UpdaterConfig:
    """Configuration for the updater service."""
    auto_apply_threshold: float = 0.85
    staleness_days: int = 30
    max_sources_per_field: int = 5
    search_timeout: float = 10.0


@dataclass
class UpdateResult:
    """Result of an update cycle."""
    companies_processed: int = 0
    proposals_created: int = 0
    proposals_auto_applied: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class UpdaterService:
    """Service for LLM-powered database updates."""

    def __init__(
        self,
        llm: Optional[ChatOllama] = None,
        tavily_api_key: Optional[str] = None,
        config: Optional[UpdaterConfig] = None,
        db_path: str = "research/fusion_research.db",
        database: Optional[Database] = None,
    ):
        self.llm = llm
        self.tavily_client: Optional[TavilyClient] = None
        if tavily_api_key:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
        self.config = config or UpdaterConfig()
        # Use provided database instance or get/create from path
        self.db = database if database else get_database(db_path)
        self._audit = AuditService(self.db)

    def search_web(self, query: str, max_results: int = 5) -> list[DataSource]:
        """Search web for information using Tavily API."""
        sources = []

        if not self.tavily_client:
            return sources

        try:
            response = self.tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
            )

            for result in response.get("results", []):
                url = result.get("url", "")
                reliability = self._classify_source_reliability(url)

                source = DataSource(
                    url=url,
                    title=result.get("title", ""),
                    reliability=reliability,
                    snippet=result.get("content", "")[:500],
                    fetched_at=datetime.now(),
                )
                sources.append(source)

        except Exception as e:
            print(f"Tavily search error: {e}")

        return sources

    def _classify_source_reliability(self, url: str) -> SourceReliability:
        """Classify source reliability based on domain."""
        try:
            domain = urlparse(url).netloc.lower()
            domain = domain.replace("www.", "")

            for reliability, patterns in SOURCE_DOMAIN_PATTERNS.items():
                for pattern in patterns:
                    if pattern in domain:
                        return reliability

            return SourceReliability.UNVERIFIED
        except Exception:
            return SourceReliability.UNVERIFIED

    def extract_value(
        self,
        field_name: str,
        extract_type: str,
        sources: list[DataSource],
        company_name: str,
    ) -> tuple[Optional[str], float]:
        """Use LLM to extract a value from sources."""
        if not self.llm or not sources:
            return None, 0.0

        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources[:5], 1):
            context_parts.append(
                f"Source {i} ({source.reliability.label}, {source.reliability.score:.2f}):\n"
                f"Title: {source.title}\n"
                f"Content: {source.snippet}\n"
            )
        context = "\n".join(context_parts)

        # Create extraction prompt based on type
        type_instructions = {
            "currency": "Extract as a number in USD (e.g., 150000000 for $150M). Convert from EUR/GBP if needed.",
            "integer": "Extract as a whole number (e.g., 250 for 250 employees).",
            "percentage": "Extract as a decimal percentage (e.g., 15.5 for 15.5%).",
            "date": "Extract as ISO date format (YYYY-MM-DD).",
            "text": "Extract as concise text, comma-separated if multiple items.",
        }

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data extraction specialist for fusion energy companies.
Extract the requested information from the provided sources.
Be precise and only extract information that is explicitly stated.
If the information is not found or unclear, respond with "NOT_FOUND".
{type_instruction}"""),
            ("human", """Company: {company_name}
Field to extract: {field_name}

Sources:
{context}

Extract the {field_name} value. Respond with ONLY the extracted value or "NOT_FOUND":"""),
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            result = chain.invoke({
                "company_name": company_name,
                "field_name": field_name,
                "context": context,
                "type_instruction": type_instructions.get(extract_type, ""),
            })

            result = result.strip()

            if result == "NOT_FOUND" or not result:
                return None, 0.0

            # Clean up numeric values
            if extract_type in ("currency", "integer", "percentage"):
                result = self._clean_numeric(result, extract_type)

            # Calculate confidence based on source reliability
            confidence = self._calculate_confidence(sources)

            return result, confidence

        except Exception as e:
            print(f"LLM extraction error: {e}")
            return None, 0.0

    def _clean_numeric(self, value: str, extract_type: str) -> str:
        """Clean and normalize numeric values."""
        # Remove common suffixes and prefixes
        value = re.sub(r'[,$%]', '', value)
        value = value.replace('USD', '').replace('EUR', '').strip()

        # Handle multipliers (M = million, B = billion)
        multiplier = 1
        if 'B' in value.upper() or 'billion' in value.lower():
            multiplier = 1_000_000_000
            value = re.sub(r'[Bb]illion|[Bb]', '', value)
        elif 'M' in value.upper() or 'million' in value.lower():
            multiplier = 1_000_000
            value = re.sub(r'[Mm]illion|[Mm]', '', value)

        try:
            num = float(value.strip()) * multiplier
            if extract_type == "integer":
                return str(int(num))
            return str(num)
        except ValueError:
            return value

    def _calculate_confidence(self, sources: list[DataSource]) -> float:
        """Calculate confidence score based on source reliability."""
        if not sources:
            return 0.0

        # Average source reliability
        avg_reliability = sum(s.reliability.score for s in sources) / len(sources)

        # Boost for multiple sources (max 0.15 boost)
        source_boost = min(len(sources) / 5 * 0.15, 0.15)

        confidence = avg_reliability + source_boost
        return min(confidence, 1.0)

    def research_company_field(
        self,
        company_id: int,
        company_name: str,
        field_name: str,
        field_config: dict,
        current_value: Optional[str],
    ) -> Optional[UpdateProposal]:
        """Research a single field for a company."""
        # Build search query
        search_query = field_config["search_template"].format(
            company_name=company_name
        )

        # Search web
        sources = self.search_web(
            search_query, max_results=self.config.max_sources_per_field
        )

        if not sources:
            return None

        # Extract value using LLM
        new_value, confidence = self.extract_value(
            field_name,
            field_config["extract_type"],
            sources,
            company_name,
        )

        if new_value is None:
            return None

        # Create proposal
        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=company_id,
            field_name=field_name,
            old_value=current_value,
            new_value=new_value,
            confidence_score=confidence,
            sources=sources,
            search_query=search_query,
        )

        # Only return if it's a significant change
        if proposal.is_significant_change():
            return proposal

        return None

    def research_company(
        self,
        company_id: int,
        company_name: str,
        fields: Optional[list[str]] = None,
    ) -> list[UpdateProposal]:
        """Research all specified fields for a company."""
        proposals = []

        # Get current company data
        cursor = self.db.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        )
        row = cursor.fetchone()
        if not row:
            return proposals

        company_data = dict(row)

        # Get updateable fields for companies
        company_fields = UPDATEABLE_FIELDS.get(EntityType.COMPANY, {})

        # Filter to requested fields if specified
        if fields:
            company_fields = {k: v for k, v in company_fields.items() if k in fields}

        for field_name, field_config in company_fields.items():
            current_value = str(company_data.get(field_name, "")) or None

            proposal = self.research_company_field(
                company_id=company_id,
                company_name=company_name,
                field_name=field_name,
                field_config=field_config,
                current_value=current_value,
            )

            if proposal:
                proposals.append(proposal)

        return proposals

    def save_proposal(self, proposal: UpdateProposal) -> int:
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
        self.db.commit()
        return cursor.lastrowid

    def get_pending_proposals(self, limit: int = 50) -> list[UpdateProposal]:
        """Get all pending proposals."""
        cursor = self.db.execute(
            """
            SELECT * FROM update_proposals
            WHERE status = 'pending'
            ORDER BY confidence_score DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [UpdateProposal.from_db_row(dict(row)) for row in cursor.fetchall()]

    def get_proposal_by_id(self, proposal_id: int) -> Optional[UpdateProposal]:
        """Get a proposal by ID."""
        cursor = self.db.execute(
            "SELECT * FROM update_proposals WHERE id = ?",
            (proposal_id,),
        )
        row = cursor.fetchone()
        return UpdateProposal.from_db_row(dict(row)) if row else None

    def approve_proposal(
        self, proposal_id: int, reviewed_by: str = "user"
    ) -> bool:
        """Approve and apply a proposal."""
        proposal = self.get_proposal_by_id(proposal_id)
        if not proposal or proposal.status != ProposalStatus.PENDING:
            return False

        # Apply the update to the entity
        table_name = f"{proposal.entity_type.value}s"  # companies, fundings, etc.
        if proposal.entity_type == EntityType.COMPANY:
            table_name = "companies"
        elif proposal.entity_type == EntityType.FUNDING:
            table_name = "funding_rounds"

        try:
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

            # Create audit log entry
            audit_entry = AuditLogEntry(
                entity_type=proposal.entity_type,
                entity_id=proposal.entity_id,
                field_name=proposal.field_name,
                old_value=proposal.old_value,
                new_value=proposal.new_value,
                change_source=ChangeSource.AUTO_UPDATE,
                changed_by=reviewed_by,
                proposal_id=proposal_id,
            )
            self._save_audit_entry(audit_entry)

            self.db.commit()
            return True

        except Exception as e:
            print(f"Error approving proposal: {e}")
            self.db.connection.rollback()
            return False

    def reject_proposal(
        self, proposal_id: int, reviewed_by: str = "user", notes: str = ""
    ) -> bool:
        """Reject a proposal."""
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
            print(f"Error rejecting proposal: {e}")
            return False

    def delete_all_pending_proposals(self) -> int:
        """Delete all pending proposals from the database."""
        try:
            cursor = self.db.execute(
                "SELECT COUNT(*) as count FROM update_proposals WHERE status = 'pending'"
            )
            count = cursor.fetchone()["count"]

            self.db.execute(
                "DELETE FROM update_proposals WHERE status = 'pending'"
            )
            self.db.commit()
            return count
        except Exception as e:
            print(f"Error deleting pending proposals: {e}")
            return 0

    def auto_apply_high_confidence(
        self, threshold: Optional[float] = None
    ) -> int:
        """Auto-apply proposals with confidence above threshold."""
        threshold = threshold or self.config.auto_apply_threshold
        applied_count = 0

        cursor = self.db.execute(
            """
            SELECT id FROM update_proposals
            WHERE status = 'pending' AND confidence_score >= ?
            """,
            (threshold,),
        )

        for row in cursor.fetchall():
            if self.approve_proposal(row["id"], reviewed_by="auto"):
                # Update status to auto_applied
                self.db.execute(
                    "UPDATE update_proposals SET status = ? WHERE id = ?",
                    (ProposalStatus.AUTO_APPLIED.value, row["id"]),
                )
                applied_count += 1

        self.db.commit()
        return applied_count

    def _save_audit_entry(self, entry: AuditLogEntry) -> int:
        """Save an audit log entry (delegates to AuditService)."""
        return self._audit.save_entry(entry)

    def get_audit_log(
        self,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get audit log entries (delegates to AuditService)."""
        return self._audit.get_log(entity_type, entity_id, limit)

    def get_stale_companies(self, limit: int = 20) -> list[dict]:
        """Get companies that haven't been updated recently."""
        cutoff = datetime.now() - timedelta(days=self.config.staleness_days)

        cursor = self.db.execute(
            """
            SELECT id, name, last_updated, total_funding_usd, trl
            FROM companies
            WHERE last_updated < ? OR last_updated IS NULL
            ORDER BY total_funding_usd DESC NULLS LAST
            LIMIT ?
            """,
            (cutoff.isoformat(), limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_all_companies(self, limit: int = 100) -> list[dict]:
        """Get all companies for update selection."""
        cursor = self.db.execute(
            """
            SELECT id, name, last_updated, total_funding_usd, trl, country
            FROM companies
            ORDER BY total_funding_usd DESC NULLS LAST
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def run_update_cycle(
        self,
        company_ids: list[int],
        fields: Optional[list[str]] = None,
        auto_apply: bool = False,
    ) -> UpdateResult:
        """Run a full update cycle for specified companies."""
        result = UpdateResult()

        for company_id in company_ids:
            # Get company name
            cursor = self.db.execute(
                "SELECT name FROM companies WHERE id = ?", (company_id,)
            )
            row = cursor.fetchone()
            if not row:
                result.errors.append(f"Company {company_id} not found")
                continue

            company_name = row["name"]

            try:
                proposals = self.research_company(company_id, company_name, fields)

                for proposal in proposals:
                    proposal_id = self.save_proposal(proposal)
                    result.proposals_created += 1

                    if auto_apply and proposal.confidence_score >= self.config.auto_apply_threshold:
                        if self.approve_proposal(proposal_id, reviewed_by="auto"):
                            self.db.execute(
                                "UPDATE update_proposals SET status = ? WHERE id = ?",
                                (ProposalStatus.AUTO_APPLIED.value, proposal_id),
                            )
                            result.proposals_auto_applied += 1

                result.companies_processed += 1

            except Exception as e:
                result.errors.append(f"Error processing {company_name}: {e}")

        self.db.commit()
        return result


def get_updater_service(
    llm: Optional[ChatOllama] = None,
    tavily_api_key: Optional[str] = None,
    config: Optional[UpdaterConfig] = None,
    db_path: str = "research/fusion_research.db",
) -> UpdaterService:
    """Get updater service instance."""
    return UpdaterService(
        llm=llm,
        tavily_api_key=tavily_api_key,
        config=config,
        db_path=db_path,
    )
