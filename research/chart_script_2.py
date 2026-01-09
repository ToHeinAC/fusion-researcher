
import plotly.graph_objects as go

# Data
years = [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040]
market_value = [356, 376, 395, 415, 436, 458, 480, 504, 530, 557, 585, 615, 674, 733, 780, 810, 843]

# Create figure
fig = go.Figure()

# Add line with fill (upward trend, so use strong cyan)
fig.add_trace(go.Scatter(
    x=years,
    y=market_value,
    mode='lines+markers',
    line=dict(color='#1FB8CD', width=3),
    marker=dict(size=7, color='#1FB8CD'),
    fill='tozeroy',
    fillcolor='rgba(31, 184, 205, 0.15)',
    name='Market Value',
    showlegend=False,
    hovertemplate='%{x}<br>%{y}b USD<extra></extra>'
))

# Add vertical dashed line at 2030
fig.add_vline(
    x=2030,
    line_dash="dash",
    line_color="rgba(100, 100, 100, 0.5)",
    line_width=2,
    annotation_text="Erwartete erste<br>kommerzielle Anlagen",
    annotation_position="top right",
    annotation_font_size=11,
    annotation_font_color="gray"
)

# Update layout
fig.update_layout(
    title={
        "text": "Globaler Fusionsenergie-Markt: Prognose 2024-2040<br><span style='font-size: 18px; font-weight: normal;'>CAGR ~5.5-7.1% reflects accelerating commercial viability</span>"
    },
    xaxis_title="Year",
    yaxis_title="Value (bn $)",
    yaxis=dict(range=[0, 900])
)

fig.update_traces(cliponaxis=False)
fig.update_xaxes(tickmode='linear', dtick=2)

# Save as PNG and SVG
fig.write_image("fusion_energy_market.png")
fig.write_image("fusion_energy_market.svg", format="svg")
