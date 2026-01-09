"""Tests for data models."""

import pytest
from src.models.company import Company, CompanyType, CompanyDTO
from src.models.funding import FundingRound, FundingStage
from src.models.technology import Technology, TechnologyApproach, TRLLevel
from src.models.market import Market, MarketRegion


class TestCompany:
    """Tests for Company model."""
    
    def test_company_creation(self, sample_company):
        """Test creating a company."""
        assert sample_company.name == "Test Fusion Corp"
        assert sample_company.company_type == CompanyType.STARTUP
        assert sample_company.country == "Germany"
    
    def test_funding_display(self, sample_company):
        """Test funding display formatting."""
        assert sample_company.funding_display == "$100.0M"
    
    def test_funding_display_billions(self):
        """Test funding display for billions."""
        company = Company(
            name="Big Corp",
            total_funding_usd=2_500_000_000,
        )
        assert company.funding_display == "$2.5B"
    
    def test_trl_display(self, sample_company):
        """Test TRL display formatting."""
        assert "TRL 5" in sample_company.trl_display


class TestFundingRound:
    """Tests for FundingRound model."""
    
    def test_funding_round_creation(self):
        """Test creating a funding round."""
        funding = FundingRound(
            company_id=1,
            amount_usd=50_000_000,
            stage=FundingStage.SERIES_A,
            lead_investor="Test VC",
        )
        assert funding.amount_usd == 50_000_000
        assert funding.stage == FundingStage.SERIES_A
    
    def test_amount_display(self):
        """Test amount display formatting."""
        funding = FundingRound(
            company_id=1,
            amount_usd=130_000_000,
        )
        assert funding.amount_display == "$130.0M"


class TestTechnology:
    """Tests for Technology model."""
    
    def test_technology_creation(self):
        """Test creating a technology."""
        tech = Technology(
            company_id=1,
            approach=TechnologyApproach.STELLARATOR,
            trl=6,
        )
        assert tech.approach == TechnologyApproach.STELLARATOR
        assert tech.trl == 6
    
    def test_trl_levels(self):
        """Test TRL level definitions."""
        levels = TRLLevel.get_all_levels()
        assert len(levels) == 9
        assert levels[0].level == 1
        assert levels[8].level == 9


class TestMarket:
    """Tests for Market model."""
    
    def test_market_creation(self, sample_market):
        """Test creating a market."""
        assert sample_market.region == MarketRegion.GERMANY
        assert sample_market.cagr_percent == 8.5
    
    def test_market_size_display(self, sample_market):
        """Test market size display formatting."""
        assert sample_market.market_size_2024_display == "$50.0B"
