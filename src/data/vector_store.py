"""ChromaDB vector store for semantic search."""

import os
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import OllamaEmbeddings

from src.config import get_settings


class VectorStore:
    """ChromaDB-based vector store for semantic search over fusion research data."""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "fusion_research",
        embedding_model: str = "nomic-embed-text",
        ollama_base_url: str = "http://localhost:11434",
    ):
        settings = get_settings()
        self.persist_directory = persist_directory or str(settings.chroma_db_path)
        self.collection_name = collection_name
        
        # Use Ollama embeddings (local)
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=ollama_base_url,
        )
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def vectorstore(self) -> Chroma:
        """Get or create the Chroma vectorstore."""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )
        return self._vectorstore
    
    def add_documents(self, documents: list[Document]) -> list[str]:
        """Add documents to the vector store."""
        return self.vectorstore.add_documents(documents)
    
    def add_company(
        self,
        company_id: int,
        name: str,
        description: str,
        technology: Optional[str] = None,
        country: Optional[str] = None,
        funding: Optional[float] = None,
        trl: Optional[int] = None,
    ) -> str:
        """Add a company to the vector store."""
        # Create rich text content for embedding
        content_parts = [f"Company: {name}"]
        if description:
            content_parts.append(f"Description: {description}")
        if technology:
            content_parts.append(f"Technology: {technology}")
        if country:
            content_parts.append(f"Country: {country}")
        if funding:
            content_parts.append(f"Total Funding: ${funding:,.0f}")
        if trl:
            content_parts.append(f"Technology Readiness Level (TRL): {trl}")
        
        content = "\n".join(content_parts)
        
        doc = Document(
            page_content=content,
            metadata={
                "type": "company",
                "company_id": company_id,
                "name": name,
                "technology": technology or "",
                "country": country or "",
                "funding": funding or 0,
                "trl": trl or 0,
            }
        )
        
        ids = self.vectorstore.add_documents([doc])
        return ids[0] if ids else ""
    
    def add_technology(
        self,
        tech_id: int,
        name: str,
        approach: str,
        description: str,
        trl_range: str = "",
        challenges: str = "",
    ) -> str:
        """Add a technology to the vector store."""
        content_parts = [
            f"Technology: {name}",
            f"Approach: {approach}",
        ]
        if description:
            content_parts.append(f"Description: {description}")
        if trl_range:
            content_parts.append(f"TRL Range: {trl_range}")
        if challenges:
            content_parts.append(f"Challenges: {challenges}")
        
        content = "\n".join(content_parts)
        
        doc = Document(
            page_content=content,
            metadata={
                "type": "technology",
                "tech_id": tech_id,
                "name": name,
                "approach": approach,
            }
        )
        
        ids = self.vectorstore.add_documents([doc])
        return ids[0] if ids else ""
    
    def add_market(
        self,
        market_id: int,
        region: str,
        market_size: float,
        cagr: float,
        description: str = "",
    ) -> str:
        """Add market data to the vector store."""
        content_parts = [
            f"Market Region: {region}",
            f"Market Size: ${market_size:,.0f}",
            f"CAGR: {cagr:.1f}%",
        ]
        if description:
            content_parts.append(f"Description: {description}")
        
        content = "\n".join(content_parts)
        
        doc = Document(
            page_content=content,
            metadata={
                "type": "market",
                "market_id": market_id,
                "region": region,
                "market_size": market_size,
                "cagr": cagr,
            }
        )
        
        ids = self.vectorstore.add_documents([doc])
        return ids[0] if ids else ""
    
    def add_research_chunk(
        self,
        chunk_id: str,
        content: str,
        section: str = "",
        source: str = "Fusion_Research.md",
    ) -> str:
        """Add a research document chunk to the vector store."""
        doc = Document(
            page_content=content,
            metadata={
                "type": "research",
                "chunk_id": chunk_id,
                "section": section,
                "source": source,
            }
        )
        
        ids = self.vectorstore.add_documents([doc])
        return ids[0] if ids else ""
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_type: Optional[str] = None,
    ) -> list[Document]:
        """Search for similar documents."""
        filter_dict = {"type": filter_type} if filter_type else None
        return self.vectorstore.similarity_search(query, k=k, filter=filter_dict)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_type: Optional[str] = None,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents with relevance scores."""
        filter_dict = {"type": filter_type} if filter_type else None
        return self.vectorstore.similarity_search_with_score(query, k=k, filter=filter_dict)
    
    def search_companies(self, query: str, k: int = 5) -> list[Document]:
        """Search for companies matching the query."""
        return self.similarity_search(query, k=k, filter_type="company")
    
    def search_technologies(self, query: str, k: int = 5) -> list[Document]:
        """Search for technologies matching the query."""
        return self.similarity_search(query, k=k, filter_type="technology")
    
    def search_markets(self, query: str, k: int = 5) -> list[Document]:
        """Search for market data matching the query."""
        return self.similarity_search(query, k=k, filter_type="market")
    
    def search_research(self, query: str, k: int = 5) -> list[Document]:
        """Search research document chunks."""
        return self.similarity_search(query, k=k, filter_type="research")
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the vector store collection."""
        collection = self.vectorstore._collection
        return {
            "name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory,
        }
    
    def clear(self):
        """Clear all documents from the collection."""
        global _vector_store
        self.vectorstore.delete_collection()
        self._vectorstore = None
        _vector_store = None  # Reset singleton so next get_vector_store() creates fresh instance


# Singleton instance
_vector_store: Optional[VectorStore] = None


def reset_vector_store():
    """Reset the singleton vector store instance."""
    global _vector_store
    _vector_store = None


def get_vector_store(
    persist_directory: Optional[str] = None,
    embedding_model: str = "nomic-embed-text",
    ollama_base_url: str = "http://localhost:11434",
) -> VectorStore:
    """Get or create the singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(
            persist_directory=persist_directory,
            embedding_model=embedding_model,
            ollama_base_url=ollama_base_url,
        )
    return _vector_store
