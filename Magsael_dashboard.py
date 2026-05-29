import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -- Page config ---------------------------------------------------------------

st.set_page_config(
    page_title="SDG 2 — Zero Hunger Dashboard",
    page_icon="🌍",
    layout="wide",
)

# -- Colour palette ------------------------------------------------------------

PINK   = "#FFC200"
MINT   = "#FFD966"
BLUE   = "#FFE599"
PURPLE = "#B8860B"
ORANGE = "#E8A020"
BG     = "#1A1A2E"
CARD   = "#16213E"
TEXT   = "#E0E0E0"

TIER_COLORS = {
    "Low (<10)":          "#4CAF50",
    "Moderate (10-19.9)": MINT,
    "Serious (20-34.9)":  ORANGE,
    "Alarming (35+)":     "#FF4500",
}

# -- Global dark styling -------------------------------------------------------

st.markdown(f"""
<style>
  .stApp, [data-testid="stAppViewContainer"] {{
      background-color: {BG};
      color: {TEXT};
  }}
  [data-testid="stHeader"] {{ background-color: {BG}; }}
  [data-testid="stSidebar"] {{ background-color: {CARD}; }}

  [data-testid="metric-container"] {{
      background: {CARD};
      border-radius: 12px;
      padding: 14px 18px;
      border-top: 3px solid {PINK};
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  }}
  [data-testid="stMetricLabel"] {{ color: #aaa !important; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
  [data-testid="stMetricValue"] {{ color: {TEXT} !important; font-size: 26px; }}

  h1, h2, h3 {{ color: {TEXT} !important; }}
  p, label   {{ color: {TEXT}; }}

  .stSelectbox label, .stMultiSelect label,
  .stSlider label {{ color: #aaa !important; font-size: 13px; }}

  .footer {{
      text-align: center;
      color: #555;
      font-size: 12px;
      margin-top: 16px;
  }}
</style>
""", unsafe_allow_html=True)

# -- 0. Load data --------------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("ghi_cleaned.csv")
    df["Year"] = df["Year"].astype(int)
    return df

df = load_data()
YEARS     = sorted(df["Year"].unique())
COUNTRIES = sorted(df["Country"].unique())

# -- 1. Helpers ----------------------------------------------------------------

def dark_layout(fig, title=None, **kwargs):
    fig.update_layout(
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font_color=TEXT,
        title=title,
        margin=dict(l=10, r=10, t=45, b=10),
        **kwargs,
    )
    return fig

def severity_tier(score):
    if score < 10:  return "Low (<10)"
    if score < 20:  return "Moderate (10-19.9)"
    if score < 35:  return "Serious (20-34.9)"
    return "Alarming (35+)"

# -- 2. Header -----------------------------------------------------------------

st.markdown(f"""
<div style="margin-bottom:24px">
  <h1 style="margin:0;font-size:28px">🌍 SDG 2: Zero Hunger</h1>
</div>
""", unsafe_allow_html=True)

# -- 3. Controls ---------------------------------------------------------------

ctrl_col1, ctrl_col2 = st.columns([2, 3])

with ctrl_col1:
    year = st.select_slider("Select Year", options=YEARS, value=YEARS[-1])

with ctrl_col2:
    default_countries = [c for c in ["Philippines", "India", "Nigeria", "Brazil"]
                         if c in COUNTRIES]
    selected_countries = st.multiselect(
        "Select Countries (Trend Chart)",
        options=COUNTRIES,
        default=default_countries or COUNTRIES[:4],
    )

# -- 4. KPI Row ----------------------------------------------------------------

sub_year  = df[df["Year"] == year]
prev_year = year - 1
sub_prev  = df[df["Year"] == prev_year] if prev_year in YEARS else None

def delta(col):
    if sub_prev is None or sub_prev.empty:
        return None
    return round(sub_year[col].mean() - sub_prev[col].mean(), 1)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Avg GHI Score",          f"{sub_year['GHI_Score'].mean():.1f}",         delta=delta("GHI_Score"))
kpi2.metric("Countries Tracked",       str(sub_year['Country'].nunique()))
kpi3.metric("Avg Undernourishment %",  f"{sub_year['Undernourishment'].mean():.1f}%", delta=delta("Undernourishment"))
kpi4.metric("Avg Child Mortality %",   f"{sub_year['ChildMortality'].mean():.1f}%",   delta=delta("ChildMortality"))
kpi5.metric("Avg Child Stunting %",    f"{sub_year['ChildStunting'].mean():.1f}%",    delta=delta("ChildStunting"))

st.markdown("<br>", unsafe_allow_html=True)

# -- 5. Row 1: Choropleth + Severity Donut ------------------------------------

row1_left, row1_right = st.columns([3, 2])

with row1_left:
    st.markdown(f'<h4 style="color:{PINK};margin-bottom:8px">GHI Score by Country</h4>',
                unsafe_allow_html=True)
    map_sub = sub_year.dropna(subset=["GHI_Score"])
    fig_map = px.choropleth(
        map_sub, locations="Country", locationmode="country names",
        color="GHI_Score",
        color_continuous_scale=[[0, MINT], [0.5, "#FFA07A"], [1, "#8B0000"]],
        range_color=[0, 55],
        labels={"GHI_Score": "GHI Score"},
    )
    fig_map.update_layout(
        paper_bgcolor=CARD, plot_bgcolor=CARD, font_color=TEXT,
        geo=dict(bgcolor=BG, showframe=False, showcoastlines=True, coastlinecolor="#333"),
        coloraxis_colorbar=dict(title="GHI Score", tickfont=dict(color=TEXT)),
        margin=dict(l=0, r=0, t=10, b=0),
        title=f"GHI Score — {year}",
    )
    st.plotly_chart(fig_map, use_container_width=True)

