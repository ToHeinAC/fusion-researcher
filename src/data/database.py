"""SQLite database connection and schema management."""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: str = "research/fusion_research.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """Get a database cursor with automatic commit/rollback."""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL statement."""
        return self.connection.execute(sql, params)
    
    def executemany(self, sql: str, params_list: list) -> sqlite3.Cursor:
        """Execute SQL statement with multiple parameter sets."""
        return self.connection.executemany(sql, params_list)
    
    def commit(self):
        """Commit current transaction."""
        self.connection.commit()
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def init_schema(self):
        """Initialize database schema."""
        schema_sql = """
        -- Companies table
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            company_type TEXT DEFAULT 'Unknown',
            country TEXT DEFAULT 'Unknown',
            city TEXT,
            founded_year INTEGER,
            website TEXT,
            team_size INTEGER,
            description TEXT,
            technology_approach TEXT,
            trl INTEGER CHECK (trl >= 1 AND trl <= 9),
            trl_justification TEXT,
            total_funding_usd REAL,
            key_investors TEXT,
            key_partnerships TEXT,
            competitive_positioning TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score REAL DEFAULT 0.8,
            source_url TEXT
        );
        
        -- Funding rounds table
        CREATE TABLE IF NOT EXISTS funding_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            amount_usd REAL,
            amount_original REAL,
            currency TEXT DEFAULT 'USD',
            date DATE,
            stage TEXT DEFAULT 'Unknown',
            lead_investor TEXT,
            all_investors TEXT,
            valuation_usd REAL,
            source_url TEXT,
            notes TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Investors table
        CREATE TABLE IF NOT EXISTS investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            investor_type TEXT DEFAULT 'Unknown',
            country TEXT,
            website TEXT,
            portfolio_focus TEXT,
            total_investments_count INTEGER DEFAULT 0,
            total_invested_usd REAL
        );
        
        -- Investor-Funding junction table
        CREATE TABLE IF NOT EXISTS funding_investors (
            funding_id INTEGER NOT NULL,
            investor_id INTEGER NOT NULL,
            is_lead INTEGER DEFAULT 0,
            PRIMARY KEY (funding_id, investor_id),
            FOREIGN KEY (funding_id) REFERENCES funding_rounds(id) ON DELETE CASCADE,
            FOREIGN KEY (investor_id) REFERENCES investors(id) ON DELETE CASCADE
        );
        
        -- Technologies table
        CREATE TABLE IF NOT EXISTS technologies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            approach TEXT DEFAULT 'Unknown',
            name TEXT,
            trl INTEGER CHECK (trl >= 1 AND trl <= 9),
            trl_justification TEXT,
            description TEXT,
            key_materials TEXT,
            key_challenges TEXT,
            development_stage TEXT,
            target_commercialization_year INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Markets table
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            region_name TEXT DEFAULT 'Global',
            market_size_2024_usd REAL,
            market_size_2030_usd REAL,
            market_size_2040_usd REAL,
            cagr_percent REAL,
            company_count INTEGER DEFAULT 0,
            total_funding_usd REAL,
            regulatory_environment TEXT,
            growth_drivers TEXT,
            key_challenges TEXT,
            notes TEXT
        );
        
        -- Market trends table
        CREATE TABLE IF NOT EXISTS market_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit TEXT DEFAULT 'USD',
            source TEXT,
            FOREIGN KEY (market_id) REFERENCES markets(id) ON DELETE CASCADE
        );
        
        -- Partnerships table
        CREATE TABLE IF NOT EXISTS partnerships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id_a INTEGER NOT NULL,
            company_id_b INTEGER,
            partner_name TEXT,
            partner_type TEXT DEFAULT 'Other',
            description TEXT,
            value_usd REAL,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'Active',
            key_deliverables TEXT,
            source_url TEXT,
            FOREIGN KEY (company_id_a) REFERENCES companies(id) ON DELETE CASCADE,
            FOREIGN KEY (company_id_b) REFERENCES companies(id) ON DELETE SET NULL
        );
        
        -- Collaborations table
        CREATE TABLE IF NOT EXISTS collaborations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            institution_name TEXT NOT NULL,
            institution_type TEXT DEFAULT 'Research Institute',
            country TEXT,
            collaboration_type TEXT DEFAULT 'Research',
            description TEXT,
            funding_amount_usd REAL,
            start_date DATE,
            end_date DATE,
            key_outcomes TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Regulatory milestones table
        CREATE TABLE IF NOT EXISTS regulatory_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jurisdiction TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            date TEXT,
            description TEXT,
            impact_assessment TEXT,
            affected_companies TEXT,
            source_url TEXT
        );
        
        -- Company updates/news table
        CREATE TABLE IF NOT EXISTS company_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            update_type TEXT DEFAULT 'News',
            title TEXT,
            content TEXT,
            source_url TEXT,
            published_date DATE,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            relevance_score REAL,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
        
        -- Update proposals table (LLM-suggested data changes)
        CREATE TABLE IF NOT EXISTS update_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            confidence_score REAL,
            sources TEXT,
            search_query TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            notes TEXT
        );

        -- Audit log table (track all data changes)
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            change_source TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by TEXT,
            proposal_id INTEGER,
            FOREIGN KEY (proposal_id) REFERENCES update_proposals(id)
        );

        -- Create indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_companies_country ON companies(country);
        CREATE INDEX IF NOT EXISTS idx_companies_technology ON companies(technology_approach);
        CREATE INDEX IF NOT EXISTS idx_companies_trl ON companies(trl);
        CREATE INDEX IF NOT EXISTS idx_companies_funding ON companies(total_funding_usd);
        CREATE INDEX IF NOT EXISTS idx_funding_company ON funding_rounds(company_id);
        CREATE INDEX IF NOT EXISTS idx_funding_date ON funding_rounds(date);
        CREATE INDEX IF NOT EXISTS idx_technologies_company ON technologies(company_id);
        CREATE INDEX IF NOT EXISTS idx_partnerships_company ON partnerships(company_id_a);
        CREATE INDEX IF NOT EXISTS idx_markets_region ON markets(region);
        CREATE INDEX IF NOT EXISTS idx_proposals_status ON update_proposals(status);
        CREATE INDEX IF NOT EXISTS idx_proposals_entity ON update_proposals(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
        """
        
        self.connection.executescript(schema_sql)
        self.commit()
    
    def get_table_names(self) -> list[str]:
        """Get list of all table names."""
        cursor = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_info(self, table_name: str) -> list[dict]:
        """Get column information for a table."""
        cursor = self.execute(f"PRAGMA table_info({table_name})")
        return [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default": row[4],
                "pk": row[5],
            }
            for row in cursor.fetchall()
        ]
    
    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        cursor = self.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


# Singleton instance
_database: Optional[Database] = None


def get_database(db_path: str = "research/fusion_research.db") -> Database:
    """Get database singleton instance."""
    global _database
    if _database is None:
        _database = Database(db_path)
    return _database
