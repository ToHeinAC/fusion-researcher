"""Tests for the LLM database updater service."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

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
from src.services.updater_service import (
    UpdaterService,
    UpdaterConfig,
    UpdateResult,
    get_updater_service,
)


class TestDataSource:
    """Tests for DataSource model."""

    def test_create_data_source(self):
        source = DataSource(
            url="https://techcrunch.com/article",
            title="Test Article",
            reliability=SourceReliability.MAJOR_NEWS,
            snippet="Some content here",
        )

        assert source.url == "https://techcrunch.com/article"
        assert source.reliability == SourceReliability.MAJOR_NEWS
        assert source.reliability.score == 0.85

    def test_to_dict(self):
        source = DataSource(
            url="https://example.com",
            title="Test",
            reliability=SourceReliability.UNVERIFIED,
        )

        data = source.to_dict()
        assert data["url"] == "https://example.com"
        assert data["reliability"] == "unverified"
        assert data["reliability_score"] == 0.30

    def test_from_dict(self):
        data = {
            "url": "https://reuters.com/news",
            "title": "Reuters News",
            "reliability": "major_news",
            "snippet": "Content",
            "fetched_at": "2024-01-01T12:00:00",
        }

        source = DataSource.from_dict(data)
        assert source.url == "https://reuters.com/news"
        assert source.reliability == SourceReliability.MAJOR_NEWS


class TestSourceReliability:
    """Tests for source reliability classification."""

    def test_reliability_scores(self):
        assert SourceReliability.COMPANY_OFFICIAL.score == 0.95
        assert SourceReliability.FINANCIAL_DATABASE.score == 0.90
        assert SourceReliability.MAJOR_NEWS.score == 0.85
        assert SourceReliability.INDUSTRY_PUBLICATION.score == 0.80
        assert SourceReliability.GENERAL_NEWS.score == 0.70
        assert SourceReliability.SOCIAL_MEDIA.score == 0.50
        assert SourceReliability.UNVERIFIED.score == 0.30

    def test_domain_patterns_exist(self):
        assert "crunchbase.com" in SOURCE_DOMAIN_PATTERNS[SourceReliability.FINANCIAL_DATABASE]
        assert "reuters.com" in SOURCE_DOMAIN_PATTERNS[SourceReliability.MAJOR_NEWS]
        assert "fusionindustryassociation.org" in SOURCE_DOMAIN_PATTERNS[SourceReliability.INDUSTRY_PUBLICATION]


class TestUpdateProposal:
    """Tests for UpdateProposal model."""

    def test_create_proposal(self):
        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="total_funding_usd",
            old_value="100000000",
            new_value="150000000",
            confidence_score=0.85,
            sources=[],
            search_query="test query",
        )

        assert proposal.entity_type == EntityType.COMPANY
        assert proposal.status == ProposalStatus.PENDING
        assert proposal.confidence_score == 0.85

    def test_is_significant_change_numeric(self):
        # 10% change is significant
        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="total_funding_usd",
            old_value="100000000",
            new_value="110000000",
            confidence_score=0.8,
            sources=[],
            search_query="test",
        )
        assert proposal.is_significant_change() is True

        # 3% change is not significant
        proposal.new_value = "103000000"
        assert proposal.is_significant_change() is False

    def test_is_significant_change_text(self):
        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="key_investors",
            old_value="Investor A",
            new_value="Investor A, Investor B",
            confidence_score=0.8,
            sources=[],
            search_query="test",
        )
        assert proposal.is_significant_change() is True

    def test_sources_json_serialization(self):
        sources = [
            DataSource(
                url="https://test.com",
                title="Test",
                reliability=SourceReliability.MAJOR_NEWS,
            ),
        ]

        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="test",
            old_value=None,
            new_value="test",
            confidence_score=0.8,
            sources=sources,
            search_query="test",
        )

        json_str = proposal.sources_to_json()
        parsed = json.loads(json_str)
        assert len(parsed) == 1
        assert parsed[0]["url"] == "https://test.com"

        # Test deserialization
        restored = UpdateProposal.sources_from_json(json_str)
        assert len(restored) == 1
        assert restored[0].url == "https://test.com"


class TestAuditLogEntry:
    """Tests for AuditLogEntry model."""

    def test_create_audit_entry(self):
        entry = AuditLogEntry(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="total_funding_usd",
            old_value="100000000",
            new_value="150000000",
            change_source=ChangeSource.AUTO_UPDATE,
            changed_by="auto",
            proposal_id=5,
        )

        assert entry.entity_type == EntityType.COMPANY
        assert entry.change_source == ChangeSource.AUTO_UPDATE
        assert entry.proposal_id == 5

    def test_to_db_dict(self):
        entry = AuditLogEntry(
            entity_type=EntityType.FUNDING,
            entity_id=2,
            field_name="amount_usd",
            old_value="50000000",
            new_value="75000000",
            change_source=ChangeSource.MANUAL,
            changed_by="user",
        )

        data = entry.to_db_dict()
        assert data["entity_type"] == "funding"
        assert data["change_source"] == "manual"


class TestUpdateableFields:
    """Tests for updateable fields configuration."""

    def test_company_fields_exist(self):
        company_fields = UPDATEABLE_FIELDS.get(EntityType.COMPANY, {})
        assert "total_funding_usd" in company_fields
        assert "team_size" in company_fields
        assert "trl" in company_fields

    def test_field_config_structure(self):
        company_fields = UPDATEABLE_FIELDS[EntityType.COMPANY]
        funding_config = company_fields["total_funding_usd"]

        assert "search_template" in funding_config
        assert "extract_type" in funding_config
        assert funding_config["extract_type"] == "currency"


class TestUpdaterService:
    """Tests for UpdaterService."""

    def test_classify_source_reliability(self):
        service = UpdaterService()

        assert service._classify_source_reliability("https://crunchbase.com/company/test") == SourceReliability.FINANCIAL_DATABASE
        assert service._classify_source_reliability("https://www.reuters.com/article") == SourceReliability.MAJOR_NEWS
        assert service._classify_source_reliability("https://proxima-fusion.com") == SourceReliability.COMPANY_OFFICIAL
        assert service._classify_source_reliability("https://unknown-domain.com") == SourceReliability.UNVERIFIED

    def test_calculate_confidence(self):
        service = UpdaterService()

        # Single high-reliability source
        sources = [
            DataSource(url="", title="", reliability=SourceReliability.COMPANY_OFFICIAL),
        ]
        confidence = service._calculate_confidence(sources)
        assert confidence > 0.95

        # Multiple sources with boost
        sources = [
            DataSource(url="", title="", reliability=SourceReliability.MAJOR_NEWS),
            DataSource(url="", title="", reliability=SourceReliability.MAJOR_NEWS),
            DataSource(url="", title="", reliability=SourceReliability.INDUSTRY_PUBLICATION),
        ]
        confidence = service._calculate_confidence(sources)
        # Base avg: (0.85 + 0.85 + 0.80) / 3 = 0.833
        # Boost: min(3/5 * 0.15, 0.15) = 0.09
        # Total: ~0.92
        assert 0.90 <= confidence <= 0.95

    def test_clean_numeric_millions(self):
        service = UpdaterService()

        assert service._clean_numeric("$150M", "currency") == "150000000.0"
        assert service._clean_numeric("150 million", "currency") == "150000000.0"
        assert service._clean_numeric("2.5B", "currency") == "2500000000.0"

    def test_clean_numeric_integer(self):
        service = UpdaterService()

        assert service._clean_numeric("250", "integer") == "250"
        assert service._clean_numeric("1,500", "integer") == "1500"


class TestUpdaterServiceDatabase:
    """Tests for UpdaterService database operations."""

    def test_save_and_get_proposal(self, temp_db):
        service = UpdaterService(database=temp_db)

        # Insert a test company
        temp_db.execute(
            "INSERT INTO companies (name, country) VALUES (?, ?)",
            ("Test Company", "Germany"),
        )
        temp_db.commit()

        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="total_funding_usd",
            old_value="100000000",
            new_value="150000000",
            confidence_score=0.85,
            sources=[
                DataSource(
                    url="https://test.com",
                    title="Test Source",
                    reliability=SourceReliability.MAJOR_NEWS,
                ),
            ],
            search_query="test query",
        )

        proposal_id = service.save_proposal(proposal)
        assert proposal_id > 0

        # Retrieve pending proposals
        pending = service.get_pending_proposals()
        assert len(pending) == 1
        assert pending[0].field_name == "total_funding_usd"
        assert pending[0].confidence_score == 0.85

    def test_approve_proposal(self, temp_db):
        service = UpdaterService(database=temp_db)

        # Insert test company
        temp_db.execute(
            "INSERT INTO companies (name, country, total_funding_usd) VALUES (?, ?, ?)",
            ("Test Company", "Germany", 100000000),
        )
        temp_db.commit()

        # Create and save proposal
        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="total_funding_usd",
            old_value="100000000",
            new_value="150000000",
            confidence_score=0.90,
            sources=[],
            search_query="test",
        )
        proposal_id = service.save_proposal(proposal)

        # Approve
        result = service.approve_proposal(proposal_id, reviewed_by="test_user")
        assert result is True

        # Check company was updated (SQLite stores as REAL, so compare numerically)
        cursor = temp_db.execute("SELECT total_funding_usd FROM companies WHERE id = 1")
        row = cursor.fetchone()
        assert float(row["total_funding_usd"]) == 150000000.0

        # Check audit log
        audit_entries = service.get_audit_log(entity_type=EntityType.COMPANY, entity_id=1)
        assert len(audit_entries) == 1
        assert audit_entries[0].new_value == "150000000"
        assert audit_entries[0].changed_by == "test_user"

    def test_reject_proposal(self, temp_db):
        service = UpdaterService(database=temp_db)

        # Insert test company
        temp_db.execute(
            "INSERT INTO companies (name, country) VALUES (?, ?)",
            ("Test Company", "Germany"),
        )
        temp_db.commit()

        # Create and save proposal
        proposal = UpdateProposal(
            entity_type=EntityType.COMPANY,
            entity_id=1,
            field_name="total_funding_usd",
            old_value="100000000",
            new_value="150000000",
            confidence_score=0.60,
            sources=[],
            search_query="test",
        )
        proposal_id = service.save_proposal(proposal)

        # Reject
        result = service.reject_proposal(
            proposal_id, reviewed_by="test_user", notes="Low confidence"
        )
        assert result is True

        # Check status
        updated = service.get_proposal_by_id(proposal_id)
        assert updated.status == ProposalStatus.REJECTED
        assert updated.notes == "Low confidence"

    def test_get_stale_companies(self, temp_db):
        service = UpdaterService(database=temp_db)
        service.config.staleness_days = 30

        # Insert companies with different update times
        temp_db.execute(
            "INSERT INTO companies (name, country, last_updated) VALUES (?, ?, ?)",
            ("Fresh Company", "Germany", datetime.now().isoformat()),
        )
        temp_db.execute(
            "INSERT INTO companies (name, country, last_updated) VALUES (?, ?, ?)",
            ("Stale Company", "USA", "2020-01-01T00:00:00"),
        )
        temp_db.commit()

        stale = service.get_stale_companies(limit=10)
        assert len(stale) == 1
        assert stale[0]["name"] == "Stale Company"


class TestUpdaterConfig:
    """Tests for UpdaterConfig."""

    def test_default_config(self):
        config = UpdaterConfig()

        assert config.auto_apply_threshold == 0.85
        assert config.staleness_days == 30
        assert config.max_sources_per_field == 5

    def test_custom_config(self):
        config = UpdaterConfig(
            auto_apply_threshold=0.90,
            staleness_days=14,
            max_sources_per_field=3,
        )

        assert config.auto_apply_threshold == 0.90
        assert config.staleness_days == 14


class TestUpdateResult:
    """Tests for UpdateResult."""

    def test_default_result(self):
        result = UpdateResult()

        assert result.companies_processed == 0
        assert result.proposals_created == 0
        assert result.errors == []

    def test_result_with_data(self):
        result = UpdateResult(
            companies_processed=5,
            proposals_created=10,
            proposals_auto_applied=3,
            errors=["Error 1"],
        )

        assert result.companies_processed == 5
        assert result.proposals_auto_applied == 3
        assert len(result.errors) == 1
