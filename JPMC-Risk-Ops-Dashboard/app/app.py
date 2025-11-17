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
    # IMPORTANT: Streamlit Cloud uses repo root as working directory
    df = pd.read_csv("JPMC-Risk-Ops-Dashboard/data/incidents_12000.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# --------------------------------------------------
# FILTER SIDEBAR
# --------------------------------------------------
def filter_data(df):
    st.sidebar.header("Filters")

    # Date range filter
    min_date = df["date"].min()
    max_date = df["date"].max()

    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    # Region
    regions = st.sidebar.multiselect(
        "Region",
        options=sorted(df["region"].unique()),
        default=sorted(df["region"].unique()),
    )

    # Channel
    channels = st.sidebar.multiselect(
        "Channel",
        options=sorted(df["channel"].unique()),
        default=sorted(df["channel"].unique()),
    )

    # Severity
    severities = st.sidebar.multiselect(
        "Severity level",
        options=sorted(df["severity_level"].unique()),
        default=sorted(df["severity_level"].unique()),
    )

    # Category
    categories = st.sidebar.multiselect(
        "Category",
        options=sorted(df["category"].unique()),
        default=sorted(df["category"].unique()),
    )

    # Subsystem
    subsystems = st.sidebar.multiselect(
        "Subsystem",
        options=sorted(df["subsystem"].unique()),
        default=sorted(df["subsystem"].unique()),
    )

    # SLA breached?
    sla_filter = st.sidebar.selectbox("SLA breached?", ["All", "Yes", "No"])

    # Apply conditions
    mask = (
        (df["date"] >= pd.to_datetime(start_date))
        & (df["date"] <= pd.to_datetime(end_date))
        & (df["region"].isin(regions))
        & (df["channel"].isin(channels))
        & (df["severity_level"].isin(severities))
        & (df["category"].isin(categories))
        & (df["subsystem"].isin(subsystems))
    )

    if sla_filter != "All":
        mask &= df["sla_breached"].eq(sla_filter)

    return df[mask].copy()


filtered_df = filter_data(df)

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
def compute_kpis(df):
    total_incidents = len(df)
    sla_breach_rate = (
        df["sla_breached"].value_counts(normalize=True).get("Yes", 0) * 100
        if total_incidents > 0
        else 0
    )
    avg_resolution = df["time_to_resolve_hours"].mean() if total_incidents > 0 else 0
    total_impact = df["financial_impact_usd"].sum() if total_incidents > 0 else 0
    repeat_rate = (
        df["is_repeated_incident"].mean() * 100 if total_incidents > 0 else 0
    )

    return {
        "Total Incidents": int(total_incidents),
        "SLA Breach Rate (%)": round(sla_breach_rate, 2),
        "Avg Resolution Time (hrs)": round(avg_resolution, 2),
        "Total Financial Impact ($)": round(total_impact, 2),
        "Repeated Incident Rate (%)": round(repeat_rate, 2),
    }


kpis = compute_kpis(filtered_df)

# --------------------------------------------------
# AUTO-INSIGHTS
# --------------------------------------------------
def generate_insights(df):
    insights = []

    if df.empty:
        insights.append("No incidents match the selected filters.")
        return insights

    # Category with most incidents
    top_cat = df["category"].value_counts().idxmax()
    insights.append(f"🔹 **{top_cat}** has the highest incident volume.")

    # Subsystem with worst avg resolution time
    subsystem_rt = (
        df.groupby("subsystem")["time_to_resolve_hours"]
        .mean()
        .sort_values(ascending=False)
    )
    worst_sub = subsystem_rt.index[0]
    worst_rt = subsystem_rt.iloc[0]
    insights.append(
        f"🔹 **{worst_sub}** has the longest average resolution time "
        f"at **{worst_rt:.1f} hours**."
    )

    # Root cause driving SLA breaches
    sla_df = df[df["sla_breached"] == "Yes"]
    if not sla_df.empty:
        rc = (
            sla_df["root_cause"]
            .value_counts(normalize=True)
            .sort_values(ascending=False)
        )
        top_rc = rc.index[0]
        top_rc_pct = rc.iloc[0] * 100
        insights.append(
            f"🔹 **{top_rc}** accounts for ~{top_rc_pct:.1f}% of SLA-breached incidents."
        )

    # Category with highest financial impact
    fi_cat = (
        df.groupby("category")["financial_impact_usd"].sum().sort_values(ascending=False)
    )
    top_fi_cat = fi_cat.index[0]
    top_fi_val = fi_cat.iloc[0]
    insights.append(
        f"🔹 **{top_fi_cat}** drives the highest financial impact "
        f"(~${top_fi_val:,.0f})."
    )

    return insights

# --------------------------------------------------
# PAGE TITLE
# --------------------------------------------------
st.title("🏦 Banking Operations – Risk & Incident Analytics Dashboard")

st.markdown(
    """
This dashboard simulates a banking operations environment with ~12,000 incidents  
across payments, authentication, fraud alerts, API failures, and other areas.  

Use the filters on the left to slice the data by time period, channel, region,  
severity, category, subsystem, and SLA performance.
"""
)


# --------------------------------------------------
# KPI DISPLAY
# --------------------------------------------------
st.subheader("Key KPIs")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Incidents", f"{kpis['Total Incidents']:,}")
col2.metric("SLA Breach Rate", f"{kpis['SLA Breach Rate (%)']}%")
col3.metric("Avg Resolution (hrs)", kpis["Avg Resolution Time (hrs)"])
col4.metric("Total Financial Impact", f"${kpis['Total Financial Impact ($)']:,.0f}")
col5.metric("Repeated Incident Rate", f"{kpis['Repeated Incident Rate (%)']}%")

st.markdown("---")

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab_overview, tab_root, tab_systems, tab_financial = st.tabs(
    ["📊 Overview", "🧩 Root Cause & SLA", "🖥 Systems, Region & Channel", "💰 Financial Impact"]
)

# ---------------- OVERVIEW TAB ---------------------
with tab_overview:
    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        # Incidents over time
        incidents_over_time = (
            filtered_df.groupby("date").size().reset_index(name="count")
        )
        fig_time = px.line(
            incidents_over_time,
            x="date",
            y="count",
            title="Incidents Over Time",
        )
        st.plotly_chart(fig_time, use_container_width=True)

        col1, col2 = st.columns(2)

        # Incidents by category
        with col1:
            cat = (
                filtered_df["category"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "category", "category": "count"})
            )
            fig_cat = px.bar(cat, x="category", y="count", title="Incidents by Category")
            st.plotly_chart(fig_cat, use_container_width=True)

        # Severity distribution
        with col2:
            sev = (
                filtered_df["severity_level"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "severity_level", "severity_level": "count"})
            )
            fig_sev = px.bar(
                sev, x="severity_level", y="count", title="Incidents by Severity Level"
            )
            st.plotly_chart(fig_sev, use_container_width=True)


