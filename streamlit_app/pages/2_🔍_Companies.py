"""Companies search and browse page."""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Companies - Fusion Research", page_icon="🔍", layout="wide")

st.title("🔍 Companies")
st.markdown("Search and browse fusion companies worldwide.")

# Check if database exists
db_path = Path("research/fusion_research.db")
if not db_path.exists():
    st.warning("⚠️ Database not initialized.")
    st.stop()

try:
    from src.data.database import get_database
    from src.services.company_service import CompanyService, CompanySearchCriteria
    
    db = get_database()
    company_service = CompanyService(db)
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔧 Filters")
        
        # Country filter
        countries = ["All"] + company_service.get_countries()
        selected_country = st.selectbox("Country", countries)
        
        # Technology filter
        technologies = ["All"] + company_service.get_technologies()
        selected_tech = st.selectbox("Technology", technologies)
        
        # TRL range
        st.markdown("**TRL Range**")
        trl_min, trl_max = st.slider("TRL", 1, 9, (1, 9))
        
        # Funding range
        st.markdown("**Funding (USD Million)**")
        funding_min = st.number_input("Min Funding", min_value=0, value=0)
        funding_max = st.number_input("Max Funding", min_value=0, value=10000)
        
        # Company type
        company_types = ["All", "Startup", "KMU", "Konzern", "Forschung"]
        selected_type = st.selectbox("Company Type", company_types)
        
        # Apply filters button
        apply_filters = st.button("🔍 Apply Filters", type="primary")
    
    # Build search criteria
    criteria = CompanySearchCriteria(
        country=selected_country if selected_country != "All" else None,
        technology=selected_tech if selected_tech != "All" else None,
        trl_min=trl_min,
        trl_max=trl_max,
        funding_min=funding_min * 1_000_000 if funding_min > 0 else None,
        funding_max=funding_max * 1_000_000 if funding_max < 10000 else None,
        company_type=selected_type if selected_type != "All" else None,
        limit=100,
    )
    
    # Search results
    companies = company_service.search_companies(criteria)
    
    st.markdown(f"### 📋 Results ({len(companies)} companies)")
    
    if companies:
        # Display as cards
        cols = st.columns(3)
        for i, company in enumerate(companies):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <h4 style="margin: 0;">{company.name}</h4>
                        <p style="color: #666; margin: 0.5rem 0;">📍 {company.country}</p>
                        <p style="margin: 0.25rem 0;"><strong>Technology:</strong> {company.technology_approach or 'N/A'}</p>
                        <p style="margin: 0.25rem 0;"><strong>TRL:</strong> {company.trl or 'N/A'}</p>
                        <p style="margin: 0.25rem 0;"><strong>Funding:</strong> {company.funding_display}</p>
                        <p style="margin: 0.25rem 0;"><strong>Team:</strong> {company.team_size or 'N/A'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"View Details", key=f"view_{company.id}"):
                        st.session_state.selected_company_id = company.id
        
        # Company detail view
        if "selected_company_id" in st.session_state:
            st.markdown("---")
            st.markdown("### 📄 Company Details")
            
            company = company_service.get_company(st.session_state.selected_company_id)
            if company:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"## {company.name}")
                    st.markdown(f"**Type:** {company.company_type.value}")
                    st.markdown(f"**Country:** {company.country}")
                    st.markdown(f"**City:** {company.city or 'N/A'}")
                    st.markdown(f"**Founded:** {company.founded_year or 'N/A'}")
                    st.markdown(f"**Team Size:** {company.team_size or 'N/A'}")
                    st.markdown(f"**Website:** {company.website or 'N/A'}")
                
                with col2:
                    st.markdown("### Technology")
                    st.markdown(f"**Approach:** {company.technology_approach or 'N/A'}")
                    st.markdown(f"**{company.trl_display}**")
                    if company.trl_justification:
                        st.markdown(f"*{company.trl_justification}*")
                    
                    st.markdown("### Funding")
                    st.markdown(f"**Total:** {company.funding_display}")
                    if company.key_investors:
                        st.markdown(f"**Key Investors:** {company.key_investors}")
                
                if company.description:
                    st.markdown("### Description")
                    st.markdown(company.description)
                
                if company.key_partnerships:
                    st.markdown("### Key Partnerships")
                    st.markdown(company.key_partnerships)
                
                if company.competitive_positioning:
                    st.markdown("### Competitive Positioning")
                    st.markdown(company.competitive_positioning)
                
                # Funding history
                st.markdown("### Funding History")
                funding_history = company_service.get_company_funding_history(company.id)
                if funding_history:
                    for f in funding_history:
                        st.markdown(f"- **{f.stage.value}** ({f.date or 'N/A'}): {f.amount_display} - {f.lead_investor or 'N/A'}")
                else:
                    st.info("No detailed funding history available")
                
                # Clear selection button
                if st.button("← Back to List"):
                    del st.session_state.selected_company_id
                    st.rerun()
    else:
        st.info("No companies found matching your criteria. Try adjusting the filters.")

except Exception as e:
    st.error(f"Error loading companies: {e}")
    st.exception(e)
