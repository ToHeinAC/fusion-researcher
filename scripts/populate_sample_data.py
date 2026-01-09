#!/usr/bin/env python3
"""Populate database with data from Fusion_Research.md."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import get_database
from src.data.repositories import CompanyRepository, MarketRepository
from src.data.parsers.markdown_parser import parse_fusion_research


def main():
    """Populate the database with research data."""
    print("📚 Populating Fusion Research Database...")
    
    # Check if research file exists
    research_path = project_root / "research" / "Fusion_Research.md"
    if not research_path.exists():
        print(f"❌ Research file not found: {research_path}")
        return 1
    
    print(f"📄 Parsing: {research_path}")
    
    # Parse the research document
    try:
        parsed = parse_fusion_research(str(research_path))
        print(f"   Found {len(parsed.companies)} companies")
        print(f"   Found {len(parsed.markets)} markets")
    except Exception as e:
        print(f"❌ Error parsing research file: {e}")
        return 1
    
    # Get database
    db = get_database()
    
    # Initialize schema if needed
    tables = db.get_table_names()
    if not tables:
        print("📋 Initializing database schema...")
        db.init_schema()
    
    # Insert companies
    company_repo = CompanyRepository(db)
    print("\n👥 Inserting companies...")
    
    inserted = 0
    skipped = 0
    for company in parsed.companies:
        try:
            # Check if company already exists
            existing = company_repo.get_by_name(company.name)
            if existing:
                print(f"   ⏭️ Skipping (exists): {company.name}")
                skipped += 1
                continue
            
            company_repo.create(company)
            print(f"   ✅ Added: {company.name}")
            inserted += 1
        except Exception as e:
            print(f"   ❌ Error adding {company.name}: {e}")
    
    print(f"\n   Inserted: {inserted}, Skipped: {skipped}")
    
    # Insert markets
    market_repo = MarketRepository(db)
    print("\n🌍 Inserting markets...")
    
    inserted_markets = 0
    for market in parsed.markets:
        try:
            existing = market_repo.get_by_region(market.region.value)
            if existing:
                print(f"   ⏭️ Skipping (exists): {market.region_name}")
                continue
            
            market_repo.create(market)
            print(f"   ✅ Added: {market.region_name}")
            inserted_markets += 1
        except Exception as e:
            print(f"   ❌ Error adding {market.region_name}: {e}")
    
    print(f"\n   Inserted: {inserted_markets} markets")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Database Summary:")
    print(f"   Companies: {company_repo.get_count()}")
    print(f"   Markets: {len(market_repo.get_all())}")
    print("=" * 50)
    
    print("\n✅ Database population complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
