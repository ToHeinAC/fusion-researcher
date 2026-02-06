"""Network visualization service using database and pyvis."""

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
import pandas as pd
from pyvis.network import Network

from src.data.database import Database, get_database


@dataclass
class NetworkNode:
    """Represents a node in the network."""

    id: str
    label: str
    type: str
    country: str
    attributes: dict = field(default_factory=dict)


@dataclass
class NetworkEdge:
    """Represents an edge in the network."""

    source: str
    target: str
    type: str
    attributes: dict = field(default_factory=dict)


@dataclass
class NetworkData:
    """Container for network data."""

    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    metadata: dict = field(default_factory=dict)


@dataclass
class NetworkFilterCriteria:
    """Criteria for filtering network data."""

    node_types: list[str] | None = None
    edge_types: list[str] | None = None
    countries: list[str] | None = None


@dataclass
class NetworkStats:
    """Network statistics."""

    total_nodes: int
    total_edges: int
    node_type_counts: dict[str, int]
    edge_type_counts: dict[str, int]
    country_counts: dict[str, int]


class NetworkService:
    """Service for building and visualizing network from database."""

    # Node type colors
    NODE_COLORS = {
        "company": "#E53935",  # Red
        "investor": "#8E24AA",  # Purple
        "research_partner": "#43A047",  # Green
        "industrial_partner": "#1E88E5",  # Blue
        "government": "#00897B",  # Teal
    }

    # Edge type colors
    EDGE_COLORS = {
        "investor": "#8E24AA",  # Purple
        "technology_partner": "#1E88E5",  # Blue
        "academic_partner": "#43A047",  # Green
        "strategic_partner": "#FB8C00",  # Orange
    }

    DEFAULT_NODE_COLOR = "#9E9E9E"  # Grey
    DEFAULT_EDGE_COLOR = "#BDBDBD"  # Light Grey

    def __init__(self, db: Database | None = None):
        """Initialize the service with database connection."""
        self._db = db or get_database()
        self._network_data: NetworkData | None = None

    def _parse_text_list(self, text: str | None) -> list[str]:
        """Parse comma/semicolon separated text into list of names."""
        if not text:
            return []

        # Split on comma or semicolon
        items = re.split(r"[,;]", text)

        result = []
        for item in items:
            # Clean up the item
            item = item.strip()
            # Remove trailing citations like [16]
            item = re.sub(r"\[\d+\]$", "", item).strip()
            # Remove parenthetical notes like (Berlin), (London)
            item = re.sub(r"\s*\([^)]+\)\s*$", "", item).strip()

            if item and len(item) > 1:
                result.append(item)

        return result

    def _classify_partner(self, partner_name: str) -> str:
        """Classify partner type based on name patterns."""
        name_lower = partner_name.lower()

        # Research/academic indicators
        academic_keywords = [
            "university",
            "universität",
            "college",
            "institute",
            "institut",
            "lab",
            "laboratory",
            "research",
            "national",
            "department of energy",
            "doe",
            "cnrs",
            "max planck",
            "fraunhofer",
            "lmu",
            "mit",
            "princeton",
            "oxford",
            "cambridge",
            "stanford",
            "berkeley",
            "caltech",
        ]

        # Government indicators
        government_keywords = [
            "government",
            "ministry",
            "department",
            "agency",
            "commission",
            "u.s.",
            "us ",
            "european",
            "federal",
            "state of",
            "dod",
            "arpa",
            "darpa",
        ]

        for kw in academic_keywords:
            if kw in name_lower:
                return "research_partner"

        for kw in government_keywords:
            if kw in name_lower:
                return "government"

        return "industrial_partner"

    def load_network_from_db(self) -> NetworkData:
        """Load network data from database."""
        if self._network_data is not None:
            return self._network_data

        nodes: dict[str, NetworkNode] = {}
        edges: list[NetworkEdge] = []

        # Load companies as nodes
        cursor = self._db.execute(
            """
            SELECT id, name, country, technology_approach, total_funding_usd,
                   key_investors, key_partnerships
            FROM companies
            """
        )

        for row in cursor.fetchall():
            company_name = row["name"]
            company_id = f"company_{row['id']}"

            # Add company node
            nodes[company_id] = NetworkNode(
                id=company_id,
                label=company_name,
                type="company",
                country=row["country"] or "Unknown",
                attributes={
                    "technology": row["technology_approach"],
                    "funding_usd_m": (
                        round(row["total_funding_usd"] / 1_000_000, 1)
                        if row["total_funding_usd"]
                        else None
                    ),
                },
            )

            # Parse and add investors
            investors = self._parse_text_list(row["key_investors"])
            for investor_name in investors:
                investor_id = f"investor_{investor_name.lower().replace(' ', '_')}"

                if investor_id not in nodes:
                    nodes[investor_id] = NetworkNode(
                        id=investor_id,
                        label=investor_name,
                        type="investor",
                        country="Unknown",
                    )

                edges.append(
                    NetworkEdge(
                        source=investor_id,
                        target=company_id,
                        type="investor",
                    )
                )

            # Parse and add partners
            partners = self._parse_text_list(row["key_partnerships"])
            for partner_name in partners:
                partner_type = self._classify_partner(partner_name)
                partner_id = f"partner_{partner_name.lower().replace(' ', '_')}"

                if partner_id not in nodes:
                    nodes[partner_id] = NetworkNode(
                        id=partner_id,
                        label=partner_name,
                        type=partner_type,
                        country="Unknown",
                    )

                edge_type = (
                    "academic_partner"
                    if partner_type == "research_partner"
                    else "strategic_partner"
                )
                edges.append(
                    NetworkEdge(
                        source=company_id,
                        target=partner_id,
                        type=edge_type,
                    )
                )

        self._network_data = NetworkData(
            nodes=list(nodes.values()),
            edges=edges,
            metadata={
                "source": "fusion_research.db",
                "description": "Fusion company investor and partner network",
            },
        )

        return self._network_data

    def load_network(self) -> NetworkData:
        """Alias for load_network_from_db for backwards compatibility."""
        return self.load_network_from_db()

    def build_nodes_dataframe(self, data: NetworkData | None = None) -> pd.DataFrame:
        """Build pandas DataFrame for nodes."""
        if data is None:
            data = self.load_network()

        records = []
        for node in data.nodes:
            records.append(
                {
                    "id": node.id,
                    "name": node.label,
                    "type": node.type,
                    "color": self.get_node_color(node.type),
                    "country": node.country,
                    "technology": node.attributes.get("technology"),
                    "funding_usd_m": node.attributes.get("funding_usd_m"),
                }
            )

        return pd.DataFrame(records)

    def build_edges_dataframe(self, data: NetworkData | None = None) -> pd.DataFrame:
        """Build pandas DataFrame for edges."""
        if data is None:
            data = self.load_network()

        records = []
        for edge in data.edges:
            records.append(
                {
                    "from": edge.source,
                    "to": edge.target,
                    "type": edge.type,
                    "weight": 1,
                    "color": self.get_edge_color(edge.type),
                    "message": f"{edge.type.replace('_', ' ').title()}",
                }
            )

        return pd.DataFrame(records)

    def create_pyvis_network(
        self,
        df_edges: pd.DataFrame | None = None,
        df_nodes: pd.DataFrame | None = None,
        height: str = "800px",
        show_buttons: bool = False,
    ) -> Network:
        """Create pyvis Network object for visualization."""
        data = self.load_network()

        if df_nodes is None:
            df_nodes = self.build_nodes_dataframe(data)
        if df_edges is None:
            df_edges = self.build_edges_dataframe(data)

        # Create pyvis network
        net = Network(
            height=height,
            width="100%",
            bgcolor="white",
            font_color="black",
            directed=True,
            notebook=False,
            neighborhood_highlight=True,
            cdn_resources="remote",
        )

        # Use networkx for degree calculation (for node sizing)
        if not df_edges.empty:
            G = nx.from_pandas_edgelist(
                df_edges, "from", "to", ["weight", "message", "color"]
            )
            degrees = dict(G.degree())
        else:
            degrees = {}

        # Build node id to index mapping
        node_ids = df_nodes["id"].tolist()

        # Add nodes with size based on degree
        for _, row in df_nodes.iterrows():
            node_id = row["id"]
            degree = degrees.get(node_id, 1)
            # Base size + degree multiplier
            size = 10 + degree * 3

            # Build title/hover text
            title_parts = [f"<b>{row['name']}</b>"]
            title_parts.append(f"Type: {row['type'].replace('_', ' ').title()}")
            title_parts.append(f"Country: {row['country']}")
            if row.get("technology"):
                title_parts.append(f"Technology: {row['technology']}")
            if row.get("funding_usd_m"):
                title_parts.append(f"Funding: ${row['funding_usd_m']}M")
            title_parts.append(f"Connections: {degree}")

            net.add_node(
                node_id,
                label=row["name"],
                color=row["color"],
                size=size,
                title="<br>".join(title_parts),
            )

        # Add edges
        for _, row in df_edges.iterrows():
            net.add_edge(
                row["from"],
                to=row["to"],
                title=row["message"],
                width=row["weight"],
                color=row["color"],
            )

        # Add legend nodes (fixed positions outside main graph)
        legend_x = -400
        legend_y = -300
        legend_spacing = 40

        for i, (node_type, color) in enumerate(self.NODE_COLORS.items()):
            legend_id = f"legend_{node_type}"
            net.add_node(
                legend_id,
                label=node_type.replace("_", " ").title(),
                color=color,
                size=15,
                x=legend_x,
                y=legend_y + i * legend_spacing,
                physics=False,
                fixed=True,
            )

        # Configure physics
        net.set_options(
            """
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {
                    "iterations": 150
                }
            },
            "nodes": {
                "font": {
                    "size": 12
                }
            },
            "edges": {
                "smooth": {
                    "type": "continuous"
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 100,
                "navigationButtons": true,
                "keyboard": true
            }
        }
        """
        )

        if show_buttons:
            net.show_buttons(filter_=["physics"])

        return net

    def get_network_html(
        self, data: NetworkData | None = None, height: str = "800px"
    ) -> str:
        """Generate HTML string for network visualization."""
        if data is not None:
            df_nodes = self.build_nodes_dataframe(data)
            df_edges = self.build_edges_dataframe(data)
        else:
            df_nodes = None
            df_edges = None

        net = self.create_pyvis_network(df_edges, df_nodes, height=height)

        # Save to temp file and read HTML
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as tmp:
            net.save_graph(tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Clean up
        Path(tmp_path).unlink(missing_ok=True)

        return html

    def filter_network(self, criteria: NetworkFilterCriteria) -> NetworkData:
        """Filter network data based on criteria."""
        data = self.load_network()

        # Filter nodes
        filtered_nodes = data.nodes
        if criteria.node_types:
            filtered_nodes = [n for n in filtered_nodes if n.type in criteria.node_types]
        if criteria.countries:
            filtered_nodes = [n for n in filtered_nodes if n.country in criteria.countries]

        # Get IDs of filtered nodes
        node_ids = {n.id for n in filtered_nodes}

        # Filter edges - keep edges where both source and target are in filtered nodes
        filtered_edges = data.edges
        if criteria.edge_types:
            filtered_edges = [e for e in filtered_edges if e.type in criteria.edge_types]
        filtered_edges = [
            e
            for e in filtered_edges
            if e.source in node_ids and e.target in node_ids
        ]

        return NetworkData(
            nodes=filtered_nodes,
            edges=filtered_edges,
            metadata=data.metadata,
        )

    def get_node_types(self) -> list[str]:
        """Get all unique node types."""
        data = self.load_network()
        return sorted(set(n.type for n in data.nodes))

    def get_edge_types(self) -> list[str]:
        """Get all unique edge types."""
        data = self.load_network()
        return sorted(set(e.type for e in data.edges))

    def get_countries(self) -> list[str]:
        """Get all unique countries."""
        data = self.load_network()
        return sorted(set(n.country for n in data.nodes))

    def get_network_stats(self, data: NetworkData | None = None) -> NetworkStats:
        """Get network statistics."""
        if data is None:
            data = self.load_network()

        node_type_counts: dict[str, int] = {}
        for node in data.nodes:
            node_type_counts[node.type] = node_type_counts.get(node.type, 0) + 1

        edge_type_counts: dict[str, int] = {}
        for edge in data.edges:
            edge_type_counts[edge.type] = edge_type_counts.get(edge.type, 0) + 1

        country_counts: dict[str, int] = {}
        for node in data.nodes:
            country_counts[node.country] = country_counts.get(node.country, 0) + 1

        return NetworkStats(
            total_nodes=len(data.nodes),
            total_edges=len(data.edges),
            node_type_counts=node_type_counts,
            edge_type_counts=edge_type_counts,
            country_counts=country_counts,
        )

    def get_node_by_id(self, node_id: str) -> NetworkNode | None:
        """Get a node by its ID."""
        data = self.load_network()
        for node in data.nodes:
            if node.id == node_id:
                return node
        return None

    def get_node_color(self, node_type: str) -> str:
        """Get color for a node type."""
        return self.NODE_COLORS.get(node_type, self.DEFAULT_NODE_COLOR)

    def get_edge_color(self, edge_type: str) -> str:
        """Get color for an edge type."""
        return self.EDGE_COLORS.get(edge_type, self.DEFAULT_EDGE_COLOR)
