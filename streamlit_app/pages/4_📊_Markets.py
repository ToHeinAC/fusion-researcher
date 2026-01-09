"""Markets intelligence page."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Markets - Fusion Research", page_icon="📊", layout="wide")

st.title("📊 Markets")
st.markdown("Market intelligence and investment landscape analysis.")

# Check if database exists
db_path = Path("research/fusion_research.db")
if not db_path.exists():
    st.warning("⚠️ Database not initialized.")
    st.stop()

try:
    from src.data.database import get_database
    from src.services.market_service import MarketService
    
    db = get_database()
    market_service = MarketService(db)
    
    # Key Metrics
    st.markdown("### 📈 Market Overview")
    
    metrics = market_service.get_market_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        size_2024 = f"${metrics.total_market_size_2024 / 1e9:.0f}B" if metrics.total_market_size_2024 else "N/A"
        st.metric("Market Size (2024)", size_2024)
    
    with col2:
        size_2040 = f"${metrics.total_market_size_2040 / 1e9:.0f}B" if metrics.total_market_size_2040 else "N/A"
        st.metric("Market Size (2040)", size_2040)
    
    with col3:
        st.metric("CAGR", f"{metrics.cagr:.1f}%")
    
    with col4:
        funding = f"${metrics.total_funding / 1e9:.2f}B" if metrics.total_funding else "N/A"
        st.metric("Total Private Funding", funding)
    
    st.markdown("---")
    
    # Market Size Projections
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
        fig.add_trace(go.Bar(
            x=years,
            y=[s / 1e9 for s in sizes],
            marker_color=["#1E88E5", "#42A5F5", "#90CAF9"],
            text=[f"${s/1e9:.0f}B" for s in sizes],
            textposition="outside",
        ))
        fig.update_layout(
            yaxis_title="Market Size (USD Billions)",
            xaxis_title="Year",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Regional Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌍 Regional Distribution")
        
        regional = market_service.get_regional_distribution()
        
        if regional:
            fig = px.pie(
                values=[r["count"] for r in regional],
                names=[r["country"] for r in regional],
                hole=0.4,
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No regional data available")
    
    with col2:
        st.markdown("### 💰 Funding by Region")
        
        if regional:
            fig = px.bar(
                x=[r["country"] for r in regional[:10]],
                y=[r["funding"] / 1e6 for r in regional[:10]],
                labels={"x": "Country", "y": "Funding (USD Millions)"},
                color=[r["funding"] for r in regional[:10]],
                color_continuous_scale="Greens",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No funding data available")
    
    st.markdown("---")
    
    # Investment Landscape
    st.markdown("### 💼 Investment Landscape")
    
    investment = market_service.get_investment_landscape()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Funding by Stage")
        if investment["by_stage"]:
            fig = px.bar(
                x=[s["stage"] for s in investment["by_stage"]],
                y=[s["total"] / 1e6 for s in investment["by_stage"]],
                labels={"x": "Stage", "y": "Total (USD Millions)"},
                color=[s["count"] for s in investment["by_stage"]],
                color_continuous_scale="Blues",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No stage data available")
    
    with col2:
        st.markdown("#### Top Investors")
        if investment["top_investors"]:
            for inv in investment["top_investors"][:5]:
                total = f"${inv['total']/1e6:.1f}M" if inv['total'] else "N/A"
                st.markdown(f"**{inv['investor']}**: {total} ({inv['deals']} deals)")
        else:
            st.info("No investor data available")
    
    st.markdown("---")
    
    # Funding Trends
    st.markdown("### 📈 Funding Trends")
    
    funding_trends = market_service.get_funding_trends()
    
    if funding_trends:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[t["year"] for t in funding_trends],
            y=[t["total"] / 1e6 for t in funding_trends],
            mode="lines+markers",
            line=dict(color="#1E88E5", width=3),
            marker=dict(size=10),
            fill="tozeroy",
            fillcolor="rgba(30, 136, 229, 0.2)",
        ))
        fig.update_layout(
            yaxis_title="Funding (USD Millions)",
            xaxis_title="Year",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No funding trend data available")
    
    st.markdown("---")
    
    # Market Details Table
    st.markdown("### 📋 Market Details by Region")
    
    if markets:
        table_data = [
            {
                "Region": m.region_name,
                "Market Size 2024": f"${m.market_size_2024_usd/1e9:.1f}B" if m.market_size_2024_usd else "N/A",
                "CAGR": f"{m.cagr_percent:.1f}%" if m.cagr_percent else "N/A",
                "Companies": m.company_count,
                "Notes": (m.notes or "")[:100],
            }
            for m in markets
        ]
        st.dataframe(table_data, use_container_width=True, hide_index=True)
    else:
        st.info("No market data available")

except Exception as e:
    st.error(f"Error loading markets: {e}")
    st.exception(e)
