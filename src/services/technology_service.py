"""Technology analysis service."""

from typing import Optional
from dataclasses import dataclass

from src.data.database import Database
from src.data.repositories import TechnologyRepository, CompanyRepository
from src.models.technology import TRLLevel


@dataclass
class TechnologyMetrics:
    """Technology metrics summary."""
    trl_distribution: list[dict]
    approach_distribution: list[dict]
    avg_trl_by_approach: dict
    companies_by_approach: dict


class TechnologyService:
    """Service for technology analysis."""
    
    def __init__(self, db: Database):
        self.db = db
        self.tech_repo = TechnologyRepository(db)
        self.company_repo = CompanyRepository(db)
    
    def get_trl_distribution(self) -> list[dict]:
        """Get TRL distribution across companies."""
        return self.tech_repo.get_trl_distribution()
    
    def get_approach_distribution(self) -> list[dict]:
        """Get technology approach distribution."""
        return self.tech_repo.get_approach_distribution()
    
    def get_technology_metrics(self) -> TechnologyMetrics:
        """Get comprehensive technology metrics."""
        trl_dist = self.get_trl_distribution()
        approach_dist = self.get_approach_distribution()
        
        # Average TRL by approach
        cursor = self.db.execute(
            """SELECT technology_approach, AVG(trl) as avg_trl, COUNT(*) as count
               FROM companies
               WHERE technology_approach IS NOT NULL AND trl IS NOT NULL
               GROUP BY technology_approach"""
        )
        avg_trl_by_approach = {
            row[0]: {"avg_trl": round(row[1], 1), "count": row[2]}
            for row in cursor.fetchall()
        }
        
        # Companies by approach
        companies_by_approach = {}
        for approach in approach_dist:
            companies = self.company_repo.search(technology=approach["approach"], limit=50)
            companies_by_approach[approach["approach"]] = [
                {"name": c.name, "trl": c.trl, "funding": c.total_funding_usd}
                for c in companies
            ]
        
        return TechnologyMetrics(
            trl_distribution=trl_dist,
            approach_distribution=approach_dist,
            avg_trl_by_approach=avg_trl_by_approach,
            companies_by_approach=companies_by_approach,
        )
    
    def get_trl_matrix(self) -> list[dict]:
        """Get TRL matrix data for visualization."""
        cursor = self.db.execute(
            """SELECT name, technology_approach, trl, total_funding_usd, country
               FROM companies
               WHERE trl IS NOT NULL
               ORDER BY trl DESC, total_funding_usd DESC NULLS LAST"""
        )
        return [
            {
                "company": row[0],
                "technology": row[1] or "Unknown",
                "trl": row[2],
                "funding": row[3] or 0,
                "country": row[4] or "Unknown",
            }
            for row in cursor.fetchall()
        ]
    
    def get_trl_levels(self) -> list[TRLLevel]:
        """Get all TRL level definitions."""
        return TRLLevel.get_all_levels()
    
    def get_companies_near_commercialization(self, min_trl: int = 6) -> list[dict]:
        """Get companies closest to commercialization."""
        companies = self.company_repo.search(trl_min=min_trl, limit=20)
        return [
            {
                "name": c.name,
                "trl": c.trl,
                "technology": c.technology_approach,
                "funding": c.total_funding_usd,
                "country": c.country,
            }
            for c in companies
        ]
    
    def get_technology_comparison(self) -> list[dict]:
        """Get technology approach comparison data."""
        cursor = self.db.execute(
            """SELECT 
                technology_approach,
                COUNT(*) as company_count,
                AVG(trl) as avg_trl,
                MAX(trl) as max_trl,
                SUM(total_funding_usd) as total_funding,
                AVG(total_funding_usd) as avg_funding
               FROM companies
               WHERE technology_approach IS NOT NULL
               GROUP BY technology_approach
               ORDER BY total_funding DESC NULLS LAST"""
        )
        return [
            {
                "approach": row[0],
                "company_count": row[1],
                "avg_trl": round(row[2] or 0, 1),
                "max_trl": row[3] or 0,
                "total_funding": row[4] or 0,
                "avg_funding": row[5] or 0,
            }
            for row in cursor.fetchall()
        ]
    
    def get_technology_timeline(self) -> list[dict]:
        """Get technology development timeline data."""
        cursor = self.db.execute(
            """SELECT 
                technology_approach,
                founded_year,
                COUNT(*) as count
               FROM companies
               WHERE technology_approach IS NOT NULL AND founded_year IS NOT NULL
               GROUP BY technology_approach, founded_year
               ORDER BY founded_year"""
        )
        return [
            {"technology": row[0], "year": row[1], "count": row[2]}
            for row in cursor.fetchall()
        ]
