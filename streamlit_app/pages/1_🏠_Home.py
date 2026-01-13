"""Home dashboard page."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Home - Fusion Research", page_icon="🏠", layout="wide")

st.title("🏠 Dashboard")
st.markdown("Overview of the global fusion energy market and key metrics.")

# Check if database exists
db_path = Path("research/fusion_research.db")
if not db_path.exists():
    st.warning("⚠️ Database not initialized. Please run the initialization script first.")
    st.code("python scripts/init_db.py && python scripts/populate_sample_data.py", language="bash")
    st.stop()

try:
    from src.data.database import get_database
    from src.services.company_service import CompanyService
    from src.services.market_service import MarketService
    from src.services.technology_service import TechnologyService
    
    db = get_database()
    company_service = CompanyService(db)
    market_service = MarketService(db)
    tech_service = TechnologyService(db)
    
    # Key Metrics Row
    st.markdown("### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    stats = company_service.get_company_summary_stats()
    metrics = market_service.get_market_metrics()
    
    with col1:
        st.metric(
            "Total Companies",
            stats["total_companies"],
            help="Number of fusion companies in database"
        )
    
    with col2:
        funding_display = f"${stats['total_funding_usd'] / 1e9:.2f}B" if stats['total_funding_usd'] else "N/A"
        st.metric(
            "Total Funding",
            funding_display,
            help="Total private funding raised"
        )
    
    with col3:
        st.metric(
            "Average TRL",
            f"{stats['average_trl']:.1f}",
            help="Average Technology Readiness Level"
        )
    
    with col4:
        market_size = f"${metrics.total_market_size_2024 / 1e9:.0f}B" if metrics.total_market_size_2024 else "N/A"
        st.metric(
            "Market Size (2024)",
            market_size,
            help="Global fusion market size"
        )
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌍 Companies by Country")
        if stats["by_country"]:
            fig = px.pie(
                values=list(stats["by_country"].values()),
                names=list(stats["by_country"].keys()),
                hole=0.4,
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data available")
    
    with col2:
        st.markdown("### 🔬 Companies by Technology")
        if stats["by_technology"]:
            fig = px.bar(
                x=list(stats["by_technology"].keys()),
                y=list(stats["by_technology"].values()),
                labels={"x": "Technology", "y": "Count"},
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No technology data available")
    
    st.markdown("---")
    
    # TRL Distribution
    st.markdown("### 📈 TRL Distribution")
    trl_dist = tech_service.get_trl_distribution()
    if trl_dist:
        fig = px.bar(
            x=[d["trl"] for d in trl_dist],
            y=[d["count"] for d in trl_dist],
            labels={"x": "Technology Readiness Level", "y": "Number of Companies"},
            color=[d["count"] for d in trl_dist],
            color_continuous_scale="Blues",
        )
        fig.update_layout(
            xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No TRL data available")
    
    st.markdown("---")
    
    # Top Companies Table
    st.markdown("### 🏆 Top Funded Companies")
    top_companies = company_service.get_top_funded_companies(limit=10)
    if top_companies:
        data = [
            {
                "Company": c.name,
                "Country": c.country,
                "Technology": c.technology_approach or "N/A",
                "TRL": str(c.trl) if c.trl is not None else "N/A",
                "Funding": c.funding_display,
            }
            for c in top_companies
        ]
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.info("No company data available")
    
    # Market Projections
    st.markdown("---")
    st.markdown("### 📊 Market Size Projections")
    
    markets = market_service.get_all_markets()
    global_market = next((m for m in markets if m.region.value == "Global"), None)
    
    if global_market:
        years = ["2024", "2030", "2040"]
        sizes = [
            global_market.market_size_2024_usd or 0,
            global_market.market_size_2030_usd or 0,
            global_market.market_size_2040_usd or 0,
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=[s / 1e9 for s in sizes],
            mode="lines+markers",
            name="Market Size",
            line=dict(color="#1E88E5", width=3),
            marker=dict(size=12),
        ))
        fig.update_layout(
            yaxis_title="Market Size (USD Billions)",
            xaxis_title="Year",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"📈 Projected CAGR: {global_market.cagr_percent or 0:.1f}%")
    else:
        st.info("No market projection data available")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.exception(e)
