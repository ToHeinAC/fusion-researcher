"""Company business logic service."""

from typing import Optional
from dataclasses import dataclass

from src.data.database import Database
from src.data.repositories import CompanyRepository, FundingRepository, PartnershipRepository
from src.models.company import Company, CompanyDTO
from src.llm.analyzer import FusionAnalyzer, SWOTAnalysis, CompanyComparison


@dataclass
class CompanySearchCriteria:
    """Search criteria for companies."""
    country: Optional[str] = None
    technology: Optional[str] = None
    trl_min: Optional[int] = None
    trl_max: Optional[int] = None
    funding_min: Optional[float] = None
    funding_max: Optional[float] = None
    company_type: Optional[str] = None
    founded_after: Optional[int] = None
    founded_before: Optional[int] = None
    limit: int = 100


class CompanyService:
    """Service for company-related business logic."""
    
    def __init__(
        self,
        db: Database,
        analyzer: Optional[FusionAnalyzer] = None,
    ):
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.funding_repo = FundingRepository(db)
        self.partnership_repo = PartnershipRepository(db)
        self.analyzer = analyzer
    
    def get_company(self, company_id: int) -> Optional[Company]:
        """Get company by ID."""
        return self.company_repo.get_by_id(company_id)
    
    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get company by name."""
        return self.company_repo.get_by_name(name)
    
    def search_companies(self, criteria: CompanySearchCriteria) -> list[CompanyDTO]:
        """Search companies with filters."""
        return self.company_repo.search(
            country=criteria.country,
            technology=criteria.technology,
            trl_min=criteria.trl_min,
            trl_max=criteria.trl_max,
            funding_min=criteria.funding_min,
            funding_max=criteria.funding_max,
            company_type=criteria.company_type,
            founded_after=criteria.founded_after,
            founded_before=criteria.founded_before,
            limit=criteria.limit,
        )
    
    def get_all_companies(self, limit: int = 100) -> list[Company]:
        """Get all companies."""
        return self.company_repo.get_all(limit=limit)
    
    def get_company_count(self) -> int:
        """Get total company count."""
        return self.company_repo.get_count()
    
    def get_countries(self) -> list[str]:
        """Get list of unique countries."""
        return self.company_repo.get_countries()
    
    def get_technologies(self) -> list[str]:
        """Get list of unique technology approaches."""
        return self.company_repo.get_technologies()
    
    def get_company_funding_history(self, company_id: int) -> list:
        """Get funding history for a company."""
        return self.funding_repo.get_by_company(company_id)
    
    def get_company_partnerships(self, company_id: int) -> list:
        """Get partnerships for a company."""
        return self.partnership_repo.get_by_company(company_id)
    
    def generate_swot(self, company_id: int, market_context: str = "") -> Optional[SWOTAnalysis]:
        """Generate SWOT analysis for a company."""
        if not self.analyzer:
            return None
        
        company = self.get_company(company_id)
        if not company:
            return None
        
        return self.analyzer.generate_swot(company, market_context)
    
    def compare_companies(self, company_id_a: int, company_id_b: int) -> Optional[CompanyComparison]:
        """Compare two companies."""
        if not self.analyzer:
            return None
        
        company_a = self.get_company(company_id_a)
        company_b = self.get_company(company_id_b)
        
        if not company_a or not company_b:
            return None
        
        return self.analyzer.compare_companies(company_a, company_b)
    
    def get_top_funded_companies(self, limit: int = 10) -> list[CompanyDTO]:
        """Get top funded companies."""
        return self.company_repo.search(limit=limit)
    
    def get_companies_by_trl(self, trl: int) -> list[CompanyDTO]:
        """Get companies at a specific TRL."""
        return self.company_repo.search(trl_min=trl, trl_max=trl)
    
    def get_german_startups(self) -> list[CompanyDTO]:
        """Get German fusion startups."""
        return self.company_repo.search(country="Germany", company_type="Startup")
    
    def create_company(self, company: Company) -> int:
        """Create a new company."""
        return self.company_repo.create(company)
    
    def update_company(self, company: Company) -> bool:
        """Update an existing company."""
        return self.company_repo.update(company)
    
    def delete_company(self, company_id: int) -> bool:
        """Delete a company."""
        return self.company_repo.delete(company_id)
    
    def get_company_summary_stats(self) -> dict:
        """Get summary statistics for companies."""
        all_companies = self.company_repo.get_all(limit=1000)
        
        total_funding = sum(c.total_funding_usd or 0 for c in all_companies)
        avg_trl = sum(c.trl or 0 for c in all_companies if c.trl) / max(1, sum(1 for c in all_companies if c.trl))
        
        by_country = {}
        by_technology = {}
        by_type = {}
        
        for company in all_companies:
            by_country[company.country] = by_country.get(company.country, 0) + 1
            if company.technology_approach:
                by_technology[company.technology_approach] = by_technology.get(company.technology_approach, 0) + 1
            by_type[company.company_type.value] = by_type.get(company.company_type.value, 0) + 1
        
        return {
            "total_companies": len(all_companies),
            "total_funding_usd": total_funding,
            "average_trl": round(avg_trl, 1),
            "by_country": by_country,
            "by_technology": by_technology,
            "by_type": by_type,
        }
