"""News scraping and digest service for fusion industry news."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import httpx
import feedparser
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


@dataclass
class NewsArticle:
    """Represents a news article."""
    title: str
    url: str
    source: str
    published: Optional[datetime] = None
    summary: Optional[str] = None
    relevance: str = "medium"  # high, medium, low
    ai_summary: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        """Generate unique ID from URL."""
        return hashlib.md5(self.url.encode()).hexdigest()[:12]


@dataclass
class NewsDigest:
    """A collection of news articles with summary."""
    articles: list[NewsArticle]
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    executive_summary: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert digest to markdown format."""
        lines = [
            f"# Fusion Energy News Digest",
            f"",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Period:** {self.period_start.strftime('%Y-%m-%d')} to {self.period_end.strftime('%Y-%m-%d')}",
            f"",
        ]
        
        if self.executive_summary:
            lines.extend([
                "## Executive Summary",
                "",
                self.executive_summary,
                "",
            ])
        
        # Group by relevance
        high = [a for a in self.articles if a.relevance == "high"]
        medium = [a for a in self.articles if a.relevance == "medium"]
        low = [a for a in self.articles if a.relevance == "low"]
        
        if high:
            lines.extend(["## 🔥 High Relevance", ""])
            for article in high:
                lines.extend(self._format_article(article))
        
        if medium:
            lines.extend(["## 📰 Medium Relevance", ""])
            for article in medium:
                lines.extend(self._format_article(article))
        
        if low:
            lines.extend(["## 📋 Other News", ""])
            for article in low:
                lines.extend(self._format_article(article))
        
        return "\n".join(lines)
    
    def _format_article(self, article: NewsArticle) -> list[str]:
        """Format a single article as markdown."""
        lines = [
            f"### [{article.title}]({article.url})",
            f"",
            f"**Source:** {article.source}",
        ]
        if article.published:
            lines.append(f"**Published:** {article.published.strftime('%Y-%m-%d')}")
        if article.tags:
            lines.append(f"**Tags:** {', '.join(article.tags)}")
        lines.append("")
        
        if article.ai_summary:
            lines.extend([article.ai_summary, ""])
        elif article.summary:
            lines.extend([article.summary[:500] + "..." if len(article.summary) > 500 else article.summary, ""])
        
        lines.append("---")
        lines.append("")
        return lines


