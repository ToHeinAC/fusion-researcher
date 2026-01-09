"""Tests for database layer."""

import pytest
from src.data.database import Database
from src.data.repositories import CompanyRepository, MarketRepository


class TestDatabase:
    """Tests for Database class."""
    
    def test_database_creation(self, temp_db):
        """Test database creation and schema initialization."""
        tables = temp_db.get_table_names()
        assert "companies" in tables
        assert "funding_rounds" in tables
        assert "technologies" in tables
        assert "markets" in tables
        assert "partnerships" in tables
    
    def test_table_info(self, temp_db):
        """Test getting table info."""
        info = temp_db.get_table_info("companies")
        column_names = [col["name"] for col in info]
        assert "id" in column_names
        assert "name" in column_names
        assert "country" in column_names


class TestCompanyRepository:
    """Tests for CompanyRepository."""
    
    def test_create_company(self, temp_db, sample_company):
        """Test creating a company."""
        repo = CompanyRepository(temp_db)
        company_id = repo.create(sample_company)
        assert company_id > 0
    
    def test_get_company_by_id(self, temp_db, sample_company):
        """Test getting company by ID."""
        repo = CompanyRepository(temp_db)
        company_id = repo.create(sample_company)
        
        retrieved = repo.get_by_id(company_id)
        assert retrieved is not None
        assert retrieved.name == sample_company.name
    
    def test_get_company_by_name(self, temp_db, sample_company):
        """Test getting company by name."""
        repo = CompanyRepository(temp_db)
        repo.create(sample_company)
        
        retrieved = repo.get_by_name(sample_company.name)
        assert retrieved is not None
        assert retrieved.country == sample_company.country
    
    def test_search_companies(self, temp_db, sample_company):
        """Test searching companies."""
        repo = CompanyRepository(temp_db)
        repo.create(sample_company)
        
        results = repo.search(country="Germany")
        assert len(results) == 1
        assert results[0].name == sample_company.name
    
    def test_get_count(self, temp_db, sample_company):
        """Test getting company count."""
        repo = CompanyRepository(temp_db)
        assert repo.get_count() == 0
        
        repo.create(sample_company)
        assert repo.get_count() == 1


class TestMarketRepository:
    """Tests for MarketRepository."""
    
    def test_create_market(self, temp_db, sample_market):
        """Test creating a market."""
        repo = MarketRepository(temp_db)
        market_id = repo.create(sample_market)
        assert market_id > 0
    
    def test_get_market_by_region(self, temp_db, sample_market):
        """Test getting market by region."""
        repo = MarketRepository(temp_db)
        repo.create(sample_market)
        
        retrieved = repo.get_by_region("Germany")
        assert retrieved is not None
        assert retrieved.cagr_percent == sample_market.cagr_percent
