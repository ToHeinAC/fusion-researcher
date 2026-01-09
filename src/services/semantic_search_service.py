"""Semantic search service using ChromaDB vector store."""

from typing import Optional
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.data.vector_store import VectorStore, get_vector_store
from src.data.database import Database


@dataclass
class SemanticSearchResult:
    """Result from semantic search."""
    query: str
    results: list[dict]
    answer: Optional[str] = None
    sources: list[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []


class SemanticSearchService:
    """Service for semantic search over fusion research data."""
    
    def __init__(
        self,
        db: Database,
        vector_store: Optional[VectorStore] = None,
        llm: Optional[ChatOllama] = None,
    ):
        self.db = db
        self.vector_store = vector_store or get_vector_store()
        self.llm = llm
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_type: Optional[str] = None,
    ) -> SemanticSearchResult:
        """Perform semantic search and return results."""
        docs = self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter_type=filter_type,
        )
        
        results = []
        sources = []
        
        for doc, score in docs:
            result = {
                "content": doc.page_content,
                "score": float(score),
                "type": doc.metadata.get("type", "unknown"),
                **doc.metadata,
            }
            results.append(result)
            
            # Build source citation
            doc_type = doc.metadata.get("type", "")
            if doc_type == "company":
                sources.append(f"Company: {doc.metadata.get('name', 'Unknown')}")
            elif doc_type == "technology":
                sources.append(f"Technology: {doc.metadata.get('name', 'Unknown')}")
            elif doc_type == "market":
                sources.append(f"Market: {doc.metadata.get('region', 'Unknown')}")
            elif doc_type == "research":
                sources.append(f"Research: {doc.metadata.get('section', 'Unknown section')}")
        
        return SemanticSearchResult(
            query=query,
            results=results,
            sources=sources,
        )
    
    def search_with_answer(
        self,
        query: str,
        k: int = 5,
        filter_type: Optional[str] = None,
    ) -> SemanticSearchResult:
        """Perform semantic search and generate an LLM answer."""
        # First get search results
        search_result = self.search(query, k=k, filter_type=filter_type)
        
        if not self.llm:
            return search_result
        
        # Build context from results
        context_parts = []
        for i, result in enumerate(search_result.results, 1):
            context_parts.append(f"[{i}] {result['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fusion energy industry expert. Answer the user's question based on the provided context.
Be concise and factual. Use bullet points when listing multiple items.
Always cite your sources using [1], [2], etc. to reference the context items.
If the context doesn't contain enough information, say so clearly."""),
            ("human", """Context:
{context}

Question: {query}

Answer:"""),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            answer = chain.invoke({
                "context": context,
                "query": query,
            })
            search_result.answer = answer
        except Exception as e:
            search_result.answer = f"Error generating answer: {e}"
        
        return search_result
    
    def find_similar_companies(self, company_name: str, k: int = 5) -> list[dict]:
        """Find companies similar to the given company."""
        # First, get the company's description
        query = f"Companies similar to {company_name} in fusion energy"
        docs = self.vector_store.search_companies(query, k=k+1)  # +1 to exclude self
        
        results = []
        for doc in docs:
            name = doc.metadata.get("name", "")
            if name.lower() != company_name.lower():  # Exclude the query company
                results.append({
                    "name": name,
                    "technology": doc.metadata.get("technology", ""),
                    "country": doc.metadata.get("country", ""),
                    "funding": doc.metadata.get("funding", 0),
                    "trl": doc.metadata.get("trl", 0),
                    "content": doc.page_content,
                })
        
        return results[:k]
    
    def find_companies_by_technology(self, technology: str, k: int = 10) -> list[dict]:
        """Find companies working on a specific technology."""
        query = f"Fusion companies using {technology} technology approach"
        docs = self.vector_store.search_companies(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "name": doc.metadata.get("name", ""),
                "technology": doc.metadata.get("technology", ""),
                "country": doc.metadata.get("country", ""),
                "funding": doc.metadata.get("funding", 0),
                "trl": doc.metadata.get("trl", 0),
            })
        
        return results
    
    def research_question(self, question: str, k: int = 8) -> SemanticSearchResult:
        """Answer a research question using the full knowledge base."""
        # Search across all document types
        return self.search_with_answer(query=question, k=k, filter_type=None)
    
    def get_market_insights(self, region: str) -> SemanticSearchResult:
        """Get market insights for a specific region."""
        query = f"Fusion energy market analysis and trends in {region}"
        return self.search_with_answer(query=query, k=5, filter_type=None)
    
    def technology_comparison(self, tech1: str, tech2: str) -> SemanticSearchResult:
        """Compare two fusion technologies."""
        query = f"Compare {tech1} vs {tech2} fusion technology approaches, advantages, challenges, and companies"
        return self.search_with_answer(query=query, k=8, filter_type=None)
