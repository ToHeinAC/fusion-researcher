"""Fusion Company Network visualization page using pyvis."""

import subprocess
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.set_page_config(page_title="Network - Fusion Research", page_icon="🔗", layout="wide")

st.title("Fusion Company Network")
st.markdown(
    "Visualize relationships between fusion companies, investors, research institutions, and partners."
)


def get_running_port() -> int:
    """Get the port this Streamlit app is running on."""
    import socket

    # Try common Streamlit ports
    for port in range(8511, 8520):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                result = s.connect_ex(("localhost", port))
                if result == 0:
                    return port
        except Exception:
            continue
    return 8511


# Safe exit button in sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("Exit App", type="secondary"):
        port = get_running_port()
        st.warning(f"Shutting down app on port {port}...")
        subprocess.run(
            f"lsof -ti:{port} | xargs -r kill -9",
            shell=True,
            capture_output=True,
        )
        st.stop()


try:
    from src.data.database import get_database
    from src.services.network_service import NetworkFilterCriteria, NetworkService

    # Initialize service with database
    db = get_database()
    network_service = NetworkService(db)

    # Load full network for filter options
    full_data = network_service.load_network()
    full_stats = network_service.get_network_stats(full_data)

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        # Node type filter
        all_node_types = network_service.get_node_types()
        selected_node_types = st.multiselect(
            "Node Types",
            options=all_node_types,
            default=all_node_types,
            help="Filter by entity type",
        )

        # Edge type filter
        all_edge_types = network_service.get_edge_types()
        selected_edge_types = st.multiselect(
            "Relationship Types",
            options=all_edge_types,
            default=all_edge_types,
            help="Filter by relationship type",
        )

        # Country filter
        all_countries = network_service.get_countries()
        selected_countries = st.multiselect(
            "Countries",
            options=all_countries,
            default=all_countries,
            help="Filter by country",
        )

        st.markdown("---")

        # Reset filters button
        if st.button("Reset Filters"):
            st.rerun()

    # Build filter criteria
    criteria = NetworkFilterCriteria(
        node_types=selected_node_types if selected_node_types else None,
        edge_types=selected_edge_types if selected_edge_types else None,
        countries=selected_countries if selected_countries else None,
    )

    # Apply filters
    filtered_data = network_service.filter_network(criteria)
    filtered_stats = network_service.get_network_stats(filtered_data)

    # Key metrics
    st.markdown("### Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Nodes", filtered_stats.total_nodes, delta=f"of {full_stats.total_nodes}")
    with col2:
        st.metric("Edges", filtered_stats.total_edges, delta=f"of {full_stats.total_edges}")
    with col3:
        st.metric("Node Types", len(filtered_stats.node_type_counts))
    with col4:
        st.metric("Countries", len(filtered_stats.country_counts))

    st.markdown("---")

    # Network visualization
    st.markdown("### Network Graph")
    st.caption("Hover over nodes for details. Drag to rearrange. Scroll to zoom.")

    if filtered_data.nodes:
        # Generate network HTML
        network_html = network_service.get_network_html(filtered_data, height="700px")

        # Display using streamlit components
        components.html(network_html, height=720, scrolling=False)
    else:
        st.info("No nodes to display. Try adjusting the filters.")

    st.markdown("---")

    # Node type legend
    st.markdown("### Node Type Legend")
    legend_cols = st.columns(5)

    node_type_labels = {
        "company": "Fusion Company",
        "investor": "Investor",
        "research_partner": "Research Partner",
        "industrial_partner": "Industrial Partner",
        "government": "Government",
    }

    for i, node_type in enumerate(sorted(filtered_stats.node_type_counts.keys())):
        col_idx = i % 5
        color = network_service.get_node_color(node_type)
        label = node_type_labels.get(node_type, node_type.replace("_", " ").title())
        count = filtered_stats.node_type_counts[node_type]

        with legend_cols[col_idx]:
            st.markdown(
                f'<span style="background-color: {color}; color: white; '
                f'padding: 4px 8px; border-radius: 4px; font-size: 0.85em; display: inline-block;">'
                f"{label} ({count})</span>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Node details expander
    with st.expander("Node Details Table"):
        if filtered_data.nodes:
            table_data = [
                {
                    "Name": node.label,
                    "Type": node.type.replace("_", " ").title(),
                    "Country": node.country,
                    "Technology": node.attributes.get("technology", "-"),
                    "Funding (USD M)": node.attributes.get("funding_usd_m") or "-",
                }
                for node in sorted(filtered_data.nodes, key=lambda n: (n.type, n.label))
            ]
            st.dataframe(table_data, use_container_width=True, hide_index=True)

            # Edit link for company nodes
            company_nodes = [n for n in filtered_data.nodes if n.type == "company"]
            if company_nodes:
                st.markdown("**Quick Edit:**")
                edit_options = {n.label: n.id for n in company_nodes}
                chosen = st.selectbox("Select company to edit", list(edit_options.keys()), key="net_edit_company")
                if st.button("Edit in Editor", key="net_edit_btn"):
                    node_id = edit_options[chosen]
                    # Extract numeric ID from "company_123"
                    numeric_id = int(node_id.replace("company_", ""))
                    st.session_state.editor_mode = "edit"
                    st.session_state.editor_edit_id = numeric_id
                    st.switch_page("pages/10_✏️_Editor.py")

    # Edge details expander
    with st.expander("Relationship Details Table"):
        if filtered_data.edges:
            edge_table_data = []
            for edge in sorted(filtered_data.edges, key=lambda e: (e.type, e.source)):
                source_node = network_service.get_node_by_id(edge.source)
                target_node = network_service.get_node_by_id(edge.target)
                edge_table_data.append(
                    {
                        "Source": source_node.label if source_node else edge.source,
                        "Target": target_node.label if target_node else edge.target,
                        "Relationship": edge.type.replace("_", " ").title(),
                    }
                )
            st.dataframe(edge_table_data, use_container_width=True, hide_index=True)

    # Metadata
    if filtered_data.metadata:
        st.markdown("---")
        st.caption(
            f"Source: {filtered_data.metadata.get('source', 'Unknown')} | "
            f"Description: {filtered_data.metadata.get('description', 'Unknown')}"
        )

except Exception as e:
    st.error(f"Error loading network: {e}")
    st.exception(e)
