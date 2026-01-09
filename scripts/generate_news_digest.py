"""Generate a fusion energy news digest."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.news_service import get_news_service
from src.llm.chain_factory import get_llm


def main():
    """Generate news digest."""
    print("=" * 60)
    print("Fusion Energy News Digest Generator")
    print("=" * 60)
    
    # Get LLM for summarization
    print("\n🤖 Initializing LLM...")
    try:
        llm = get_llm(model="qwen3:8b")
        print("  Using qwen3:8b for summarization")
    except Exception as e:
        print(f"  LLM not available: {e}")
        llm = None
    
    # Create news service
    print("\n📰 Initializing news service...")
    news_service = get_news_service(llm=llm)
    
    # Generate digest
    print("\n🔍 Fetching news articles...")
    print("  - Checking RSS feeds...")
    print("  - Searching for recent news...")
    
    digest = news_service.generate_digest(
        max_age_days=7,
        include_search=True,
        summarize=llm is not None,
    )
    
    print(f"\n📊 Found {len(digest.articles)} articles:")
    high = len([a for a in digest.articles if a.relevance == "high"])
    medium = len([a for a in digest.articles if a.relevance == "medium"])
    low = len([a for a in digest.articles if a.relevance == "low"])
    print(f"  - High relevance: {high}")
    print(f"  - Medium relevance: {medium}")
    print(f"  - Low relevance: {low}")
    
    # Save digest
    print("\n💾 Saving digest...")
    filepath = news_service.save_digest(digest)
    print(f"  Saved to: {filepath}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 DIGEST PREVIEW")
    print("=" * 60)
    
    if digest.executive_summary:
        print("\n📝 Executive Summary:")
        print(digest.executive_summary[:500] + "..." if len(digest.executive_summary) > 500 else digest.executive_summary)
    
    print("\n🔥 Top Headlines:")
    for i, article in enumerate(digest.articles[:5], 1):
        relevance_icon = {"high": "🔴", "medium": "🟡", "low": "⚪"}[article.relevance]
        print(f"  {i}. {relevance_icon} {article.title[:60]}...")
        print(f"     Source: {article.source}")
    
    print(f"\n✅ Full digest saved to: {filepath}")


if __name__ == "__main__":
    main()