class NewsService:
    """Service for fetching and processing fusion industry news."""
    
    # RSS feeds for fusion energy news
    RSS_FEEDS = {
        "Fusion Industry Association": "https://www.fusionindustryassociation.org/feed/",
        "World Nuclear News": "https://www.world-nuclear-news.org/rss",
        "Energy.gov Fusion": "https://www.energy.gov/science/fes/rss.xml",
        "ITER News": "https://www.iter.org/rss",
    }
    
    # Keywords for relevance scoring
    HIGH_RELEVANCE_KEYWORDS = [
        "fusion", "tokamak", "stellarator", "iter", "commonwealth fusion",
        "proxima fusion", "helion", "tae technologies", "general fusion",
        "focused energy", "marvel fusion", "gauss fusion", "type one energy",
        "hts magnet", "plasma", "tritium", "deuterium", "net energy gain",
        "q>1", "first plasma", "funding", "series a", "series b", "investment",
    ]
    
    MEDIUM_RELEVANCE_KEYWORDS = [
        "nuclear", "clean energy", "energy transition", "decarbonization",
        "superconductor", "magnet", "power plant", "electricity generation",
        "doe", "department of energy", "euratom", "research reactor",
    ]
    
    def __init__(
        self,
        llm: Optional[ChatOllama] = None,
        cache_dir: str = "research/news_cache",
    ):
        self.llm = llm
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_rss_articles(self, max_age_days: int = 7) -> list[NewsArticle]:
        """Fetch articles from RSS feeds."""
        articles = []
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        for source_name, feed_url in self.RSS_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Limit per source
                    # Parse published date
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime(*entry.updated_parsed[:6])
                    
                    # Skip old articles
                    if published and published < cutoff:
                        continue
                    
                    article = NewsArticle(
                        title=entry.get('title', 'No title'),
                        url=entry.get('link', ''),
                        source=source_name,
                        published=published,
                        summary=entry.get('summary', ''),
                    )
                    
                    # Score relevance
                    article.relevance = self._score_relevance(article)
                    article.tags = self._extract_tags(article)
                    
                    articles.append(article)
                    
            except Exception as e:
                print(f"Error fetching {source_name}: {e}")
        
        return articles
    
    def search_news(self, query: str, max_results: int = 10) -> list[NewsArticle]:
        """Search for news using web search (via DuckDuckGo)."""
        articles = []
        
        try:
            # Use DuckDuckGo HTML search
            search_url = "https://html.duckduckgo.com/html/"
            params = {"q": f"{query} fusion energy news", "t": "h_"}
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(search_url, data=params)
                
                if response.status_code == 200:
                    # Simple parsing of DuckDuckGo results
                    from html.parser import HTMLParser
                    
                    class DDGParser(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.results = []
                            self.in_result = False
                            self.current_title = ""
                            self.current_url = ""
                            self.current_snippet = ""
                        
                        def handle_starttag(self, tag, attrs):
                            attrs_dict = dict(attrs)
                            if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                                self.in_result = True
                                self.current_url = attrs_dict.get("href", "")
                        
                        def handle_data(self, data):
                            if self.in_result:
                                self.current_title = data.strip()
                        
                        def handle_endtag(self, tag):
                            if tag == "a" and self.in_result:
                                if self.current_title and self.current_url:
                                    self.results.append({
                                        "title": self.current_title,
                                        "url": self.current_url,
                                    })
                                self.in_result = False
                                self.current_title = ""
                                self.current_url = ""
                    
                    parser = DDGParser()
                    parser.feed(response.text)
                    
                    for result in parser.results[:max_results]:
                        article = NewsArticle(
                            title=result["title"],
                            url=result["url"],
                            source="Web Search",
                            published=datetime.now(),
                        )
                        article.relevance = self._score_relevance(article)
                        article.tags = self._extract_tags(article)
                        articles.append(article)
                        
        except Exception as e:
            print(f"Search error: {e}")
        
        return articles
    
    def _score_relevance(self, article: NewsArticle) -> str:
        """Score article relevance based on keywords."""
        text = f"{article.title} {article.summary or ''}".lower()
        
        high_count = sum(1 for kw in self.HIGH_RELEVANCE_KEYWORDS if kw in text)
        medium_count = sum(1 for kw in self.MEDIUM_RELEVANCE_KEYWORDS if kw in text)
        
        if high_count >= 2:
            return "high"
        elif high_count >= 1 or medium_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _extract_tags(self, article: NewsArticle) -> list[str]:
        """Extract relevant tags from article."""
        text = f"{article.title} {article.summary or ''}".lower()
        tags = []
        
        # Technology tags
        if any(kw in text for kw in ["tokamak", "iter"]):
            tags.append("Tokamak")
        if "stellarator" in text:
            tags.append("Stellarator")
        if any(kw in text for kw in ["laser", "inertial"]):
            tags.append("Laser/ICF")
        
        # Topic tags
        if any(kw in text for kw in ["funding", "investment", "series", "raise"]):
            tags.append("Funding")
        if any(kw in text for kw in ["milestone", "breakthrough", "achieve"]):
            tags.append("Milestone")
        if any(kw in text for kw in ["policy", "regulation", "government"]):
            tags.append("Policy")
        if any(kw in text for kw in ["partnership", "collaboration", "agreement"]):
            tags.append("Partnership")
        
        # Company tags
        companies = [
            "Commonwealth Fusion", "Proxima Fusion", "Helion", "TAE",
            "General Fusion", "Focused Energy", "Marvel Fusion", "Gauss Fusion",
        ]
        for company in companies:
            if company.lower() in text:
                tags.append(company)
        
        return tags[:5]  # Limit tags
    
    def summarize_article(self, article: NewsArticle) -> str:
        """Use LLM to summarize an article."""
        if not self.llm:
            return article.summary or ""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fusion energy industry analyst. Summarize the following news article in 2-3 sentences.
Focus on: key facts, companies mentioned, funding amounts, technology milestones, and industry implications.
Be concise and factual."""),
            ("human", """Title: {title}
Source: {source}
Content: {content}

Summary:"""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            summary = chain.invoke({
                "title": article.title,
                "source": article.source,
                "content": article.summary or article.title,
            })
            return summary.strip()
        except Exception as e:
            return f"Summary unavailable: {e}"
    
    def generate_digest(
        self,
        max_age_days: int = 7,
        include_search: bool = True,
        summarize: bool = True,
    ) -> NewsDigest:
        """Generate a complete news digest."""
        # Fetch articles
        articles = self.fetch_rss_articles(max_age_days=max_age_days)
        
        # Add search results for key topics
        if include_search:
            search_queries = [
                "fusion energy startup funding 2024",
                "tokamak stellarator breakthrough",
                "fusion power plant progress",
            ]
            for query in search_queries:
                articles.extend(self.search_news(query, max_results=5))
        
        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        # Sort by relevance and date
        unique_articles.sort(
            key=lambda a: (
                {"high": 0, "medium": 1, "low": 2}[a.relevance],
                -(a.published.timestamp() if a.published else 0),
            )
        )
        
        # Summarize top articles
        if summarize and self.llm:
            for article in unique_articles[:10]:  # Limit LLM calls
                if article.relevance in ["high", "medium"]:
                    article.ai_summary = self.summarize_article(article)
        
        # Create digest
        now = datetime.now()
        digest = NewsDigest(
            articles=unique_articles[:20],  # Limit total articles
            generated_at=now,
            period_start=now - timedelta(days=max_age_days),
            period_end=now,
        )
        
        # Generate executive summary
        if self.llm and unique_articles:
            digest.executive_summary = self._generate_executive_summary(unique_articles[:10])
        
        return digest
    
    def _generate_executive_summary(self, articles: list[NewsArticle]) -> str:
        """Generate executive summary of top articles."""
        if not self.llm:
            return ""
        
        # Build article list
        article_texts = []
        for i, article in enumerate(articles, 1):
            article_texts.append(f"{i}. {article.title} ({article.source})")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fusion energy industry analyst writing a weekly digest for investors and researchers.
Write a brief executive summary (3-4 paragraphs) of the key developments in fusion energy this week.
Highlight: major funding rounds, technology milestones, policy changes, and notable partnerships.
Be concise, factual, and focus on actionable insights."""),
            ("human", """This week's top fusion energy news:

{articles}

Executive Summary:"""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            return chain.invoke({"articles": "\n".join(article_texts)})
        except Exception as e:
            return f"Summary generation failed: {e}"
    
    def save_digest(self, digest: NewsDigest, filename: Optional[str] = None) -> Path:
        """Save digest to file."""
        if filename is None:
            filename = f"digest_{digest.generated_at.strftime('%Y%m%d_%H%M')}.md"
        
        filepath = self.cache_dir / filename
        filepath.write_text(digest.to_markdown(), encoding="utf-8")
        return filepath
    
    def load_cached_digests(self, limit: int = 10) -> list[Path]:
        """Load cached digest files."""
        digests = sorted(
            self.cache_dir.glob("digest_*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return digests[:limit]


def get_news_service(
    llm: Optional[ChatOllama] = None,
    cache_dir: str = "research/news_cache",
) -> NewsService:
    """Get news service instance."""
    return NewsService(llm=llm, cache_dir=cache_dir)
