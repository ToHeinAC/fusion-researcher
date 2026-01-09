"""Report generation service."""

from typing import Optional
from datetime import datetime
from pathlib import Path

from src.data.database import Database
from src.services.company_service import CompanyService
from src.services.market_service import MarketService
from src.services.technology_service import TechnologyService
from src.llm.analyzer import FusionAnalyzer


class ReportService:
    """Service for generating reports."""
    
    def __init__(
        self,
        db: Database,
        analyzer: Optional[FusionAnalyzer] = None,
    ):
        self.db = db
        self.company_service = CompanyService(db, analyzer)
        self.market_service = MarketService(db, analyzer)
        self.tech_service = TechnologyService(db)
        self.analyzer = analyzer
    
    def generate_market_overview(self) -> str:
        """Generate market overview report."""
        metrics = self.market_service.get_market_metrics()
        regional = self.market_service.get_regional_distribution()
        tech_comparison = self.tech_service.get_technology_comparison()
        
        report = f"""# Fusion Energy Market Overview
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Executive Summary

The global fusion energy market is experiencing unprecedented growth, driven by significant private investment and technological breakthroughs.

## Key Metrics

| Metric | Value |
|--------|-------|
| Market Size (2024) | ${metrics.total_market_size_2024 / 1e9:.1f}B |
| Market Size (2040) | ${metrics.total_market_size_2040 / 1e9:.1f}B |
| CAGR | {metrics.cagr:.1f}% |
| Total Private Funding | ${metrics.total_funding / 1e9:.2f}B |
| Active Companies | {metrics.company_count} |

## Regional Distribution

| Country | Companies | Total Funding |
|---------|-----------|---------------|
"""
        for r in regional[:10]:
            funding_display = f"${r['funding'] / 1e6:.1f}M" if r['funding'] else "N/A"
            report += f"| {r['country']} | {r['count']} | {funding_display} |\n"
        
        report += """
## Technology Landscape

| Technology | Companies | Avg TRL | Total Funding |
|------------|-----------|---------|---------------|
"""
        for t in tech_comparison:
            funding_display = f"${t['total_funding'] / 1e9:.2f}B" if t['total_funding'] else "N/A"
            report += f"| {t['approach']} | {t['company_count']} | {t['avg_trl']} | {funding_display} |\n"
        
        report += """
## Investment Trends

"""
        for year_data in metrics.funding_by_year[-5:]:
            report += f"- **{year_data['year']}:** ${year_data['total'] / 1e6:.1f}M\n"
        
        return report
    
    def generate_company_profile(self, company_id: int) -> Optional[str]:
        """Generate detailed company profile report."""
        company = self.company_service.get_company(company_id)
        if not company:
            return None
        
        funding_history = self.company_service.get_company_funding_history(company_id)
        partnerships = self.company_service.get_company_partnerships(company_id)
        
        report = f"""# Company Profile: {company.name}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Overview

| Attribute | Value |
|-----------|-------|
| Company Type | {company.company_type.value} |
| Country | {company.country} |
| City | {company.city or "N/A"} |
| Founded | {company.founded_year or "N/A"} |
| Team Size | {company.team_size or "N/A"} |
| Website | {company.website or "N/A"} |

## Technology

| Attribute | Value |
|-----------|-------|
| Approach | {company.technology_approach or "N/A"} |
| TRL | {company.trl_display} |

{company.trl_justification or ""}

## Funding

**Total Funding:** {company.funding_display}

### Funding History
"""
        if funding_history:
            report += "\n| Date | Stage | Amount | Lead Investor |\n|------|-------|--------|---------------|\n"
            for f in funding_history:
                date_str = f.date.isoformat() if f.date else "N/A"
                report += f"| {date_str} | {f.stage.value} | {f.amount_display} | {f.lead_investor or 'N/A'} |\n"
        else:
            report += "\nNo detailed funding history available.\n"
        
        report += f"""
## Key Investors

{company.key_investors or "Not disclosed"}

## Partnerships
"""
        if partnerships:
            for p in partnerships:
                report += f"- **{p.partner_name or 'Partner'}** ({p.partner_type.value}): {p.description or 'N/A'}\n"
        else:
            report += "\nNo partnership data available.\n"
        
        report += f"""
## Description

{company.description or "No description available."}

## Competitive Positioning

{company.competitive_positioning or "No competitive positioning data available."}

---
*Data confidence score: {company.confidence_score:.0%}*
*Last updated: {company.last_updated.strftime("%Y-%m-%d") if company.last_updated else "N/A"}*
"""
        return report
    
    def generate_investment_thesis(self, focus: str = "German startups") -> str:
        """Generate investment thesis report."""
        metrics = self.market_service.get_market_metrics()
        investment = self.market_service.get_investment_landscape()
        near_commercial = self.tech_service.get_companies_near_commercialization()
        
        report = f"""# Fusion Energy Investment Thesis
**Focus:** {focus}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Market Opportunity

The fusion energy market represents a **${metrics.total_market_size_2040 / 1e9:.0f}B opportunity by 2040**, growing at a CAGR of {metrics.cagr:.1f}%.

### Key Drivers
- Global decarbonization mandates
- AI/data center power demand explosion
- Energy security concerns
- Technological breakthroughs (HTS magnets, AI plasma control)

## Investment Landscape

**Total Private Investment:** ${metrics.total_funding / 1e9:.2f}B

### By Stage
"""
        for stage in investment["by_stage"][:5]:
            if stage["total"]:
                report += f"- **{stage['stage']}:** ${stage['total'] / 1e6:.1f}M ({stage['count']} deals)\n"
        
        report += """
### Top Investors
"""
        for inv in investment["top_investors"][:5]:
            if inv["total"]:
                report += f"- **{inv['investor']}:** ${inv['total'] / 1e6:.1f}M ({inv['deals']} deals)\n"
        
        report += """
## Companies Near Commercialization (TRL 6+)

| Company | TRL | Technology | Funding | Country |
|---------|-----|------------|---------|---------|
"""
        for c in near_commercial[:10]:
            funding = f"${c['funding'] / 1e6:.1f}M" if c['funding'] else "N/A"
            report += f"| {c['name']} | {c['trl']} | {c['technology'] or 'N/A'} | {funding} | {c['country']} |\n"
        
        report += """
## Investment Considerations

### Opportunities
- First-mover advantage in emerging sector
- Strong government support (Germany EUR 2B+ Action Plan)
- Technology convergence with AI, advanced materials
- Multiple viable technology approaches

### Risks
- Long development timelines (5-15 years to commercialization)
- High capital requirements
- Technology risk (net energy not yet demonstrated at scale)
- Regulatory uncertainty in some jurisdictions

## Recommended Focus Areas
1. **HTS Magnet Technology** - Critical enabler across approaches
2. **Stellarator Development** - Steady-state advantage
3. **Supply Chain Enablers** - Lower risk, near-term revenue
4. **German Ecosystem** - Favorable regulation, strong research base
"""
        return report
    
    def save_report(self, content: str, filename: str, output_dir: str = "research/reports") -> str:
        """Save report to file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / filename
        file_path.write_text(content, encoding="utf-8")
        
        return str(file_path)
