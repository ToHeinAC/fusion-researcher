"""Technologies analysis page."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Technologies - Fusion Research", page_icon="🔬", layout="wide")

st.title("🔬 Technologies")
st.markdown("Technology readiness analysis and comparison across fusion approaches.")

# Check if database exists
db_path = Path("research/fusion_research.db")
if not db_path.exists():
    st.warning("⚠️ Database not initialized.")
    st.stop()

try:
    from src.data.database import get_database
    from src.services.technology_service import TechnologyService
    
    db = get_database()
    tech_service = TechnologyService(db)
    
    # TRL Definitions
    with st.expander("📖 TRL Definitions", expanded=False):
        trl_levels = tech_service.get_trl_levels()
        for level in trl_levels:
            st.markdown(f"**TRL {level.level}: {level.name}**")
            st.markdown(f"*{level.description}*")
            st.markdown(f"Typical activities: {level.typical_activities}")
            st.markdown("---")
    
    # Technology Comparison
    st.markdown("### 📊 Technology Approach Comparison")
    
    tech_comparison = tech_service.get_technology_comparison()
    
    if tech_comparison:
        col1, col2 = st.columns(2)
        
        with col1:
            # Funding by technology
            fig = px.bar(
                x=[t["approach"] for t in tech_comparison],
                y=[t["total_funding"] / 1e9 for t in tech_comparison],
                labels={"x": "Technology", "y": "Total Funding (USD Billions)"},
                color=[t["total_funding"] for t in tech_comparison],
                color_continuous_scale="Viridis",
            )
            fig.update_layout(showlegend=False, title="Total Funding by Technology")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Average TRL by technology
            fig = px.bar(
                x=[t["approach"] for t in tech_comparison],
                y=[t["avg_trl"] for t in tech_comparison],
                labels={"x": "Technology", "y": "Average TRL"},
                color=[t["avg_trl"] for t in tech_comparison],
                color_continuous_scale="RdYlGn",
            )
            fig.update_layout(showlegend=False, title="Average TRL by Technology")
            st.plotly_chart(fig, use_container_width=True)
        
        # Comparison table
        st.markdown("### 📋 Technology Comparison Table")
        table_data = [
            {
                "Technology": t["approach"],
                "Companies": t["company_count"],
                "Avg TRL": t["avg_trl"],
                "Max TRL": t["max_trl"],
                "Total Funding": f"${t['total_funding'] / 1e9:.2f}B" if t["total_funding"] else "N/A",
                "Avg Funding": f"${t['avg_funding'] / 1e6:.1f}M" if t["avg_funding"] else "N/A",
            }
            for t in tech_comparison
        ]
        st.dataframe(table_data, use_container_width=True, hide_index=True)
    else:
        st.info("No technology comparison data available")
    
    st.markdown("---")
    
    # TRL Matrix
    st.markdown("### 🗺️ TRL Matrix")
    st.markdown("Companies mapped by Technology Readiness Level and technology approach.")
    
    trl_matrix = tech_service.get_trl_matrix()
    
    if trl_matrix:
        # Create heatmap-style visualization
        fig = px.scatter(
            x=[d["trl"] for d in trl_matrix],
            y=[d["technology"] for d in trl_matrix],
            size=[max(10, (d["funding"] or 0) / 1e7) for d in trl_matrix],
            color=[d["technology"] for d in trl_matrix],
            hover_name=[d["company"] for d in trl_matrix],
            hover_data={
                "TRL": [d["trl"] for d in trl_matrix],
                "Funding": [f"${d['funding']/1e6:.1f}M" if d["funding"] else "N/A" for d in trl_matrix],
                "Country": [d["country"] for d in trl_matrix],
            },
            labels={"x": "TRL", "y": "Technology"},
        )
        fig.update_layout(
            xaxis=dict(tickmode="linear", tick0=1, dtick=1, range=[0.5, 9.5]),
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # TRL Matrix Table
        with st.expander("📋 View as Table"):
            st.dataframe(
                [
                    {
                        "Company": d["company"],
                        "Technology": d["technology"],
                        "TRL": d["trl"],
                        "Funding": f"${d['funding']/1e6:.1f}M" if d["funding"] else "N/A",
                        "Country": d["country"],
                    }
                    for d in trl_matrix
                ],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No TRL matrix data available")
    
    st.markdown("---")
    
    # Companies Near Commercialization
    st.markdown("### 🚀 Companies Near Commercialization (TRL 6+)")
    
    near_commercial = tech_service.get_companies_near_commercialization(min_trl=6)
    
    if near_commercial:
        for company in near_commercial:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.markdown(f"**{company['name']}**")
            with col2:
                st.markdown(f"TRL {company['trl']}")
            with col3:
                st.markdown(company['technology'] or "N/A")
            with col4:
                funding = f"${company['funding']/1e6:.1f}M" if company['funding'] else "N/A"
                st.markdown(funding)
    else:
        st.info("No companies at TRL 6+ found")
    
    st.markdown("---")
    
    # Technology Timeline
    st.markdown("### 📅 Technology Development Timeline")
    
    timeline = tech_service.get_technology_timeline()
    
    if timeline:
        fig = px.line(
            x=[t["year"] for t in timeline],
            y=[t["count"] for t in timeline],
            color=[t["technology"] for t in timeline],
            labels={"x": "Year Founded", "y": "Companies", "color": "Technology"},
            markers=True,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available")

except Exception as e:
    st.error(f"Error loading technologies: {e}")
    st.exception(e)
