"""Settings and configuration page."""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Settings - Fusion Research", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")
st.markdown("Configure the Fusion Research Intelligence Platform.")

# LLM Configuration (Ollama)
st.markdown("### 🤖 LLM Configuration (Ollama)")

col1, col2 = st.columns(2)

with col1:
    # Ollama Server URL
    st.markdown("**Ollama Server**")
    
    ollama_url = st.text_input(
        "Ollama Base URL:",
        value=st.session_state.get("ollama_base_url", "http://localhost:11434"),
        help="URL of your local Ollama server",
    )
    st.session_state.ollama_base_url = ollama_url
    
    # Test connection
    if st.button("🔌 Test Connection"):
        try:
            import httpx
            response = httpx.get(f"{ollama_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                available = response.json().get("models", [])
                model_names = [m.get("name", "") for m in available]
                st.success(f"✅ Connected! Found {len(available)} models")
                if model_names:
                    st.info(f"Available: {', '.join(model_names[:5])}{'...' if len(model_names) > 5 else ''}")
            else:
                st.error(f"Connection failed: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

with col2:
    # LLM Model Selection
    st.markdown("**LLM Model**")
    
    models = ["qwen3:8b", "qwen3:14b", "gpt-oss:20b"]
    current_model = st.session_state.get("llm_model", "qwen3:8b")
    
    selected_model = st.selectbox(
        "Select Model:",
        models,
        index=models.index(current_model) if current_model in models else 0,
        help="Choose your local Ollama model",
    )
    
    if selected_model != current_model:
        st.session_state.llm_model = selected_model
        st.success(f"✅ Model set to {selected_model}")
    
    # Temperature
    temperature = st.slider(
        "Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("llm_temperature", 0.3),
        step=0.1,
        help="Lower = more focused, Higher = more creative",
    )
    st.session_state.llm_temperature = temperature

st.markdown("---")

# Tavily API Configuration
st.markdown("### 🔍 Tavily Web Search API")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**API Key**")
    tavily_key = st.text_input(
        "Tavily API Key:",
        value=st.session_state.get("tavily_api_key", ""),
        type="password",
        help="Get your API key at https://tavily.com",
    )
    st.session_state.tavily_api_key = tavily_key

with col2:
    st.markdown("**Test Connection**")
    if st.button("🔌 Test Tavily API"):
        if tavily_key:
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=tavily_key)
                result = client.search("fusion energy", max_results=1)
                if result.get("results"):
                    st.success("✅ Tavily API connected!")
                    st.info(f"Test result: {result['results'][0]['title'][:50]}...")
                else:
                    st.warning("Connected but no results returned")
            except Exception as e:
                st.error(f"API test failed: {e}")
        else:
            st.warning("Please enter a Tavily API key first")

st.markdown("---")

# Database Status
st.markdown("### 🗄️ Database Status")

db_path = Path("research/fusion_research.db")

col1, col2 = st.columns(2)

with col1:
    if db_path.exists():
        st.success("✅ Database connected")
        
        # Show stats
        try:
            from src.data.database import get_database
            db = get_database()
            
            tables = db.get_table_names()
            st.markdown(f"**Tables:** {len(tables)}")
            
            for table in tables:
                count = db.get_row_count(table)
                st.markdown(f"- {table}: {count} rows")
        except Exception as e:
            st.error(f"Error reading database: {e}")
    else:
        st.warning("⚠️ Database not initialized")
        st.info("Run the initialization script to set up the database.")

with col2:
    st.markdown("**Database Actions**")
    
    if st.button("🔄 Refresh Database Connection"):
        try:
            from src.data.database import get_database
            db = get_database()
            db.close()
            st.success("✅ Connection refreshed")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    
    if st.button("🗑️ Clear Cache"):
        st.cache_data.clear()
        st.success("✅ Cache cleared")

st.markdown("---")

# Data Management
st.markdown("### 📁 Data Management")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Upload Research Data**")
    
    uploaded_file = st.file_uploader(
        "Upload Fusion_Research.md",
        type=["md"],
        help="Upload an updated research document to refresh the database",
    )
    
    if uploaded_file:
        st.info(f"File: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        
        if st.button("📥 Process Upload"):
            with st.spinner("Processing..."):
                try:
                    content = uploaded_file.read().decode("utf-8")
                    
                    # Save to research folder
                    research_path = Path("research/Fusion_Research.md")
                    research_path.write_text(content, encoding="utf-8")
                    
                    # Parse and update database
                    from src.data.parsers.markdown_parser import parse_fusion_research
                    from src.data.database import get_database
                    from src.data.repositories import CompanyRepository, MarketRepository
                    
                    parsed = parse_fusion_research(str(research_path))
                    db = get_database()
                    
                    company_repo = CompanyRepository(db)
                    market_repo = MarketRepository(db)
                    
                    # Insert companies
                    new_companies = 0
                    for company in parsed.companies:
                        try:
                            company_repo.create(company)
                            new_companies += 1
                        except Exception:
                            pass  # Skip duplicates
                    
                    # Insert markets
                    new_markets = 0
                    for market in parsed.markets:
                        try:
                            market_repo.create(market)
                            new_markets += 1
                        except Exception:
                            pass
                    
                    st.success(f"✅ Processed: {new_companies} companies, {new_markets} markets")
                except Exception as e:
                    st.error(f"Error processing file: {e}")

with col2:
    st.markdown("**Export Data**")
    
    if st.button("📤 Export Companies (CSV)"):
        try:
            from src.data.database import get_database
            from src.services.company_service import CompanyService
            import pandas as pd
            
            db = get_database()
            service = CompanyService(db)
            companies = service.get_all_companies(limit=1000)
            
            data = [
                {
                    "Name": c.name,
                    "Type": c.company_type.value,
                    "Country": c.country,
                    "Founded": c.founded_year,
                    "Technology": c.technology_approach,
                    "TRL": c.trl,
                    "Funding (USD)": c.total_funding_usd,
                    "Team Size": c.team_size,
                }
                for c in companies
            ]
            
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                "📥 Download CSV",
                csv,
                file_name="fusion_companies.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"Export failed: {e}")

st.markdown("---")

# Application Info
st.markdown("### ℹ️ Application Info")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Fusion Research Intelligence Platform**
    
    Version: 0.1.0
    
    Built with:
    - Streamlit
    - LangChain + Ollama
    - Local LLMs (qwen3, gpt-oss)
    - SQLite
    - Plotly
    """)

with col2:
    st.markdown("""
    **Quick Links**
    
    - [Documentation](docs/ARCHITECTURE.md)
    - [GitHub Repository](#)
    - [Report Issues](#)
    
    **Support**
    
    For questions or issues, please check the documentation or open an issue on GitHub.
    """)

# Debug Info (collapsible)
with st.expander("🔧 Debug Information"):
    st.markdown("**Session State:**")
    st.json({
        k: str(v)[:100] if isinstance(v, str) else str(type(v).__name__)
        for k, v in st.session_state.items()
    })
    
    st.markdown("**Paths:**")
    st.markdown(f"- Project Root: {project_root}")
    st.markdown(f"- Database: {db_path}")
    st.markdown(f"- Database Exists: {db_path.exists()}")