with row1_right:
    st.markdown(f'<h4 style="color:{MINT};margin-bottom:8px">GHI Severity Tier Breakdown</h4>',
                unsafe_allow_html=True)
    donut_sub = sub_year.dropna(subset=["GHI_Score"]).copy()
    donut_sub["Tier"] = donut_sub["GHI_Score"].apply(severity_tier)
    tier_counts = donut_sub["Tier"].value_counts().reset_index()
    tier_counts.columns = ["Tier", "Count"]
    tier_counts = tier_counts.dropna(subset=["Tier"])
    tier_order  = list(TIER_COLORS.keys())
    tier_counts["Tier"] = pd.Categorical(tier_counts["Tier"], categories=tier_order, ordered=True)
    tier_counts = tier_counts.sort_values("Tier")

    fig_donut = go.Figure(go.Pie(
        labels=tier_counts["Tier"],
        values=tier_counts["Count"],
        hole=0.55,
        marker=dict(colors=[TIER_COLORS[t] for t in tier_counts["Tier"]],
                    line=dict(color=BG, width=2)),
        textinfo="label+percent",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="%{label}<br>%{value} countries<br>%{percent}<extra></extra>",
    ))
    fig_donut.add_annotation(
        text=f"<b>{len(donut_sub)}</b><br>countries",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=TEXT, size=13),
    )
    dark_layout(fig_donut, title=f"Severity Distribution — {year}", showlegend=False)
    st.plotly_chart(fig_donut, use_container_width=True)

# -- 6. Row 2: Trend lines (full width) ---------------------------------------

st.markdown(f'<h4 style="color:{BLUE};margin-bottom:8px">GHI Score Trends Over Time</h4>',
            unsafe_allow_html=True)
countries_sel = selected_countries if selected_countries else ["Philippines"]
trend_sub = df[df["Country"].isin(countries_sel)]
fig_trend = px.line(
    trend_sub, x="Year", y="GHI_Score", color="Country",
    markers=True,
    labels={"GHI_Score": "GHI Score"},
    color_discrete_sequence=[PINK, MINT, BLUE, PURPLE, "#FFD700", "#FF7F50", "#87CEEB"],
)
dark_layout(fig_trend, title="GHI Score Over Time by Country",
            xaxis=dict(tickvals=YEARS, gridcolor="#2a2a4a"),
            yaxis=dict(gridcolor="#2a2a4a"),
            legend=dict(bgcolor=CARD, bordercolor="#333"))
st.plotly_chart(fig_trend, use_container_width=True)

# -- 7. Row 3: Top 15 Bar + Heatmap -------------------------------------------

row3_left, row3_right = st.columns([2, 3])

with row3_left:
    st.markdown(f'<h4 style="color:{PINK};margin-bottom:8px">Top 15 Countries by GHI Score</h4>',
                unsafe_allow_html=True)
    bar_sub  = sub_year.dropna(subset=["GHI_Score"])
    top15    = bar_sub.nlargest(15, "GHI_Score").sort_values("GHI_Score")
    bar_cols = [MINT if v < 20 else "#FFA07A" if v < 35 else "#FF4500"
                for v in top15["GHI_Score"]]
    fig_bar = go.Figure(go.Bar(
        x=top15["GHI_Score"], y=top15["Country"],
        orientation="h",
        marker_color=bar_cols,
        text=top15["GHI_Score"].round(1),
        textposition="outside",
    ))
    dark_layout(fig_bar, title=f"Top 15 Highest GHI Scores — {year}",
                xaxis_title="GHI Score", yaxis_title="",
                yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

with row3_right:
    st.markdown(f'<h4 style="color:{ORANGE};margin-bottom:8px">GHI Score Heatmap — Country x Year</h4>',
                unsafe_allow_html=True)

    heatmap_countries = st.multiselect(
        "Countries for heatmap (leave blank = top 20 by latest GHI)",
        options=COUNTRIES,
        default=[],
        key="heatmap_sel",
    )
    if heatmap_countries:
        heat_countries = heatmap_countries
    else:
        heat_countries = (
            df[df["Year"] == YEARS[-1]]
            .dropna(subset=["GHI_Score"])
            .nlargest(20, "GHI_Score")["Country"]
            .tolist()
        )

    heat_df    = df[df["Country"].isin(heat_countries)].dropna(subset=["GHI_Score"])
    heat_pivot = heat_df.pivot_table(index="Country", columns="Year", values="GHI_Score")
    heat_pivot = heat_pivot.reindex(
        heat_pivot.mean(axis=1).sort_values(ascending=False).index
    )

    fig_heat = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=[str(y) for y in heat_pivot.columns],
        y=heat_pivot.index.tolist(),
        colorscale=[[0, MINT], [0.5, "#FFA07A"], [1, "#8B0000"]],
        zmin=0, zmax=55,
        colorbar=dict(title="GHI Score", tickfont=dict(color=TEXT)),
        hovertemplate="Country: %{y}<br>Year: %{x}<br>GHI Score: %{z:.1f}<extra></extra>",
    ))
    dark_layout(fig_heat, title="GHI Score Heatmap",
                xaxis=dict(title="Year", gridcolor="#2a2a4a"),
                yaxis=dict(title="", autorange="reversed"))
    st.plotly_chart(fig_heat, use_container_width=True)

# -- 8. Footer -----------------------------------------------------------------

st.markdown(
    '<p class="footer">Data Source: Global Hunger Index 2025 (Welthungerhilfe &amp; Concern Worldwide) '
    '&nbsp;|&nbsp; SDG 2: Zero Hunger &nbsp;|&nbsp; '
    'Analytics Techniques and Tools — Finals Project</p>',
    unsafe_allow_html=True,
)