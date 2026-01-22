"""Populate ChromaDB vector store with data from SQLite database."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import get_database
from src.data.vector_store import get_vector_store
from src.data.repositories import CompanyRepository, TechnologyRepository, MarketRepository


def populate_companies(vector_store, db):
    """Populate vector store with company data."""
    repo = CompanyRepository(db)
    companies = repo.get_all(limit=1000)
    
    count = 0
    for company in companies:
        try:
            vector_store.add_company(
                company_id=company.id,
                name=company.name,
                description=company.description or "",
                technology=company.technology_approach,
                country=company.country,
                funding=company.total_funding_usd,
                trl=company.trl,
            )
            count += 1
            print(f"  Added company: {company.name}")
        except Exception as e:
            print(f"  Error adding {company.name}: {e}")
    
    return count


def populate_technologies(vector_store, db):
    """Populate vector store with technology data."""
    repo = TechnologyRepository(db)
    technologies = repo.get_all(limit=100)

    count = 0
    for tech in technologies:
        try:
            vector_store.add_technology(
                tech_id=tech.id,
                name=tech.name or f"Technology {tech.id}",
                approach=tech.approach.value if tech.approach else "Unknown",
                description=tech.description or "",
                trl_range=str(tech.trl) if tech.trl else "",
                challenges=tech.key_challenges or "",
            )
            count += 1
            print(f"  Added technology: {tech.name}")
        except Exception as e:
            print(f"  Error adding {tech.name}: {e}")

    return count


def populate_markets(vector_store, db):
    """Populate vector store with market data."""
    repo = MarketRepository(db)
    markets = repo.get_all(limit=100)
    
    count = 0
    for market in markets:
        try:
            vector_store.add_market(
                market_id=market.id,
                region=market.region.value if market.region else "Global",
                market_size=market.market_size_usd_2024 or 0,
                cagr=market.cagr_percent or 0,
                description=market.description or "",
            )
            count += 1
            print(f"  Added market: {market.region}")
        except Exception as e:
            print(f"  Error adding market: {e}")
    
    return count


def populate_research_chunks(vector_store):
    """Populate vector store with research document chunks."""
    research_path = Path("research/Fusion_Research.md")
    
    if not research_path.exists():
        print("  Research document not found")
        return 0
    
    content = research_path.read_text(encoding="utf-8")
    
    # Split into sections by ## headers
    sections = content.split("\n## ")
    
    count = 0
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        
        # Get section title from first line
        lines = section.split("\n")
        title = lines[0].strip("#").strip() if lines else f"Section {i}"
        section_content = "\n".join(lines[1:]).strip()
        
        # Skip very short sections
        if len(section_content) < 100:
            continue
        
        # Split large sections into chunks (~1000 chars each)
        chunk_size = 1000
        chunks = [section_content[j:j+chunk_size] for j in range(0, len(section_content), chunk_size)]
        
        for j, chunk in enumerate(chunks):
            try:
                vector_store.add_research_chunk(
                    chunk_id=f"section_{i}_chunk_{j}",
                    content=chunk,
                    section=title,
                )
                count += 1
            except Exception as e:
                print(f"  Error adding chunk {i}_{j}: {e}")
    
    print(f"  Added {count} research chunks")
    return count


def main():
    """Main function to populate the vector store."""
    print("=" * 60)
    print("Populating ChromaDB Vector Store")
    print("=" * 60)
    
    # Initialize
    print("\n📦 Initializing vector store...")
    try:
        vector_store = get_vector_store()
        print(f"  Persist directory: {vector_store.persist_directory}")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        print("\nMake sure Ollama is running with the embedding model:")
        print("  ollama pull nomic-embed-text")
        return
    
    print("\n🗄️ Connecting to database...")
    db = get_database()
    
    # Clear existing data
    print("\n🗑️ Clearing existing vector data...")
    try:
        vector_store.clear()
        vector_store = get_vector_store()  # Reinitialize after clear
    except Exception as e:
        print(f"  Warning: {e}")
    
    # Populate companies
    print("\n🏢 Adding companies...")
    company_count = populate_companies(vector_store, db)
    
    # Populate technologies
    print("\n🔬 Adding technologies...")
    tech_count = populate_technologies(vector_store, db)
    
    # Populate markets
    print("\n📊 Adding markets...")
    market_count = populate_markets(vector_store, db)
    
    # Populate research chunks
    print("\n📄 Adding research document chunks...")
    chunk_count = populate_research_chunks(vector_store)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Vector Store Population Complete")
    print("=" * 60)
    print(f"  Companies: {company_count}")
    print(f"  Technologies: {tech_count}")
    print(f"  Markets: {market_count}")
    print(f"  Research chunks: {chunk_count}")
    
    # Show stats
    stats = vector_store.get_collection_stats()
    print(f"\n📈 Collection stats:")
    print(f"  Total documents: {stats['count']}")
    print(f"  Persist directory: {stats['persist_directory']}")


if __name__ == "__main__":
    main()
