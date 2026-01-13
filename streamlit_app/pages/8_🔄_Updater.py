"""LLM-powered database updater page."""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Updater - Fusion Research", page_icon="🔄", layout="wide")

st.title("🔄 Database Updater")
st.markdown("LLM-powered automatic data updates with confidence scoring and human review.")

try:
    from src.services.updater_service import (
        get_updater_service,
        UpdaterService,
        UpdaterConfig,
    )
    from src.models.update_proposal import (
        EntityType,
        ProposalStatus,
        UPDATEABLE_FIELDS,
    )
    from src.llm.chain_factory import get_llm
    from src.config import get_settings

    # Get settings from session state, fallback to config/.env
    settings = get_settings()
    ollama_model = st.session_state.get("llm_model", settings.llm_model)
    ollama_url = st.session_state.get("ollama_base_url", settings.ollama_base_url)
    tavily_api_key = st.session_state.get("tavily_api_key", "") or (settings.tavily_api_key or "")

    # Initialize config from session state or defaults
    if "updater_config" not in st.session_state:
        st.session_state.updater_config = UpdaterConfig()

    config = st.session_state.updater_config

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Run Updates",
        "📋 Review Proposals",
        "📜 Audit Log",
        "⚙️ Settings",
    ])

    with tab1:
        st.markdown("### 🔍 Run Updates")
        st.markdown("Search the web for updated company information and create proposals.")

        if not tavily_api_key:
            st.warning("⚠️ Tavily API key not configured. Go to Settings page to add your API key.")
            st.stop()

        # Initialize service
        try:
            llm = get_llm(model=ollama_model, base_url=ollama_url)
        except Exception as e:
            st.warning(f"LLM not available: {e}. Updates will be limited.")
            llm = None

        updater = get_updater_service(
            llm=llm,
            tavily_api_key=tavily_api_key,
            config=config,
        )

        # Company selection
        col1, col2 = st.columns(2)

        with col1:
            company_mode = st.radio(
                "Select companies:",
                ["Stale companies", "All companies", "Specific company"],
                key="company_mode",
            )

        with col2:
            batch_size = st.slider(
                "Batch size:",
                min_value=1,
                max_value=20,
                value=5,
                key="batch_size",
            )

        # Get companies based on selection
        if company_mode == "Stale companies":
            companies = updater.get_stale_companies(limit=batch_size)
            st.info(f"Found {len(companies)} companies not updated in {config.staleness_days}+ days")
        elif company_mode == "All companies":
            companies = updater.get_all_companies(limit=batch_size)
        else:
            all_companies = updater.get_all_companies(limit=100)
            company_names = {c["name"]: c["id"] for c in all_companies}
            selected = st.selectbox(
                "Select company:",
                options=list(company_names.keys()),
                key="selected_company",
            )
            if selected:
                companies = [{"id": company_names[selected], "name": selected}]
            else:
                companies = []

        # Display selected companies
        if companies:
            st.markdown("**Selected companies:**")
            for c in companies[:10]:
                funding = c.get("total_funding_usd")
                funding_str = f"${funding/1e6:.0f}M" if funding else "N/A"
                st.markdown(f"- {c['name']} (TRL: {c.get('trl', 'N/A')}, Funding: {funding_str})")
            if len(companies) > 10:
                st.caption(f"... and {len(companies) - 10} more")

        # Field selection
        st.markdown("---")
        st.markdown("**Fields to update:**")

        company_fields = UPDATEABLE_FIELDS.get(EntityType.COMPANY, {})
        field_options = list(company_fields.keys())
        default_fields = ["total_funding_usd", "team_size", "trl"]
        default_selection = [f for f in default_fields if f in field_options]

        selected_fields = st.multiselect(
            "Select fields:",
            options=field_options,
            default=default_selection,
            key="selected_fields",
        )

        # Show field descriptions
        if selected_fields:
            for field in selected_fields:
                desc = company_fields[field].get("description", field)
                st.caption(f"• {field}: {desc}")

        # Auto-apply option
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            auto_apply = st.checkbox(
                f"Auto-apply high confidence (≥{config.auto_apply_threshold:.0%})",
                value=False,
                key="auto_apply",
            )

        with col2:
            st.caption(f"Using model: {ollama_model}")

        # Run updates button
        if st.button("🚀 Run Updates", type="primary", disabled=not companies or not selected_fields):
            company_ids = [c["id"] for c in companies]

            with st.status("Running updates...", expanded=True) as status:
                st.write(f"Processing {len(company_ids)} companies...")

                result = updater.run_update_cycle(
                    company_ids=company_ids,
                    fields=selected_fields,
                    auto_apply=auto_apply,
                )

                st.write(f"✅ Companies processed: {result.companies_processed}")
                st.write(f"📝 Proposals created: {result.proposals_created}")
                if auto_apply:
                    st.write(f"🔄 Auto-applied: {result.proposals_auto_applied}")

                if result.errors:
                    st.write("⚠️ Errors:")
                    for error in result.errors:
                        st.write(f"  - {error}")

                status.update(
                    label=f"Complete! {result.proposals_created} proposals created",
                    state="complete",
                )

            st.success(f"Created {result.proposals_created} proposals. Review them in the Review tab.")

    with tab2:
        st.markdown("### 📋 Review Proposals")
        st.markdown("Review and approve/reject proposed updates.")

        # Refresh service
        updater = get_updater_service(
            llm=None,
            tavily_api_key=tavily_api_key,
            config=config,
        )

        # Get pending proposals
        proposals = updater.get_pending_proposals(limit=50)

        if not proposals:
            st.info("No pending proposals. Run an update to create proposals.")
        else:
            st.markdown(f"**{len(proposals)} pending proposals**")

            # Bulk actions
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ Approve All High Confidence", key="approve_all_high"):
                    approved = updater.auto_apply_high_confidence(threshold=config.auto_apply_threshold)
                    st.success(f"Approved {approved} proposals")
                    st.rerun()

            with col2:
                if st.button("🔄 Refresh", key="refresh_proposals"):
                    st.rerun()

            st.markdown("---")

            # Display proposals
            for proposal in proposals:
                # Get company name
                cursor = updater.db.execute(
                    "SELECT name FROM companies WHERE id = ?",
                    (proposal.entity_id,),
                )
                row = cursor.fetchone()
                company_name = row["name"] if row else f"ID: {proposal.entity_id}"

                # Confidence color
                if proposal.confidence_score >= 0.85:
                    conf_color = "🟢"
                elif proposal.confidence_score >= 0.70:
                    conf_color = "🟡"
                else:
                    conf_color = "🔴"

                with st.expander(
                    f"{conf_color} {company_name} - {proposal.field_name} "
                    f"({proposal.confidence_score:.0%})",
                    expanded=False,
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Current Value:**")
                        st.code(proposal.old_value or "N/A")

                    with col2:
                        st.markdown("**Proposed Value:**")
                        st.code(proposal.new_value or "N/A")

                    st.markdown(f"**Confidence:** {proposal.confidence_score:.1%}")
                    st.markdown(f"**Search Query:** {proposal.search_query}")

                    # Sources
                    if proposal.sources:
                        st.markdown("**Sources:**")
                        for source in proposal.sources[:5]:
                            st.markdown(
                                f"- [{source.title}]({source.url}) "
                                f"({source.reliability.label}: {source.reliability.score:.0%})"
                            )
                            if source.snippet:
                                st.caption(source.snippet[:200] + "...")

                    # Action buttons
                    col1, col2, col3 = st.columns([1, 1, 2])

                    with col1:
                        if st.button("✅ Approve", key=f"approve_{proposal.id}"):
                            if updater.approve_proposal(proposal.id, reviewed_by="user"):
                                st.success("Approved!")
                                st.rerun()
                            else:
                                st.error("Failed to approve")

                    with col2:
                        if st.button("❌ Reject", key=f"reject_{proposal.id}"):
                            if updater.reject_proposal(proposal.id, reviewed_by="user"):
                                st.success("Rejected")
                                st.rerun()
                            else:
                                st.error("Failed to reject")

    with tab3:
        st.markdown("### 📜 Audit Log")
        st.markdown("View history of all data changes.")

        # Refresh service
        updater = get_updater_service(
            llm=None,
            tavily_api_key=tavily_api_key,
            config=config,
        )

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            entity_filter = st.selectbox(
                "Entity type:",
                options=["All"] + [e.value for e in EntityType],
                key="audit_entity_filter",
            )

        with col2:
            limit = st.slider("Entries to show:", 10, 200, 50, key="audit_limit")

        # Get audit log
        entity_type = None
        if entity_filter != "All":
            entity_type = EntityType(entity_filter)

        entries = updater.get_audit_log(entity_type=entity_type, limit=limit)

        if not entries:
            st.info("No audit log entries found.")
        else:
            st.markdown(f"**{len(entries)} entries**")

            for entry in entries:
                with st.expander(
                    f"{entry.changed_at.strftime('%Y-%m-%d %H:%M')} - "
                    f"{entry.entity_type.value} #{entry.entity_id} - {entry.field_name}",
                    expanded=False,
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Before:**")
                        st.code(entry.old_value or "N/A")

                    with col2:
                        st.markdown("**After:**")
                        st.code(entry.new_value or "N/A")

                    st.markdown(f"**Source:** {entry.change_source.value}")
                    st.markdown(f"**Changed by:** {entry.changed_by}")

                    if entry.proposal_id:
                        st.markdown(f"**Proposal ID:** {entry.proposal_id}")

    with tab4:
        st.markdown("### ⚙️ Updater Settings")
        st.markdown("Configure the automatic update behavior.")

        # Auto-apply threshold
        new_threshold = st.slider(
            "Auto-apply confidence threshold:",
            min_value=0.5,
            max_value=1.0,
            value=config.auto_apply_threshold,
            step=0.05,
            help="Proposals with confidence above this threshold can be auto-applied.",
            key="config_threshold",
        )

        # Staleness days
        new_staleness = st.slider(
            "Staleness threshold (days):",
            min_value=7,
            max_value=90,
            value=config.staleness_days,
            help="Companies not updated for this many days are considered stale.",
            key="config_staleness",
        )

        # Max sources
        new_max_sources = st.slider(
            "Max sources per field:",
            min_value=3,
            max_value=10,
            value=config.max_sources_per_field,
            help="Maximum number of web sources to fetch per field.",
            key="config_sources",
        )

        # Save settings
        if st.button("💾 Save Settings", type="primary", key="save_config"):
            st.session_state.updater_config = UpdaterConfig(
                auto_apply_threshold=new_threshold,
                staleness_days=new_staleness,
                max_sources_per_field=new_max_sources,
            )
            st.success("Settings saved!")

        # API key status
        st.markdown("---")
        st.markdown("**API Status:**")

        if tavily_api_key:
            st.success("✅ Tavily API key configured")
        else:
            st.warning("⚠️ Tavily API key not set. Configure in Settings page.")

        st.info(f"LLM Model: {ollama_model} ({ollama_url})")

except Exception as e:
    st.error(f"Error loading updater page: {e}")
    st.exception(e)


# Safe exit button (per user preference)
st.sidebar.markdown("---")
if st.sidebar.button("🛑 Safe Exit"):
    import subprocess
    port = 8511
    subprocess.run(f"lsof -ti:{port} | xargs -r kill -9", shell=True)
