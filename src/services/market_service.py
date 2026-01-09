"""Market analysis service."""

from typing import Optional
from dataclasses import dataclass

from src.data.database import Database
from src.data.repositories import MarketRepository, FundingRepository
from src.models.market import Market
from src.llm.analyzer import FusionAnalyzer


@dataclass
class MarketMetrics:
    """Key market metrics."""
    total_market_size_2024: float
    total_market_size_2040: float
    cagr: float
    total_funding: float
    company_count: int
    top_regions: list[dict]
    funding_by_year: list[dict]


class MarketService:
    """Service for market analysis and intelligence."""
    
    def __init__(
        self,
        db: Database,
        analyzer: Optional[FusionAnalyzer] = None,
    ):
        self.db = db
        self.market_repo = MarketRepository(db)
        self.funding_repo = FundingRepository(db)
        self.analyzer = analyzer
    
    def get_all_markets(self) -> list[Market]:
        """Get all market data."""
        return self.market_repo.get_all()
    
    def get_market_by_region(self, region: str) -> Optional[Market]:
        """Get market data for a specific region."""
        return self.market_repo.get_by_region(region)
    
    def get_global_market(self) -> Optional[Market]:
        """Get global market data."""
        return self.market_repo.get_by_region("Global")
    
    def get_market_metrics(self) -> MarketMetrics:
        """Get key market metrics."""
        markets = self.market_repo.get_all()
        
        # Find global market for totals
        global_market = next((m for m in markets if m.region.value == "Global"), None)
        
        total_2024 = global_market.market_size_2024_usd if global_market else 0
        total_2040 = global_market.market_size_2040_usd if global_market else 0
        cagr = global_market.cagr_percent if global_market else 0
        
        # Get funding data
        total_funding = self.funding_repo.get_total_funding()
        funding_by_year = self.funding_repo.get_funding_by_year()
        
        # Get company count
        cursor = self.db.execute("SELECT COUNT(*) FROM companies")
        company_count = cursor.fetchone()[0]
        
        # Top regions by market size
        top_regions = [
            {
                "region": m.region_name,
                "market_size_2024": m.market_size_2024_usd or 0,
            }
            for m in sorted(
                [m for m in markets if m.market_size_2024_usd],
                key=lambda x: x.market_size_2024_usd or 0,
                reverse=True,
            )[:5]
        ]
        
        return MarketMetrics(
            total_market_size_2024=total_2024 or 0,
            total_market_size_2040=total_2040 or 0,
            cagr=cagr or 0,
            total_funding=total_funding,
            company_count=company_count,
            top_regions=top_regions,
            funding_by_year=funding_by_year,
        )
    
    def get_funding_trends(self) -> list[dict]:
        """Get funding trends by year."""
        return self.funding_repo.get_funding_by_year()
    
    def get_regional_distribution(self) -> list[dict]:
        """Get company distribution by region."""
        cursor = self.db.execute(
            """SELECT country, COUNT(*) as count, SUM(total_funding_usd) as funding
               FROM companies
               GROUP BY country
               ORDER BY funding DESC NULLS LAST"""
        )
        return [
            {"country": row[0], "count": row[1], "funding": row[2] or 0}
            for row in cursor.fetchall()
        ]
    
    def generate_market_report(self, focus_area: str = "general") -> Optional[str]:
        """Generate a market report section."""
        if not self.analyzer:
            return None
        
        metrics = self.get_market_metrics()
        regional = self.get_regional_distribution()
        
        market_data = f"""
Market Size 2024: ${metrics.total_market_size_2024 / 1e9:.1f}B
Market Size 2040: ${metrics.total_market_size_2040 / 1e9:.1f}B
CAGR: {metrics.cagr:.1f}%
Total Private Funding: ${metrics.total_funding / 1e9:.2f}B
Company Count: {metrics.company_count}

Regional Distribution:
{chr(10).join(f"- {r['country']}: {r['count']} companies, ${r['funding']/1e6:.1f}M funding" for r in regional[:10])}

Funding by Year:
{chr(10).join(f"- {y['year']}: ${y['total']/1e6:.1f}M" for y in metrics.funding_by_year[-5:])}
"""
        
        return self.analyzer.generate_market_report(market_data, focus_area)
    
    def get_investment_landscape(self) -> dict:
        """Get investment landscape data."""
        # Funding by stage
        cursor = self.db.execute(
            """SELECT stage, COUNT(*) as count, SUM(amount_usd) as total
               FROM funding_rounds
               GROUP BY stage
               ORDER BY total DESC NULLS LAST"""
        )
        by_stage = [
            {"stage": row[0], "count": row[1], "total": row[2] or 0}
            for row in cursor.fetchall()
        ]
        
        # Top investors
        cursor = self.db.execute(
            """SELECT lead_investor, COUNT(*) as count, SUM(amount_usd) as total
               FROM funding_rounds
               WHERE lead_investor IS NOT NULL
               GROUP BY lead_investor
               ORDER BY total DESC NULLS LAST
               LIMIT 10"""
        )
        top_investors = [
            {"investor": row[0], "deals": row[1], "total": row[2] or 0}
            for row in cursor.fetchall()
        ]
        
        return {
            "by_stage": by_stage,
            "top_investors": top_investors,
            "total_funding": self.funding_repo.get_total_funding(),
        }
