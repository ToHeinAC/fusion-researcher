"""News digest page for fusion industry news."""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="News - Fusion Research", page_icon="📰", layout="wide")

st.title("📰 Fusion Energy News")
st.markdown("Stay updated with the latest fusion industry news and developments.")

try:
    from src.services.news_service import get_news_service, NewsDigest
    from src.llm.chain_factory import get_llm
    
    # Get Ollama settings
    ollama_model = st.session_state.get("llm_model", "qwen3:8b")
    ollama_url = st.session_state.get("ollama_base_url", "http://localhost:11434")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📰 Generate Digest", "📚 Saved Digests", "🔍 Search News"])
    
    with tab1:
        st.markdown("### 📰 Generate News Digest")
        st.markdown("Fetch and summarize the latest fusion energy news from multiple sources.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_age = st.slider("News age (days):", 1, 30, 7, key="news_age")
            include_search = st.checkbox("Include web search", value=True, key="news_search")
        
        with col2:
            summarize = st.checkbox("AI summarization", value=True, key="news_summarize")
            st.caption(f"Using model: {ollama_model}")
        
        if st.button("🔄 Generate Digest", type="primary", key="generate_digest"):
            with st.spinner("Fetching news articles..."):
                try:
                    # Initialize LLM if summarization enabled
                    llm = None
                    if summarize:
                        try:
                            llm = get_llm(model=ollama_model, base_url=ollama_url)
                        except Exception as e:
                            st.warning(f"LLM not available: {e}")
                    
                    # Create service and generate digest
                    news_service = get_news_service(llm=llm)
                    
                    with st.status("Generating digest...", expanded=True) as status:
                        st.write("📡 Fetching RSS feeds...")
                        digest = news_service.generate_digest(
                            max_age_days=max_age,
                            include_search=include_search,
                            summarize=summarize,
                        )
                        st.write(f"✅ Found {len(digest.articles)} articles")
                        
                        # Save digest
                        filepath = news_service.save_digest(digest)
                        st.write(f"💾 Saved to {filepath.name}")
                        status.update(label="Digest complete!", state="complete")
                    
                    # Store in session state
                    st.session_state.current_digest = digest
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to generate digest: {e}")
        
        # Display current digest
        if "current_digest" in st.session_state:
            digest = st.session_state.current_digest
            
            st.markdown("---")
            st.markdown(f"**Generated:** {digest.generated_at.strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Period:** {digest.period_start.strftime('%Y-%m-%d')} to {digest.period_end.strftime('%Y-%m-%d')}")
            st.markdown(f"**Articles:** {len(digest.articles)}")
            
            # Executive summary
            if digest.executive_summary:
                with st.expander("📝 Executive Summary", expanded=True):
                    st.markdown(digest.executive_summary)
            
            # Articles by relevance
            high = [a for a in digest.articles if a.relevance == "high"]
            medium = [a for a in digest.articles if a.relevance == "medium"]
            low = [a for a in digest.articles if a.relevance == "low"]
            
            if high:
                st.markdown("### 🔥 High Relevance")
                for article in high:
                    with st.expander(f"📰 {article.title}", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Source:** {article.source}")
                            if article.published:
                                st.markdown(f"**Published:** {article.published.strftime('%Y-%m-%d')}")
                            if article.tags:
                                st.markdown(f"**Tags:** {', '.join(article.tags)}")
                        with col2:
                            st.link_button("🔗 Read Article", article.url)
                        
                        if article.ai_summary:
                            st.markdown("**AI Summary:**")
                            st.markdown(article.ai_summary)
                        elif article.summary:
                            st.markdown("**Summary:**")
                            st.markdown(article.summary[:500] + "..." if len(article.summary) > 500 else article.summary)
            
            if medium:
                st.markdown("### 📰 Medium Relevance")
                for article in medium[:10]:  # Limit display
                    with st.expander(f"📰 {article.title}", expanded=False):
                        st.markdown(f"**Source:** {article.source}")
                        if article.published:
                            st.markdown(f"**Published:** {article.published.strftime('%Y-%m-%d')}")
                        st.link_button("🔗 Read Article", article.url)
                        if article.ai_summary:
                            st.markdown(article.ai_summary)
            
            if low:
                st.markdown("### 📋 Other News")
                for article in low[:5]:  # Limit display
                    st.markdown(f"- [{article.title}]({article.url}) ({article.source})")
            
            # Download button
            st.markdown("---")
            st.download_button(
                "📥 Download Digest (Markdown)",
                digest.to_markdown(),
                file_name=f"fusion_news_digest_{digest.generated_at.strftime('%Y%m%d')}.md",
                mime="text/markdown",
                key="download_digest",
            )
    
    with tab2:
        st.markdown("### 📚 Saved Digests")
        st.markdown("View previously generated news digests.")
        
        news_service = get_news_service()
        cached_digests = news_service.load_cached_digests(limit=20)
        
        if cached_digests:
            for filepath in cached_digests:
                # Parse date from filename
                filename = filepath.name
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"📄 **{filename}**")
                
                with col2:
                    # Show file date
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    st.caption(mtime.strftime("%Y-%m-%d %H:%M"))
                
                with col3:
                    if st.button("View", key=f"view_{filename}"):
                        content = filepath.read_text(encoding="utf-8")
                        st.session_state.viewing_digest = content
                        st.session_state.viewing_digest_name = filename
            
            # Display selected digest
            if "viewing_digest" in st.session_state:
                st.markdown("---")
                st.markdown(f"### 📖 {st.session_state.viewing_digest_name}")
                st.markdown(st.session_state.viewing_digest)
        else:
            st.info("No saved digests found. Generate a digest first!")
    
    with tab3:
        st.markdown("### 🔍 Search News")
        st.markdown("Search for specific fusion energy news topics.")
        
        search_query = st.text_input(
            "Search query:",
            placeholder="e.g., Commonwealth Fusion funding, stellarator breakthrough",
            key="news_search_query",
        )
        
        if st.button("🔍 Search", type="primary", key="search_news_btn"):
            if search_query:
                with st.spinner("Searching..."):
                    try:
                        news_service = get_news_service()
                        articles = news_service.search_news(search_query, max_results=15)
                        
                        if articles:
                            st.success(f"Found {len(articles)} results")
                            
                            for article in articles:
                                relevance_icon = {"high": "🔴", "medium": "🟡", "low": "⚪"}[article.relevance]
                                with st.expander(f"{relevance_icon} {article.title}", expanded=False):
                                    st.markdown(f"**Source:** {article.source}")
                                    if article.tags:
                                        st.markdown(f"**Tags:** {', '.join(article.tags)}")
                                    st.link_button("🔗 Open", article.url)
                        else:
                            st.warning("No results found. Try different keywords.")
                    except Exception as e:
                        st.error(f"Search failed: {e}")
            else:
                st.warning("Please enter a search query.")

except Exception as e:
    st.error(f"Error loading news page: {e}")
    st.exception(e)