# ---------------- ROOT CAUSE TAB --------------------
with tab_root:
    if filtered_df.empty:
        st.warning("No data for selected filters.")
    else:
        col1, col2 = st.columns(2)

        # Root cause distribution
        rc_counts = (
            filtered_df["root_cause"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "root_cause", "root_cause": "count"})
        )
        fig_rc = px.bar(
            rc_counts, x="root_cause", y="count", title="Incidents by Root Cause"
        )
        col1.plotly_chart(fig_rc, use_container_width=True)

        # SLA breach by root cause
        temp = (
            filtered_df.groupby("root_cause")["sla_breached"]
            .value_counts(normalize=True)
            .rename("proportion")
            .reset_index()
        )
        sla_yes = temp[temp["sla_breached"] == "Yes"]

        fig_sla_rc = px.bar(
            sla_yes,
            x="root_cause",
            y="proportion",
            title="SLA Breach Rate by Root Cause",
        )
        fig_sla_rc.update_layout(yaxis_tickformat=".0%")
        col2.plotly_chart(fig_sla_rc, use_container_width=True)


# ------------- SYSTEMS / REGION / CHANNEL TAB -------
with tab_systems:
    if filtered_df.empty:
        st.warning("No data for selected filters.")
    else:
        col1, col2 = st.columns(2)

        # Incidents by subsystem
        ss = (
            filtered_df["subsystem"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "subsystem", "subsystem": "count"})
        )
        fig_ss = px.bar(
            ss, x="subsystem", y="count", title="Incidents by Subsystem"
        )
        col1.plotly_chart(fig_ss, use_container_width=True)

        # Avg resolution by subsystem
        ss_rt = (
            filtered_df.groupby("subsystem")["time_to_resolve_hours"]
            .mean()
            .reset_index()
            .sort_values("time_to_resolve_hours", ascending=False)
        )
        fig_rt = px.bar(
            ss_rt,
            x="subsystem",
            y="time_to_resolve_hours",
            title="Avg Resolution Time by Subsystem (hrs)",
        )
        col2.plotly_chart(fig_rt, use_container_width=True)

        col3, col4 = st.columns(2)

        # Region
        reg = (
            filtered_df["region"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "region", "region": "count"})
        )
        fig_reg = px.bar(reg, x="region", y="count", title="Incidents by Region")
        col3.plotly_chart(fig_reg, use_container_width=True)

        # Channel
        ch = (
            filtered_df["channel"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "channel", "channel": "count"})
        )
        fig_ch = px.bar(ch, x="channel", y="count", title="Incidents by Channel")
        col4.plotly_chart(fig_ch, use_container_width=True)


# ---------------- FINANCIAL IMPACT TAB --------------
with tab_financial:
    if filtered_df.empty:
        st.warning("No data for selected filters.")
    else:
        col1, col2 = st.columns(2)

        # Financial impact by category
        fi_cat = (
            filtered_df.groupby("category")["financial_impact_usd"]
            .sum()
            .reset_index()
            .sort_values("financial_impact_usd", ascending=False)
        )
        fig_fi_cat = px.bar(
            fi_cat,
            x="category",
            y="financial_impact_usd",
            title="Total Financial Impact by Category",
        )
        col1.plotly_chart(fig_fi_cat, use_container_width=True)

        # Financial impact by subsystem
        fi_ss = (
            filtered_df.groupby("subsystem")["financial_impact_usd"]
            .sum()
            .reset_index()
            .sort_values("financial_impact_usd", ascending=False)
        )
        fig_fi_ss = px.bar(
            fi_ss,
            x="subsystem",
            y="financial_impact_usd",
            title="Total Financial Impact by Subsystem",
        )
        col2.plotly_chart(fig_fi_ss, use_container_width=True)

        st.subheader("Top 10 High Impact Incidents")
        top10 = filtered_df.sort_values(
            "financial_impact_usd", ascending=False
        ).head(10)

        st.dataframe(
            top10[
                [
                    "incident_id",
                    "date",
                    "category",
                    "severity_level",
                    "subsystem",
                    "financial_impact_usd",
                ]
            ]
        )

# --------------------------------------------------
# AUTO INSIGHTS SECTION
# --------------------------------------------------
st.markdown("---")
st.subheader("🔎 Auto-Generated Insights")

for insight in generate_insights(filtered_df):
    st.markdown(insight)

