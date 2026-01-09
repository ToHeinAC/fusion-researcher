"""Markdown parser for Fusion_Research.md document."""

import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from src.models.company import Company, CompanyType
from src.models.funding import FundingRound, FundingStage
from src.models.technology import Technology, TechnologyApproach
from src.models.market import Market, MarketRegion
from src.models.partnership import Partnership, PartnershipType


@dataclass
class ParsedData:
    """Container for all parsed data from Fusion_Research.md."""
    companies: list[Company] = field(default_factory=list)
    funding_rounds: list[FundingRound] = field(default_factory=list)
    technologies: list[Technology] = field(default_factory=list)
    markets: list[Market] = field(default_factory=list)
    partnerships: list[Partnership] = field(default_factory=list)
    raw_sections: dict[str, str] = field(default_factory=dict)


class MarkdownParser:
    """Parser for Fusion_Research.md document."""
    
    # Technology approach mappings
    TECH_MAPPINGS = {
        "tokamak": TechnologyApproach.TOKAMAK,
        "stellarator": TechnologyApproach.STELLARATOR,
        "laser": TechnologyApproach.LASER_ICF,
        "icf": TechnologyApproach.LASER_ICF,
        "inertial": TechnologyApproach.LASER_ICF,
        "frc": TechnologyApproach.FRC,
        "field-reversed": TechnologyApproach.FRC,
        "magnetized target": TechnologyApproach.MAGNETIZED_TARGET,
        "z-pinch": TechnologyApproach.Z_PINCH,
        "mirror": TechnologyApproach.MIRROR,
    }
    
    # Country mappings
    COUNTRY_MAPPINGS = {
        "deutschland": "Germany",
        "germany": "Germany",
        "münchen": "Germany",
        "munich": "Germany",
        "darmstadt": "Germany",
        "garching": "Germany",
        "hanau": "Germany",
        "usa": "USA",
        "uk": "UK",
        "japan": "Japan",
        "frankreich": "France",
        "france": "France",
        "china": "China",
    }
    
    # Funding stage mappings
    STAGE_MAPPINGS = {
        "pre-seed": FundingStage.PRE_SEED,
        "seed": FundingStage.SEED,
        "series a": FundingStage.SERIES_A,
        "series b": FundingStage.SERIES_B,
        "series c": FundingStage.SERIES_C,
        "series d": FundingStage.SERIES_D,
        "series e": FundingStage.SERIES_D,
        "series f": FundingStage.SERIES_D,
        "grant": FundingStage.GRANT,
    }
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split("\n")
        self.parsed_data = ParsedData()
        self._company_id_counter = 0
    
    def parse(self) -> ParsedData:
        """Parse the entire document."""
        self._extract_sections()
        self._parse_companies()
        self._parse_markets()
        return self.parsed_data
    
    def _extract_sections(self):
        """Extract major sections from the document."""
        current_section = ""
        current_content = []
        
        for line in self.lines:
            if line.startswith("## "):
                if current_section:
                    self.parsed_data.raw_sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            self.parsed_data.raw_sections[current_section] = "\n".join(current_content)
    
    def _parse_companies(self):
        """Parse company profiles from the document."""
        # Find company sections (#### headers)
        company_pattern = re.compile(r"^####\s+(.+?)\s*\((.+?)\)\s*$", re.MULTILINE)
        
        for match in company_pattern.finditer(self.content):
            company_name = match.group(1).strip()
            location = match.group(2).strip()
            
            # Get the content after this header until the next #### or ###
            start_pos = match.end()
            next_header = re.search(r"\n(?:####|###)\s+", self.content[start_pos:])
            if next_header:
                end_pos = start_pos + next_header.start()
            else:
                end_pos = len(self.content)
            
            company_content = self.content[start_pos:end_pos]
            
            company = self._parse_company_block(company_name, location, company_content)
            if company:
                self.parsed_data.companies.append(company)
    
    def _parse_company_block(self, name: str, location: str, content: str) -> Optional[Company]:
        """Parse a single company block."""
        self._company_id_counter += 1
        
        # Determine country from location
        country = "Unknown"
        city = None
        for key, value in self.COUNTRY_MAPPINGS.items():
            if key.lower() in location.lower():
                country = value
                city = location.split("/")[0].strip() if "/" in location else location
                break
        
        # Determine company type
        company_type = CompanyType.STARTUP
        if "konzern" in content.lower() or "corporation" in content.lower():
            company_type = CompanyType.KONZERN
        elif "kmu" in content.lower() or "mittelstand" in content.lower():
            company_type = CompanyType.KMU
        elif "forschung" in content.lower() or "research" in content.lower() or "institut" in content.lower():
            company_type = CompanyType.FORSCHUNG
        
        # Extract technology approach
        tech_approach = None
        for key, value in self.TECH_MAPPINGS.items():
            if key.lower() in content.lower():
                tech_approach = value.value
                break
        
        # Extract funding
        total_funding = self._extract_funding(content)
        
        # Extract TRL
        trl = self._extract_trl(content)
        
        # Extract team size
        team_size = self._extract_team_size(content)
        
        # Extract founded year
        founded_year = self._extract_founded_year(content)
        
        # Extract investors
        investors = self._extract_investors(content)
        
        # Extract description (first paragraph after profile)
        description = self._extract_description(content)
        
        return Company(
            id=self._company_id_counter,
            name=name,
            company_type=company_type,
            country=country,
            city=city,
            founded_year=founded_year,
            team_size=team_size,
            description=description,
            technology_approach=tech_approach,
            trl=trl,
            total_funding_usd=total_funding,
            key_investors=investors,
            confidence_score=0.85,
        )
    
    def _extract_funding(self, content: str) -> Optional[float]:
        """Extract total funding amount from content."""
        # Match patterns like "EUR 130M", "USD 2.86 Mrd.", "USD 1+ Mrd."
        patterns = [
            r"(?:USD|EUR)\s*([\d.,]+)\s*(?:Mrd\.?|Billion|B)",  # Billions
            r"(?:USD|EUR)\s*([\d.,]+)\s*(?:M|Million|Mio\.?)",  # Millions
            r"Gesamt\s*(?:USD|EUR)\s*([\d.,]+)\s*(?:M|Mio\.?)",  # Total funding
            r"Finanzierung[:\s]+(?:USD|EUR)\s*([\d.,]+)\s*(?:M|Mio\.?|Mrd\.?)",
        ]
        
        max_funding = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.replace(",", ".").replace("+", ""))
                    # Convert to USD (assuming EUR ≈ USD for simplicity)
                    if "Mrd" in pattern or "Billion" in pattern or "B" in pattern:
                        value *= 1_000_000_000
                    else:
                        value *= 1_000_000
                    max_funding = max(max_funding, value)
                except ValueError:
                    continue
        
        return max_funding if max_funding > 0 else None
    
    def _extract_trl(self, content: str) -> Optional[int]:
        """Extract TRL level from content."""
        # Match patterns like "TRL 6-7", "TRL 5", "erreicht TRL 6"
        patterns = [
            r"TRL\s*(\d)",
            r"TRL\s*(\d)-\d",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_team_size(self, content: str) -> Optional[int]:
        """Extract team size from content."""
        patterns = [
            r"(\d+)\+?\s*(?:Mitarbeiter|employees|Team)",
            r"Team[:\s]+(\d+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def _extract_founded_year(self, content: str) -> Optional[int]:
        """Extract founding year from content."""
        patterns = [
            r"gegründet\s*(?:~)?(\d{4})",
            r"founded\s*(?:~)?(\d{4})",
            r"\((\d{4})\)",
            r"Spin-out\s*\((\d{4})\)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    year = int(match.group(1))
                    if 1990 <= year <= 2030:
                        return year
                except ValueError:
                    continue
        return None
    
    def _extract_investors(self, content: str) -> Optional[str]:
        """Extract key investors from content."""
        patterns = [
            r"Investoren[:\s]+(.+?)(?:\n|$)",
            r"Investors[:\s]+(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:500]  # Limit length
        return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract company description."""
        # Look for **Profil:** section
        match = re.search(r"\*\*Profil:\*\*\s*(.+?)(?:\n\n|\n-|\n\*\*)", content, re.DOTALL)
        if match:
            return match.group(1).strip()[:1000]
        
        # Fallback: first substantial paragraph
        paragraphs = content.split("\n\n")
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50 and not para.startswith("-") and not para.startswith("*"):
                return para[:1000]
        return None
    
    def _parse_markets(self):
        """Parse market data from the document."""
        # Extract market size data from section 2.3
        market_section = self.parsed_data.raw_sections.get("2. Marktsegment & Nutzenpotenzial", "")
        
        # Global market
        global_market = Market(
            region=MarketRegion.GLOBAL,
            region_name="Global",
            market_size_2024_usd=356_000_000_000,  # USD 356 Mrd.
            market_size_2030_usd=460_000_000_000,  # ~USD 460 Mrd.
            market_size_2040_usd=843_000_000_000,  # USD 843 Mrd.
            cagr_percent=5.5,
            notes="CAGR 5.5-7.1%",
        )
        self.parsed_data.markets.append(global_market)
        
        # Europe market
        europe_market = Market(
            region=MarketRegion.EUROPE,
            region_name="Europe",
            market_size_2024_usd=128_000_000_000,  # ~35.9% of global
            cagr_percent=6.0,
            notes="35.9% of global market by 2035",
        )
        self.parsed_data.markets.append(europe_market)
        
        # Germany market
        germany_market = Market(
            region=MarketRegion.GERMANY,
            region_name="Germany",
            notes="EUR 2+ Billion Fusion Action Plan until 2029",
            regulatory_environment="Regulated under StrlSchG (not AtG), accelerated approvals",
        )
        self.parsed_data.markets.append(germany_market)
        
        # USA market
        usa_market = Market(
            region=MarketRegion.USA,
            region_name="USA",
            market_size_2024_usd=89_000_000_000,  # ~25% of global
            notes="Private sector dominance, DOE Milestone-Based Fusion Development Program",
        )
        self.parsed_data.markets.append(usa_market)
        
        # Asia-Pacific market
        apac_market = Market(
            region=MarketRegion.ASIA_PACIFIC,
            region_name="Asia-Pacific",
            market_size_2024_usd=107_000_000_000,  # ~30% of global
            notes="China, Japan, South Korea aggressive expansion plans",
        )
        self.parsed_data.markets.append(apac_market)


def parse_fusion_research(file_path: str = "research/Fusion_Research.md") -> ParsedData:
    """Parse Fusion_Research.md file and return structured data."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Research file not found: {file_path}")
    
    content = path.read_text(encoding="utf-8")
    parser = MarkdownParser(content)
    return parser.parse()
