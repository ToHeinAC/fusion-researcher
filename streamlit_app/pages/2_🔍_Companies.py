"""Companies search and browse page."""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Companies - Fusion Research", page_icon="🔍", layout="wide")

# Technology color mapping - unique colors for each technology
TECH_COLORS = {
    "tokamak": {"bg": "#E3F2FD", "border": "#1976D2", "text": "#0D47A1"},
    "stellarator": {"bg": "#F3E5F5", "border": "#7B1FA2", "text": "#4A148C"},
    "laser_icf": {"bg": "#FFF3E0", "border": "#F57C00", "text": "#E65100"},
    "frc": {"bg": "#E8F5E9", "border": "#388E3C", "text": "#1B5E20"},
    "magnetized_target": {"bg": "#FCE4EC", "border": "#C2185B", "text": "#880E4F"},
    "z_pinch": {"bg": "#FFF8E1", "border": "#FFA000", "text": "#FF6F00"},
    "mirror": {"bg": "#E0F7FA", "border": "#0097A7", "text": "#006064"},
    "other": {"bg": "#ECEFF1", "border": "#546E7A", "text": "#263238"},
    None: {"bg": "#F5F5F5", "border": "#9E9E9E", "text": "#424242"},
}

def get_tech_color(tech_approach: str) -> dict:
    """Get color scheme for a technology approach."""
    if tech_approach is None:
        return TECH_COLORS[None]
    tech_key = tech_approach.lower().replace(" ", "_").replace("-", "_")
    return TECH_COLORS.get(tech_key, TECH_COLORS["other"])

st.title("🔍 Companies")
st.markdown("Search and browse fusion companies worldwide.")

# Check if database exists
db_path = Path("research/fusion_research.db")
if not db_path.exists():
    st.warning("Database not initialized.")
    st.stop()

