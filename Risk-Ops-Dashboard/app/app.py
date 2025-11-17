import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Banking Ops – Risk & Incident Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Risk-Ops-Dashboard/data/incidents_12000.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# --------------------------------------------------
# FILTER SIDEBAR
# --------------------------------------------------
def filter_data(df):
    st.sidebar.header("Filters")

    min_date = df["date"].min()
    max_date = df["date"].max()

    date_range = st.sidebar.date_input(
        "Date range", value=(min_date, max_date),
        min_value=min_date, max_value=max_date
    )
    start_date, end_date = date_range if isinstance(date_range, tuple) else (min_date, max_date)

    regions = st.sidebar.multiselect(
        "Region", options=sorted(df["region"].unique()),
        default=sorted(df["region"].unique())
    )

    channels = st.sidebar.multiselect(
        "Channel", options=sorted(df["channel"].unique()),
        default=sorted(df["channel"].unique())
    )

    severities = st.sidebar.multiselect(
        "Severity level", options=sorted(df["severity_level"].unique()),
        default=sorted(df["severity_level"].unique())
    )

    categories = st.sidebar.multiselect(
        "Category", options=sorted(df["category"].unique()),
        default=sorted(df["category"].unique())
    )

    subsystems = st.sidebar.multiselect(
        "Subsystem", options=sorted(df["subsystem"].unique()),
        default=sorted(df["subsystem"].unique())
    )

    sla_filter = st.sidebar.selectbox("SLA breached?", ["All", "Yes", "No"])

    mask = (
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date)) &
        (df["region"].isin(regions)) &
        (df["channel"].isin(channels)) &
        (df["severity_level"].isin(severities)) &
        (df["category"].isin(categories)) &
        (df["subsystem"].isin(subsystems))
    )
    if sla_filter != "All":
        mask &= df["sla_breached"].eq(sla_filter)

    return df[mask].copy()

filtered_df = filter_data(df)

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
def compute_kpis(df):
    total = len(df)
    sla_rate = df["sla_breached"].value_counts(normalize=True).get("Yes", 0) * 100 if total > 0 else 0
    avg_rt = df["time_to_resolve_hours"].mean() if total > 0 else 0
    fin = df["financial_impact_usd"].sum() if total > 0 else 0
    rep = df["is_repeated_incident"].mean() * 100 if total > 0 else 0

    return {
        "Total": total,
        "SLA": round(sla_rate, 2),
        "ART": round(avg_rt, 2),
        "Impact": round(fin, 2),
        "Repeat": round(rep, 2),
    }

kpis = compute_kpis(filtered_df)

# --------------------------------------------------
# AUTO INSIGHTS
# --------------------------------------------------
def generate_insights(df):
    if df.empty:
        return ["No incidents match the current filters."]

    insights = []

    top_cat = df["category"].value_counts().idxmax()
    insights.append(f"• {top_cat} has the highest number of incidents")

    ss_rt = df.groupby("subsystem")["time_to_resolve_hours"].mean().sort_values(ascending=False)
    insights.append(f"• {ss_rt.index[0]} has the longest average resolution time at {ss_rt.iloc[0]:.1f} hours")

    sla_df = df[df["sla_breached"] == "Yes"]
    if not sla_df.empty:
        rc = sla_df["root_cause"].value_counts(normalize=True).sort_values(ascending=False)
        insights.append(f"• {rc.index[0]} is responsible for about {rc.iloc[0] * 100:.1f}% of SLA breaches")

    fi = df.groupby("category")["financial_impact_usd"].sum().sort_values(ascending=False)
    insights.append(f"• {fi.index[0]} has the highest financial impact at about ${fi.iloc[0]:,.0f}")

    return insights

# --------------------------------------------------
# PAGE TITLE
# --------------------------------------------------
st.title("Banking Operations – Risk and Incident Analytics Dashboard")

st.markdown("""
This dashboard helps track operational incidents across systems, channels, categories, and regions.
Use the filters on the left to adjust the view.
""")

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------
st.subheader("Key Metrics")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Incidents", f"{kpis['Total']:,}")
c2.metric("SLA Breach Rate", f"{kpis['SLA']}%")
c3.metric("Avg Resolution (hrs)", kpis["ART"])
c4.metric("Financial Impact", f"${kpis['Impact']:,.0f}")
c5.metric("Repeat Rate", f"{kpis['Repeat']}%")

st.markdown("---")

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab_overview, tab_root, tab_systems, tab_fin = st.tabs(
    ["Overview", "Root Cause and SLA", "Systems and Channels", "Financial Impact"]
)

