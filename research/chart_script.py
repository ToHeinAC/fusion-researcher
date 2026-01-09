
import plotly.graph_objects as go
import json

# Data
data = {
  "categories": ["Startups", "KMU", "Konzerne", "Forschung"],
  "Deutschland": [4, 9, 3, 3],
  "USA": [8, 2, 1, 0],
  "UK": [2, 1, 0, 0],
  "BENELUX": [1, 2, 1, 4],
  "Frankreich": [1, 2, 1, 0],
  "Rest": [4, 1, 0, 0]
}

categories = data["categories"]
regions = ["Deutschland", "USA", "UK", "BENELUX", "Frankreich", "Rest"]

# Brand colors for the 6 regions
colors = ["#1FB8CD", "#DB4545", "#2E8B57", "#5D878F", "#D2BA4C", "#B4413C"]

# Create figure
fig = go.Figure()

# Add bars for each region
for i, region in enumerate(regions):
    fig.add_trace(go.Bar(
        x=categories,
        y=data[region],
        name=region,
        marker_color=colors[i]
    ))

# Update layout
fig.update_layout(
    barmode='stack',
    title={
        "text": "Kernfusion-Ökosystem nach Akteurstyp und Region<br><span style='font-size: 18px; font-weight: normal;'>Deutschland dominiert bei KMU, USA führt bei Startups</span>"
    },
    xaxis_title="Kategorie",
    yaxis_title="Anzahl",
)

# Update traces
fig.update_traces(cliponaxis=False)

# Save as PNG and SVG
fig.write_image("fusion_actors_chart.png")
fig.write_image("fusion_actors_chart.svg", format="svg")
