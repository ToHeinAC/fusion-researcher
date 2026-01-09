
import plotly.graph_objects as go
import json

# Data
companies = [
    "Commonwealth Fusion (USA)",
    "TAE Technologies (USA)",
    "Helion Energy (USA)",
    "Pacific Fusion (USA)",
    "Shine Technologies (USA)",
    "First Light (UK)",
    "General Fusion (CAN)",
    "Zap Energy (USA)",
    "Proxima Fusion (DE)",
    "Tokamak Energy (UK)"
]
funding_millions_usd = [2860, 1400, 1000, 900, 800, 588, 392, 338, 214, 187]

# Create horizontal bar chart for better readability with company names
fig = go.Figure()

fig.add_trace(go.Bar(
    x=funding_millions_usd,
    y=companies,
    orientation='h',
    marker=dict(
        color=funding_millions_usd,
        colorscale=[[0, '#5D878F'], [0.5, '#1FB8CD'], [1, '#1FB8CD']],
        showscale=False
    ),
    text=[f'${x}m' for x in funding_millions_usd],
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Funding: $%{x}m<extra></extra>'
))

fig.update_layout(
    title={
        "text": "Top 10 Fusion-Startups nach Gesamtfinanzierung (2025)<br><span style='font-size: 18px; font-weight: normal;'>Commonwealth Fusion leads with nearly $3b in total funding</span>"
    },
    xaxis_title="Funding ($m)",
    yaxis_title="",
    yaxis={'categoryorder':'total ascending'},
    showlegend=False
)

fig.update_xaxes(showgrid=True)
fig.update_traces(cliponaxis=False)

# Save as both PNG and SVG
fig.write_image("fusion_startups.png")
fig.write_image("fusion_startups.svg", format="svg")
