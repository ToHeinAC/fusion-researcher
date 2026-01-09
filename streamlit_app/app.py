"""Main Streamlit application entry point."""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Page configuration
st.set_page_config(
    page_title="Fusion Research Intelligence",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stMetric {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Main page content
st.markdown('<p class="main-header">⚛️ Fusion Research Intelligence Platform</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered nuclear fusion market intelligence</p>', unsafe_allow_html=True)

# Welcome message
st.markdown("""
Welcome to the **Fusion Research Intelligence Platform** - your comprehensive resource for 
nuclear fusion industry analysis, company profiles, and market intelligence.

### 🚀 Quick Start

Use the sidebar to navigate between different sections:

- **🏠 Home** - Dashboard with key metrics and market overview
- **🔍 Companies** - Search and browse fusion companies
- **🔬 Technologies** - Technology readiness analysis and TRL matrix
- **📊 Markets** - Market intelligence and investment landscape
- **📝 Research** - Natural language queries and report generation
- **⚙️ Settings** - Configuration and data management

### 📈 Platform Capabilities

| Feature | Description |
|---------|-------------|
| **Natural Language Search** | Query the database using plain English |
| **Company Profiles** | Detailed profiles with funding, technology, and partnerships |
| **Market Dashboard** | KPIs, charts, and trends for the fusion industry |
| **SWOT Analysis** | AI-generated strategic analysis for any company |
| **Report Generation** | Auto-generated market reports and investment theses |
| **Data Visualization** | Interactive charts and TRL heatmaps |

### 🔧 Getting Started

1. **Configure API Key**: Go to Settings and enter your OpenAI API key
2. **Load Data**: Initialize the database with research data
3. **Explore**: Start querying companies, markets, and technologies

---
*Built with Streamlit, LangChain, and OpenAI GPT-4*
""")

# Sidebar info
with st.sidebar:
    st.markdown("### ⚛️ Fusion Research")
    st.markdown("---")
    
    # Check database status
    db_path = Path("research/fusion_research.db")
    if db_path.exists():
        st.success("✅ Database connected")
        
        # Show basic stats
        try:
            from src.data.database import get_database
            db = get_database()
            company_count = db.get_row_count("companies")
            st.metric("Companies", company_count)
        except Exception as e:
            st.warning(f"Database error: {e}")
    else:
        st.warning("⚠️ Database not initialized")
        st.info("Run `python scripts/init_db.py` to set up the database")
    
    st.markdown("---")
    st.markdown("### 📚 Resources")
    st.markdown("""
    - [Fusion Industry Association](https://www.fusionindustryassociation.org/)
    - [ITER Project](https://www.iter.org/)
    - [EUROfusion](https://euro-fusion.org/)
    """)
