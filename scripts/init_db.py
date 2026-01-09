#!/usr/bin/env python3
"""Initialize the database schema."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database import get_database


def main():
    """Initialize the database."""
    print("🗄️ Initializing Fusion Research Database...")
    
    # Get database instance
    db = get_database()
    
    # Initialize schema
    print("📋 Creating tables...")
    db.init_schema()
    
    # Verify tables
    tables = db.get_table_names()
    print(f"✅ Created {len(tables)} tables:")
    for table in tables:
        print(f"   - {table}")
    
    print("\n✅ Database initialization complete!")
    print(f"📁 Database location: {db.db_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
