"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    from src.data.database import Database
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    db.init_schema()
    
    yield db
    
    db.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_company():
    """Create a sample company for testing."""
    from src.models.company import Company, CompanyType
    
    return Company(
        name="Test Fusion Corp",
        company_type=CompanyType.STARTUP,
        country="Germany",
        city="Munich",
        founded_year=2023,
        technology_approach="Stellarator",
        trl=5,
        total_funding_usd=100_000_000,
        team_size=50,
        description="A test fusion company",
    )


@pytest.fixture
def sample_market():
    """Create a sample market for testing."""
    from src.models.market import Market, MarketRegion
    
    return Market(
        region=MarketRegion.GERMANY,
        region_name="Germany",
        market_size_2024_usd=50_000_000_000,
        market_size_2040_usd=200_000_000_000,
        cagr_percent=8.5,
    )
