"""LLM-powered analysis functions for fusion industry insights."""

from typing import Optional
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models.company import Company


@dataclass
class SWOTAnalysis:
    """SWOT analysis result."""
    company_name: str
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]
    raw_markdown: str


@dataclass
class CompanyComparison:
    """Company comparison result."""
    company_a: str
    company_b: str
    comparison_table: str
    key_differentiators: list[str]
    recommendation: str
    raw_markdown: str


@dataclass
class MarketInsight:
    """Market insight result."""
    question: str
    answer: str
    data_points: list[str]
    sources: list[str]


class FusionAnalyzer:
    """LLM-powered analyzer for fusion industry insights."""
    
    def __init__(self, llm: ChatOllama):
        self.llm = llm
    
    def generate_swot(
        self,
        company: Company,
        market_context: str = "",
    ) -> SWOTAnalysis:
        """Generate SWOT analysis for a company."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strategic analyst specializing in the nuclear fusion industry.
Generate a comprehensive SWOT analysis based on the provided company data.
Each section should have 3-4 bullet points with specific data references.
Be objective and data-driven."""),
            ("human", """Generate a SWOT analysis for {company_name}.

Company Data:
- Type: {company_type}
- Country: {country}
- Founded: {founded_year}
- Technology: {technology}
- TRL: {trl}
- Total Funding: {funding}
- Team Size: {team_size}
- Key Investors: {investors}
- Description: {description}

Market Context:
{market_context}

Provide a structured SWOT analysis with 3-4 specific, data-backed points per section."""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({
            "company_name": company.name,
            "company_type": company.company_type.value,
            "country": company.country,
            "founded_year": company.founded_year or "Unknown",
            "technology": company.technology_approach or "Unknown",
            "trl": company.trl or "Unknown",
            "funding": company.funding_display,
            "team_size": company.team_size or "Unknown",
            "investors": company.key_investors or "Not disclosed",
            "description": company.description or "No description available",
            "market_context": market_context or "General fusion market context",
        })
        
        # Parse the result into structured format
        strengths = self._extract_section(result, "Strengths")
        weaknesses = self._extract_section(result, "Weaknesses")
        opportunities = self._extract_section(result, "Opportunities")
        threats = self._extract_section(result, "Threats")
        
        return SWOTAnalysis(
            company_name=company.name,
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
            raw_markdown=result,
        )
    
    def compare_companies(
        self,
        company_a: Company,
        company_b: Company,
    ) -> CompanyComparison:
        """Compare two companies head-to-head."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert analyst comparing fusion companies.
Provide objective, data-driven comparisons across key metrics.
Include a comparison table and narrative analysis."""),
            ("human", """Compare these two fusion companies:

**{company_a_name}**
- Type: {company_a_type}
- Country: {company_a_country}
- Technology: {company_a_tech}
- TRL: {company_a_trl}
- Funding: {company_a_funding}
- Team: {company_a_team}

**{company_b_name}**
- Type: {company_b_type}
- Country: {company_b_country}
- Technology: {company_b_tech}
- TRL: {company_b_trl}
- Funding: {company_b_funding}
- Team: {company_b_team}

Provide:
1. A comparison table with key metrics
2. Key differentiators (3-4 points)
3. Competitive positioning analysis
4. Investment recommendation"""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({
            "company_a_name": company_a.name,
            "company_a_type": company_a.company_type.value,
            "company_a_country": company_a.country,
            "company_a_tech": company_a.technology_approach or "Unknown",
            "company_a_trl": company_a.trl or "Unknown",
            "company_a_funding": company_a.funding_display,
            "company_a_team": company_a.team_size or "Unknown",
            "company_b_name": company_b.name,
            "company_b_type": company_b.company_type.value,
            "company_b_country": company_b.country,
            "company_b_tech": company_b.technology_approach or "Unknown",
            "company_b_trl": company_b.trl or "Unknown",
            "company_b_funding": company_b.funding_display,
            "company_b_team": company_b.team_size or "Unknown",
        })
        
        return CompanyComparison(
            company_a=company_a.name,
            company_b=company_b.name,
            comparison_table=self._extract_table(result),
            key_differentiators=self._extract_section(result, "differentiator"),
            recommendation=self._extract_section(result, "recommendation")[0] if self._extract_section(result, "recommendation") else "",
            raw_markdown=result,
        )
    
    def answer_question(
        self,
        question: str,
        context: str,
    ) -> MarketInsight:
        """Answer an open-ended question about the fusion industry."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert analyst specializing in the nuclear fusion industry.
Answer questions with specific data points and citations.
Be concise but comprehensive. Use bullet points for clarity.
If you don't have specific data, acknowledge the limitation."""),
            ("human", """Question: {question}

Available Context:
{context}

Provide a clear, data-driven answer with specific references."""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({
            "question": question,
            "context": context,
        })
        
        return MarketInsight(
            question=question,
            answer=result,
            data_points=self._extract_data_points(result),
            sources=[],
        )
    
    def generate_market_report(
        self,
        market_data: str,
        focus_area: str = "general",
    ) -> str:
        """Generate a market report section."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market analyst specializing in the fusion energy sector.
Generate professional market reports with clear sections and data-driven insights.
Include charts descriptions, key metrics, and strategic recommendations."""),
            ("human", """Generate a market report section focused on: {focus_area}

Market Data:
{market_data}

Include:
1. Executive Summary (2-3 sentences)
2. Key Metrics
3. Trends and Analysis
4. Regional Breakdown (if applicable)
5. Strategic Implications"""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "focus_area": focus_area,
            "market_data": market_data,
        })
    
    def _extract_section(self, text: str, section_name: str) -> list[str]:
        """Extract bullet points from a section."""
        import re
        
        # Find section
        pattern = rf"(?:##?\s*)?{section_name}[:\s]*\n((?:[-•*]\s*.+\n?)+)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if not match:
            return []
        
        section_text = match.group(1)
        
        # Extract bullet points
        bullets = re.findall(r"[-•*]\s*(.+)", section_text)
        return [b.strip() for b in bullets if b.strip()]
    
    def _extract_table(self, text: str) -> str:
        """Extract markdown table from text."""
        import re
        
        # Find table pattern
        pattern = r"\|.+\|[\s\S]*?\|.+\|"
        match = re.search(pattern, text)
        
        if match:
            return match.group(0)
        return ""
    
    def _extract_data_points(self, text: str) -> list[str]:
        """Extract specific data points from text."""
        import re
        
        # Find numbers with context
        patterns = [
            r"\$[\d.,]+\s*(?:billion|million|B|M)",
            r"(?:USD|EUR)\s*[\d.,]+\s*(?:billion|million|Mrd|M)",
            r"\d+%",
            r"TRL\s*\d",
            r"\d+\s*(?:employees|companies|startups)",
        ]
        
        data_points = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            data_points.extend(matches)
        
        return list(set(data_points))[:10]  # Limit to 10 unique points
