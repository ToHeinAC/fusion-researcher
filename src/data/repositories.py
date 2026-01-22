"""Repository pattern implementations for data access."""

from typing import Optional
from datetime import datetime

from src.data.database import Database
from src.models.company import Company, CompanyType, CompanyDTO
from src.models.funding import FundingRound, FundingStage, Investor
from src.models.technology import Technology, TechnologyApproach
from src.models.market import Market, MarketRegion
from src.models.partnership import Partnership, PartnershipType


class CompanyRepository:
    """Repository for company data access."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_id(self, company_id: int) -> Optional[Company]:
        """Get company by ID."""
        cursor = self.db.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_company(row)
    
    def get_by_name(self, name: str) -> Optional[Company]:
        """Get company by name."""
        cursor = self.db.execute(
            "SELECT * FROM companies WHERE name = ?", (name,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_company(row)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> list[Company]:
        """Get all companies with pagination."""
        cursor = self.db.execute(
            "SELECT * FROM companies ORDER BY name LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [self._row_to_company(row) for row in cursor.fetchall()]
    
    def search(
        self,
        country: Optional[str] = None,
        technology: Optional[str] = None,
        trl_min: Optional[int] = None,
        trl_max: Optional[int] = None,
        funding_min: Optional[float] = None,
        funding_max: Optional[float] = None,
        company_type: Optional[str] = None,
        founded_after: Optional[int] = None,
        founded_before: Optional[int] = None,
        limit: int = 100,
    ) -> list[CompanyDTO]:
        """Search companies with filters."""
        conditions = []
        params = []
        
        if country:
            conditions.append("country = ?")
            params.append(country)
        if technology:
            conditions.append("technology_approach = ?")
            params.append(technology)
        if trl_min is not None and trl_max is not None:
            # Include companies with NULL TRL when full range (1-9) is selected
            if trl_min == 1 and trl_max == 9:
                conditions.append("(trl IS NULL OR (trl >= ? AND trl <= ?))")
                params.extend([trl_min, trl_max])
            else:
                conditions.append("trl >= ?")
                params.append(trl_min)
                conditions.append("trl <= ?")
                params.append(trl_max)
        elif trl_min is not None:
            conditions.append("trl >= ?")
            params.append(trl_min)
        elif trl_max is not None:
            conditions.append("trl <= ?")
            params.append(trl_max)
        if funding_min is not None:
            conditions.append("total_funding_usd >= ?")
            params.append(funding_min)
        if funding_max is not None:
            conditions.append("total_funding_usd <= ?")
            params.append(funding_max)
        if company_type:
            conditions.append("company_type = ?")
            params.append(company_type)
        if founded_after is not None:
            conditions.append("founded_year >= ?")
            params.append(founded_after)
        if founded_before is not None:
            conditions.append("founded_year <= ?")
            params.append(founded_before)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        
        cursor = self.db.execute(
            f"""SELECT id, name, company_type, country, founded_year, 
                       total_funding_usd, trl, technology_approach, team_size
                FROM companies 
                WHERE {where_clause}
                ORDER BY total_funding_usd DESC NULLS LAST
                LIMIT ?""",
            tuple(params)
        )
        
        return [
            CompanyDTO(
                id=row["id"],
                name=row["name"],
                company_type=row["company_type"] or "Unknown",
                country=row["country"] or "Unknown",
                founded_year=row["founded_year"],
                total_funding_usd=row["total_funding_usd"],
                trl=row["trl"],
                technology_approach=row["technology_approach"],
                team_size=row["team_size"],
            )
            for row in cursor.fetchall()
        ]
    
    def create(self, company: Company) -> int:
        """Create a new company."""
        cursor = self.db.execute(
            """INSERT INTO companies 
               (name, company_type, country, city, founded_year, website, team_size,
                description, technology_approach, trl, trl_justification, 
                total_funding_usd, key_investors, key_partnerships, 
                competitive_positioning, confidence_score, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                company.name,
                company.company_type.value,
                company.country,
                company.city,
                company.founded_year,
                company.website,
                company.team_size,
                company.description,
                company.technology_approach,
                company.trl,
                company.trl_justification,
                company.total_funding_usd,
                company.key_investors,
                company.key_partnerships,
                company.competitive_positioning,
                company.confidence_score,
                company.source_url,
            )
        )
        self.db.commit()
        return cursor.lastrowid
    
    def update(self, company: Company) -> bool:
        """Update an existing company."""
        if company.id is None:
            return False
        
        self.db.execute(
            """UPDATE companies SET
               name = ?, company_type = ?, country = ?, city = ?, founded_year = ?,
               website = ?, team_size = ?, description = ?, technology_approach = ?,
               trl = ?, trl_justification = ?, total_funding_usd = ?, key_investors = ?,
               key_partnerships = ?, competitive_positioning = ?, confidence_score = ?,
               source_url = ?, last_updated = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (
                company.name,
                company.company_type.value,
                company.country,
                company.city,
                company.founded_year,
                company.website,
                company.team_size,
                company.description,
                company.technology_approach,
                company.trl,
                company.trl_justification,
                company.total_funding_usd,
                company.key_investors,
                company.key_partnerships,
                company.competitive_positioning,
                company.confidence_score,
                company.source_url,
                company.id,
            )
        )
        self.db.commit()
        return True
    
    def delete(self, company_id: int) -> bool:
        """Delete a company."""
        cursor = self.db.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        self.db.commit()
        return cursor.rowcount > 0
    
    def get_count(self) -> int:
        """Get total company count."""
        cursor = self.db.execute("SELECT COUNT(*) FROM companies")
        return cursor.fetchone()[0]
    
    def get_countries(self) -> list[str]:
        """Get list of unique countries."""
        cursor = self.db.execute(
            "SELECT DISTINCT country FROM companies WHERE country IS NOT NULL ORDER BY country"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_technologies(self) -> list[str]:
        """Get list of unique technology approaches."""
        cursor = self.db.execute(
            "SELECT DISTINCT technology_approach FROM companies WHERE technology_approach IS NOT NULL ORDER BY technology_approach"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def _row_to_company(self, row) -> Company:
        """Convert database row to Company model."""
        return Company(
            id=row["id"],
            name=row["name"],
            company_type=CompanyType(row["company_type"]) if row["company_type"] else CompanyType.UNKNOWN,
            country=row["country"] or "Unknown",
            city=row["city"],
            founded_year=row["founded_year"],
            website=row["website"],
            team_size=row["team_size"],
            description=row["description"],
            technology_approach=row["technology_approach"],
            trl=row["trl"],
            trl_justification=row["trl_justification"],
            total_funding_usd=row["total_funding_usd"],
            key_investors=row["key_investors"],
            key_partnerships=row["key_partnerships"],
            competitive_positioning=row["competitive_positioning"],
            last_updated=datetime.fromisoformat(row["last_updated"]) if row["last_updated"] else None,
            confidence_score=row["confidence_score"] or 0.8,
            source_url=row["source_url"],
        )


class FundingRepository:
    """Repository for funding data access."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_company(self, company_id: int) -> list[FundingRound]:
        """Get all funding rounds for a company."""
        cursor = self.db.execute(
            "SELECT * FROM funding_rounds WHERE company_id = ? ORDER BY date DESC",
            (company_id,)
        )
        return [self._row_to_funding(row) for row in cursor.fetchall()]
    
    def create(self, funding: FundingRound) -> int:
        """Create a new funding round."""
        cursor = self.db.execute(
            """INSERT INTO funding_rounds 
               (company_id, amount_usd, amount_original, currency, date, stage,
                lead_investor, all_investors, valuation_usd, source_url, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                funding.company_id,
                funding.amount_usd,
                funding.amount_original,
                funding.currency,
                funding.date.isoformat() if funding.date else None,
                funding.stage.value,
                funding.lead_investor,
                funding.all_investors,
                funding.valuation_usd,
                funding.source_url,
                funding.notes,
            )
        )
        self.db.commit()
        return cursor.lastrowid
    
    def get_total_funding(self) -> float:
        """Get total funding across all companies."""
        cursor = self.db.execute("SELECT SUM(amount_usd) FROM funding_rounds")
        result = cursor.fetchone()[0]
        return result or 0.0
    
    def get_funding_by_year(self) -> list[dict]:
        """Get funding aggregated by year."""
        cursor = self.db.execute(
            """SELECT strftime('%Y', date) as year, SUM(amount_usd) as total
               FROM funding_rounds 
               WHERE date IS NOT NULL
               GROUP BY strftime('%Y', date)
               ORDER BY year"""
        )
        return [{"year": row[0], "total": row[1]} for row in cursor.fetchall()]
    
    def _row_to_funding(self, row) -> FundingRound:
        """Convert database row to FundingRound model."""
        from datetime import date as date_type
        return FundingRound(
            id=row["id"],
            company_id=row["company_id"],
            amount_usd=row["amount_usd"],
            amount_original=row["amount_original"],
            currency=row["currency"] or "USD",
            date=date_type.fromisoformat(row["date"]) if row["date"] else None,
            stage=FundingStage(row["stage"]) if row["stage"] else FundingStage.UNKNOWN,
            lead_investor=row["lead_investor"],
            all_investors=row["all_investors"],
            valuation_usd=row["valuation_usd"],
            source_url=row["source_url"],
            notes=row["notes"],
        )


class TechnologyRepository:
    """Repository for technology data access."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_company(self, company_id: int) -> list[Technology]:
        """Get all technologies for a company."""
        cursor = self.db.execute(
            "SELECT * FROM technologies WHERE company_id = ?",
            (company_id,)
        )
        return [self._row_to_technology(row) for row in cursor.fetchall()]

    def get_all(self, limit: int = 100) -> list[Technology]:
        """Get all technologies."""
        cursor = self.db.execute(
            "SELECT * FROM technologies LIMIT ?",
            (limit,)
        )
        return [self._row_to_technology(row) for row in cursor.fetchall()]

    def create(self, tech: Technology) -> int:
        """Create a new technology entry."""
        cursor = self.db.execute(
            """INSERT INTO technologies 
               (company_id, approach, name, trl, trl_justification, description,
                key_materials, key_challenges, development_stage, target_commercialization_year)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tech.company_id,
                tech.approach.value,
                tech.name,
                tech.trl,
                tech.trl_justification,
                tech.description,
                tech.key_materials,
                tech.key_challenges,
                tech.development_stage,
                tech.target_commercialization_year,
            )
        )
        self.db.commit()
        return cursor.lastrowid
    
    def get_trl_distribution(self) -> list[dict]:
        """Get TRL distribution across companies."""
        cursor = self.db.execute(
            """SELECT trl, COUNT(*) as count 
               FROM companies 
               WHERE trl IS NOT NULL 
               GROUP BY trl 
               ORDER BY trl"""
        )
        return [{"trl": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    def get_approach_distribution(self) -> list[dict]:
        """Get technology approach distribution."""
        cursor = self.db.execute(
            """SELECT technology_approach, COUNT(*) as count 
               FROM companies 
               WHERE technology_approach IS NOT NULL 
               GROUP BY technology_approach 
               ORDER BY count DESC"""
        )
        return [{"approach": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    def _row_to_technology(self, row) -> Technology:
        """Convert database row to Technology model."""
        return Technology(
            id=row["id"],
            company_id=row["company_id"],
            approach=TechnologyApproach(row["approach"]) if row["approach"] else TechnologyApproach.UNKNOWN,
            name=row["name"],
            trl=row["trl"],
            trl_justification=row["trl_justification"],
            description=row["description"],
            key_materials=row["key_materials"],
            key_challenges=row["key_challenges"],
            development_stage=row["development_stage"],
            target_commercialization_year=row["target_commercialization_year"],
        )


class MarketRepository:
    """Repository for market data access."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_all(self, limit: int = 100) -> list[Market]:
        """Get all markets."""
        cursor = self.db.execute("SELECT * FROM markets ORDER BY region_name LIMIT ?", (limit,))
        return [self._row_to_market(row) for row in cursor.fetchall()]
    
    def get_by_region(self, region: str) -> Optional[Market]:
        """Get market by region."""
        cursor = self.db.execute(
            "SELECT * FROM markets WHERE region = ?", (region,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_market(row)
    
    def create(self, market: Market) -> int:
        """Create a new market entry."""
        cursor = self.db.execute(
            """INSERT INTO markets 
               (region, region_name, market_size_2024_usd, market_size_2030_usd,
                market_size_2040_usd, cagr_percent, company_count, total_funding_usd,
                regulatory_environment, growth_drivers, key_challenges, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                market.region.value,
                market.region_name,
                market.market_size_2024_usd,
                market.market_size_2030_usd,
                market.market_size_2040_usd,
                market.cagr_percent,
                market.company_count,
                market.total_funding_usd,
                market.regulatory_environment,
                market.growth_drivers,
                market.key_challenges,
                market.notes,
            )
        )
        self.db.commit()
        return cursor.lastrowid
    
    def _row_to_market(self, row) -> Market:
        """Convert database row to Market model."""
        return Market(
            id=row["id"],
            region=MarketRegion(row["region"]) if row["region"] else MarketRegion.GLOBAL,
            region_name=row["region_name"] or "Global",
            market_size_2024_usd=row["market_size_2024_usd"],
            market_size_2030_usd=row["market_size_2030_usd"],
            market_size_2040_usd=row["market_size_2040_usd"],
            cagr_percent=row["cagr_percent"],
            company_count=row["company_count"] or 0,
            total_funding_usd=row["total_funding_usd"],
            regulatory_environment=row["regulatory_environment"],
            growth_drivers=row["growth_drivers"],
            key_challenges=row["key_challenges"],
            notes=row["notes"],
        )


class PartnershipRepository:
    """Repository for partnership data access."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_company(self, company_id: int) -> list[Partnership]:
        """Get all partnerships for a company."""
        cursor = self.db.execute(
            "SELECT * FROM partnerships WHERE company_id_a = ? OR company_id_b = ?",
            (company_id, company_id)
        )
        return [self._row_to_partnership(row) for row in cursor.fetchall()]
    
    def create(self, partnership: Partnership) -> int:
        """Create a new partnership."""
        cursor = self.db.execute(
            """INSERT INTO partnerships 
               (company_id_a, company_id_b, partner_name, partner_type, description,
                value_usd, start_date, end_date, status, key_deliverables, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                partnership.company_id_a,
                partnership.company_id_b,
                partnership.partner_name,
                partnership.partner_type.value,
                partnership.description,
                partnership.value_usd,
                partnership.start_date.isoformat() if partnership.start_date else None,
                partnership.end_date.isoformat() if partnership.end_date else None,
                partnership.status,
                partnership.key_deliverables,
                partnership.source_url,
            )
        )
        self.db.commit()
        return cursor.lastrowid
    
    def _row_to_partnership(self, row) -> Partnership:
        """Convert database row to Partnership model."""
        from datetime import date as date_type
        return Partnership(
            id=row["id"],
            company_id_a=row["company_id_a"],
            company_id_b=row["company_id_b"],
            partner_name=row["partner_name"],
            partner_type=PartnershipType(row["partner_type"]) if row["partner_type"] else PartnershipType.OTHER,
            description=row["description"],
            value_usd=row["value_usd"],
            start_date=date_type.fromisoformat(row["start_date"]) if row["start_date"] else None,
            end_date=date_type.fromisoformat(row["end_date"]) if row["end_date"] else None,
            status=row["status"] or "Active",
            key_deliverables=row["key_deliverables"],
            source_url=row["source_url"],
        )