# --------------------------------------------------
# TAB 1: OVERVIEW
# --------------------------------------------------
with tab_overview:
    if filtered_df.empty:
        st.warning("No data available.")
    else:
        daily = filtered_df.groupby("date").size().reset_index(name="count")
        st.plotly_chart(px.line(daily, x="date", y="count", title="Incidents Over Time"),
                        use_container_width=True)

        colA, colB = st.columns(2)

        with colA:
            cat = filtered_df["category"].value_counts().reset_index()
            cat.columns = ["category", "count"]
            st.plotly_chart(px.bar(cat, x="category", y="count", title="Incidents by Category"),
                            use_container_width=True)

        with colB:
            sev = filtered_df["severity_level"].value_counts().reset_index()
            sev.columns = ["severity_level", "count"]
            st.plotly_chart(px.bar(sev, x="severity_level", y="count", title="Incidents by Severity"),
                            use_container_width=True)

# --------------------------------------------------
# TAB 2: ROOT CAUSE
# --------------------------------------------------
with tab_root:
    if filtered_df.empty:
        st.warning("No data available.")
    else:
        colA, colB = st.columns(2)

        with colA:
            rc = filtered_df["root_cause"].value_counts().reset_index()
            rc.columns = ["root_cause", "count"]
            st.plotly_chart(px.bar(rc, x="root_cause", y="count", title="Incidents by Root Cause"),
                            use_container_width=True)

        with colB:
            temp = (
                filtered_df.groupby("root_cause")["sla_breached"]
                .value_counts(normalize=True)
                .rename("prop")
                .reset_index()
            )
            sla_yes = temp[temp["sla_breached"] == "Yes"]
            st.plotly_chart(
                px.bar(sla_yes, x="root_cause", y="prop", title="SLA Breach Rate by Root Cause"),
                use_container_width=True
            )

# --------------------------------------------------
# TAB 3: SYSTEMS / REGION / CHANNEL
# --------------------------------------------------
with tab_systems:
    if filtered_df.empty:
        st.warning("No data available.")
    else:
        colA, colB = st.columns(2)

        ss = filtered_df["subsystem"].value_counts().reset_index()
        ss.columns = ["subsystem", "count"]
        colA.plotly_chart(px.bar(ss, x="subsystem", y="count", title="Incidents by Subsystem"),
                          use_container_width=True)

        ss_rt = (
            filtered_df.groupby("subsystem")["time_to_resolve_hours"]
            .mean().reset_index().sort_values("time_to_resolve_hours", ascending=False)
        )
        colB.plotly_chart(px.bar(ss_rt, x="subsystem", y="time_to_resolve_hours",
                                 title="Avg Resolution Time by Subsystem"),
                          use_container_width=True)

        colC, colD = st.columns(2)

        reg = filtered_df["region"].value_counts().reset_index()
        reg.columns = ["region", "count"]
        colC.plotly_chart(px.bar(reg, x="region", y="count", title="Incidents by Region"),
                          use_container_width=True)

        ch = filtered_df["channel"].value_counts().reset_index()
        ch.columns = ["channel", "count"]
        colD.plotly_chart(px.bar(ch, x="channel", y="count", title="Incidents by Channel"),
                          use_container_width=True)

# --------------------------------------------------
# TAB 4: FINANCIAL IMPACT
# --------------------------------------------------
with tab_fin:
    if filtered_df.empty:
        st.warning("No data available.")
    else:
        colA, colB = st.columns(2)

        fi_cat = filtered_df.groupby("category")["financial_impact_usd"].sum().reset_index()
        fi_cat = fi_cat.sort_values("financial_impact_usd", ascending=False)
        colA.plotly_chart(px.bar(fi_cat, x="category", y="financial_impact_usd",
                                 title="Financial Impact by Category"),
                          use_container_width=True)

        fi_ss = filtered_df.groupby("subsystem")["financial_impact_usd"].sum().reset_index()
        fi_ss = fi_ss.sortsort_values("financial_impact_usd", ascending=False)
        colB.plotly_chart(px.bar(fi_ss, x="subsystem", y="financial_impact_usd",
                                 title="Financial Impact by Subsystem"),
                          use_container_width=True)

        st.subheader("Top 10 High Impact Incidents")
        top10 = filtered_df.sort_values("financial_impact_usd", ascending=False).head(10)
        st.dataframe(top10[["incident_id", "date", "category",
                            "severity_level", "subsystem", "financial_impact_usd"]])

# --------------------------------------------------
# INSIGHTS
# --------------------------------------------------
st.markdown("---")
st.subheader("Auto Insights")

for insight in generate_insights(filtered_df):
    st.markdown(insight)