try:
    from src.data.database import get_database
    from src.services.company_service import CompanyService, CompanySearchCriteria

    db = get_database()
    company_service = CompanyService(db)

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        countries = ["All"] + company_service.get_countries()
        selected_country = st.selectbox("Country", countries)

        technologies = ["All"] + company_service.get_technologies()
        selected_tech = st.selectbox("Technology", technologies)

        st.markdown("**TRL Range**")
        trl_min, trl_max = st.slider("TRL", 1, 9, (1, 9))

        st.markdown("**Funding (USD Million)**")
        funding_min = st.number_input("Min Funding", min_value=0, value=0)
        funding_max = st.number_input("Max Funding", min_value=0, value=10000)

        company_types = ["All", "Startup", "KMU", "Konzern", "Forschung"]
        selected_type = st.selectbox("Company Type", company_types)

        apply_filters = st.button("Apply Filters", type="primary")

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

    companies = company_service.search_companies(criteria)

    # Check if viewing details
    if "selected_company_id" in st.session_state:
        # DETAIL VIEW
        company = company_service.get_company(st.session_state.selected_company_id)
        if company:
            colors = get_tech_color(company.technology_approach)

            # Back / Edit buttons at top
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("← Back to List"):
                    del st.session_state.selected_company_id
                    st.rerun()
            with btn_col2:
                if st.button("✏️ Edit in Editor"):
                    st.session_state.editor_mode = "edit"
                    st.session_state.editor_edit_id = company.id
                    st.switch_page("pages/10_✏️_Editor.py")

            # Header
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, {colors['bg']} 0%, white 100%);
                    border-left: 6px solid {colors['border']};
                    padding: 1.5rem;
                    margin: 1rem 0;
                    border-radius: 0 12px 12px 0;
                ">
                    <h1 style="margin: 0; color: {colors['text']};">{company.name}</h1>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1em;">
                        <span style="background-color: {colors['border']}; color: white;
                            padding: 4px 12px; border-radius: 4px;">
                            {company.technology_approach or 'Unknown Technology'}
                        </span>
                        <span style="margin-left: 1rem; color: #666;">
                            {company.country} | {company.company_type.value}
                        </span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Funding", company.funding_display)
            with col2:
                st.metric("TRL", company.trl or "N/A")
            with col3:
                st.metric("Team Size", company.team_size or "N/A")
            with col4:
                st.metric("Founded", company.founded_year or "N/A")

            st.markdown("---")

            # Description (prominent if available)
            if company.description:
                st.markdown("### About")
                st.markdown(company.description)
                st.markdown("")

            # Two columns for details
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Company Details")
                details = [
                    ("Type", company.company_type.value),
                    ("Country", company.country),
                    ("City", company.city),
                    ("Founded", company.founded_year),
                    ("Team Size", f"{company.team_size} employees" if company.team_size else None),
                    ("Website", company.website),
                ]
                for label, value in details:
                    if value:
                        st.markdown(f"**{label}:** {value}")

            with col2:
                st.markdown("### Technology & Funding")
                st.markdown(f"**Approach:** {company.technology_approach or 'N/A'}")
                if company.trl:
                    st.markdown(f"**{company.trl_display}**")
                if company.trl_justification:
                    st.info(company.trl_justification)
                st.markdown(f"**Total Funding:** {company.funding_display}")

            # Key investors (if available)
            if company.key_investors:
                st.markdown("### Key Investors")
                # Clean up markdown formatting artifacts
                investors = company.key_investors.replace("**", "").strip()
                st.markdown(investors)

            # Key partnerships (if available)
            if company.key_partnerships:
                st.markdown("### Key Partnerships")
                st.markdown(company.key_partnerships)

            # Competitive positioning (if available)
            if company.competitive_positioning:
                st.markdown("### Competitive Positioning")
                st.markdown(company.competitive_positioning)

            # Funding history from linked table
            st.markdown("### Funding History")
            funding_history = company_service.get_company_funding_history(company.id)
            if funding_history:
                for f in funding_history:
                    st.markdown(f"- **{f.stage.value}** ({f.date or 'N/A'}): {f.amount_display} - {f.lead_investor or 'N/A'}")
            else:
                st.caption("No detailed funding rounds available. Total funding shown above.")

            # Data quality indicator
            st.markdown("---")
            st.caption(f"Data confidence: {company.confidence_score:.0%} | Last updated: {company.last_updated or 'Unknown'}")

    else:
        # LIST VIEW
        st.markdown(f"### Results ({len(companies)} companies)")

        # Technology legend
        st.markdown("**Technology Legend** (hover for details):")
        legend_cols = st.columns(8)
        tech_legend = {
            "tokamak": {"name": "Tokamak", "hint": "Magnetic confinement"},
            "stellarator": {"name": "Stellarator", "hint": "Twisted magnetic confinement"},
            "laser_icf": {"name": "Laser ICF", "hint": "Inertial Confinement Fusion"},
            "frc": {"name": "FRC", "hint": "Field-Reversed Configuration"},
            "magnetized_target": {"name": "Mag. Target", "hint": "Magnetized Target Fusion"},
            "z_pinch": {"name": "Z-Pinch", "hint": "Z-Pinch plasma compression"},
            "mirror": {"name": "Mirror", "hint": "Magnetic mirror confinement"},
            "other": {"name": "Other", "hint": "Other technologies"},
        }
        for i, (tech_key, tech_info) in enumerate(tech_legend.items()):
            colors = TECH_COLORS.get(tech_key, TECH_COLORS["other"])
            with legend_cols[i]:
                st.markdown(
                    f'<span title="{tech_info["hint"]}" style="background-color: {colors["bg"]}; '
                    f'border: 2px solid {colors["border"]}; color: {colors["text"]}; '
                    f'padding: 2px 8px; border-radius: 4px; font-size: 0.8em; cursor: help;">'
                    f'{tech_info["name"]}</span>',
                    unsafe_allow_html=True
                )

        st.markdown("---")

        if companies:
            # Compact card grid
            cols = st.columns(3)
            for i, company in enumerate(companies):
                colors = get_tech_color(company.technology_approach)

                # Check if company has additional details worth showing
                full_company = company_service.get_company(company.id)
                has_description = bool(full_company and full_company.description)
                has_investors = bool(full_company and full_company.key_investors)
                has_extra = has_description or has_investors

                with cols[i % 3]:
                    # Compact card - just key info
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {colors['bg']};
                            border: 3px solid {colors['border']};
                            border-radius: 12px;
                            padding: 0.8rem;
                            margin-bottom: 0.5rem;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <h4 style="margin: 0; color: {colors['text']}; font-size: 1.1em;">{company.name}</h4>
                            <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                                <span style="background-color: {colors['border']}; color: white;
                                    padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                                    {company.technology_approach or 'Unknown'}
                                </span>
                                <span style="color: #555; font-size: 0.9em;">{company.country}</span>
                            </div>
                            <div style="margin-top: 0.5rem; color: #333;">
                                <strong style="font-size: 1.1em;">{company.funding_display}</strong>
                                <span style="color: #666; margin-left: 0.5rem;">
                                    TRL: {company.trl or '-'} | Team: {company.team_size or '-'}
                                </span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Show button with indicator if there's more info
                    btn_label = "View Details" if not has_extra else "View Details +"
                    if st.button(btn_label, key=f"view_{company.id}",
                                help="Click to see full profile" + (" - has description/investors" if has_extra else "")):
                        st.session_state.selected_company_id = company.id
                        st.rerun()
        else:
            st.info("No companies found matching your criteria. Try adjusting the filters.")

except Exception as e:
    st.error(f"Error loading companies: {e}")
    st.exception(e)
