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
    # If you run from repo root: streamlit run app/app.py
    # This path assumes app.py is in /app and data is in /data
    df = pd.read_csv("../data/incidents_12000.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# --------------------------------------------------
# HELPER: FILTER DATA
# --------------------------------------------------
def filter_data(df):
    st.sidebar.header("Filters")

    # Date range
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

    # Region filter
    regions = st.sidebar.multiselect(
        "Region",
        options=sorted(df["region"].unique()),
        default=sorted(df["region"].unique()),
    )

    # Channel filter
    channels = st.sidebar.multiselect(
        "Channel",
        options=sorted(df["channel"].unique()),
        default=sorted(df["channel"].unique()),
    )

    # Severity filter
    severities = st.sidebar.multiselect(
        "Severity level",
        options=sorted(df["severity_level"].unique()),
        default=sorted(df["severity_level"].unique()),
    )

    # Category filter
    categories = st.sidebar.multiselect(
        "Category",
        options=sorted(df["category"].unique()),
        default=sorted(df["category"].unique()),
    )

    # Subsystem filter
    subsystems = st.sidebar.multiselect(
        "Subsystem",
        options=sorted(df["subsystem"].unique()),
        default=sorted(df["subsystem"].unique()),
    )

    # SLA filter
    sla_filter = st.sidebar.selectbox(
        "SLA breached?",
        options=["All", "Yes", "No"],
    )

    # Apply filters
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

    filtered = df[mask].copy()
    return filtered


# --------------------------------------------------
# KPI CALCULATION
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
    repeat_rate = df["is_repeated_incident"].mean() * 100 if total_incidents > 0 else 0

    return {
        "Total Incidents": int(total_incidents),
        "SLA Breach Rate (%)": round(sla_breach_rate, 2),
        "Avg Resolution Time (hrs)": round(avg_resolution, 2),
        "Total Financial Impact ($)": round(total_impact, 2),
        "Repeated Incident Rate (%)": round(repeat_rate, 2),
    }


# --------------------------------------------------
# AUTO-INSIGHTS
# --------------------------------------------------
def generate_insights(df):
    insights = []

    if df.empty:
        insights.append("No incidents match the current filters.")
        return insights

    # Top category by incident volume
    top_cat = df["category"].value_counts().idxmax()
    insights.append(f"🔹 **{top_cat}** has the highest incident volume.")

    # Top subsystem by avg resolution time
    subsystem_rt = (
        df.groupby("subsystem")["time_to_resolve_hours"]
        .mean()
        .sort_values(ascending=False)
    )
    if len(subsystem_rt) > 0:
        worst_subsystem = subsystem_rt.index[0]
        worst_rt = subsystem_rt.iloc[0]
        insights.append(
            f"🔹 **{worst_subsystem}** has the longest average resolution time "
            f"at **{worst_rt:.1f} hours**."
        )

    # Root cause with highest share of SLA breaches
    sla_yes = df[df["sla_breached"] == "Yes"]
    if len(sla_yes) > 0:
        rc_sla = (
            sla_yes["root_cause"].value_counts(normalize=True).sort_values(ascending=False)
        )
        rc_top = rc_sla.index[0]
        rc_pct = rc_sla.iloc[0] * 100
        insights.append(
            f"🔹 **{rc_top}** is the leading root cause among SLA-breached incidents "
            f"(~{rc_pct:.1f}% of breaches)."
        )

    # Financial impact by category
    fi_by_cat = (
        df.groupby("category")["financial_impact_usd"].sum().sort_values(ascending=False)
    )
    if len(fi_by_cat) > 0:
        high_loss_cat = fi_by_cat.index[0]
        high_loss_val = fi_by_cat.iloc[0]
        insights.append(
            f"🔹 **{high_loss_cat}** drives the highest total financial impact "
            f"(~${high_loss_val:,.0f})."
        )

    return insights


# --------------------------------------------------
# MAIN LAYOUT
# --------------------------------------------------
st.title("🏦 Banking Operations – Risk & Incident Analytics Dashboard")
st.markdown(
    """
This dashboard simulates a banking operations environment with ~12,000 incidents
across payments, authentication, fraud alerts, and other workflows.

Use the filters on the left to slice incidents by date, region, channel, severity,
category, and subsystem. The visuals and KPIs update accordingly.
"""
)

filtered_df = filter_data(df)
kpis = compute_kpis(filtered_df)

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------
st.subheader("Key KPIs")

kpi_cols = st.columns(5)

kpi_cols[0].metric("Total Incidents", f"{kpis['Total Incidents']:,}")
kpi_cols[1].metric("SLA Breach Rate", f"{kpis['SLA Breach Rate (%)']}%")
kpi_cols[2].metric("Avg Resolution (hrs)", kpis["Avg Resolution Time (hrs)"])
kpi_cols[3].metric(
    "Total Financial Impact",
    f"${kpis['Total Financial Impact ($)']:,.0f}",
)
kpi_cols[4].metric(
    "Repeated Incident Rate",
    f"{kpis['Repeated Incident Rate (%)']}%",
)

st.markdown("---")

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab_overview, tab_root, tab_systems, tab_financial = st.tabs(
    ["📊 Overview", "🧩 Root Cause & SLA", "🖥 Systems, Region & Channel", "💰 Financial Impact"]
)

# ----------------- OVERVIEW TAB -------------------
with tab_overview:
    st.subheader("Incident Volume & Severity Overview")

    if filtered_df.empty:
        st.warning("No data for the selected filters.")
    else:
        # Incidents over time
        incidents_over_time = (
            filtered_df.groupby("date").size().reset_index(name="incident_count")
        )
        fig_time = px.line(
            incidents_over_time,
            x="date",
            y="incident_count",
            title="Incidents Over Time",
        )
        st.plotly_chart(fig_time, use_container_width=True)

        col1, col2 = st.columns(2)

        # Incidents by category
        with col1:
            cat_counts = (
                filtered_df["category"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "category", "category": "count"})
            )
            fig_cat = px.bar(
                cat_counts,
                x="category",
                y="count",
                title="Incidents by Category",
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        # Severity distribution
        with col2:
            sev_counts = (
                filtered_df["severity_level"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "severity_level", "severity_level": "count"})
            )
            fig_sev = px.bar(
                sev_counts,
                x="severity_level",
                y="count",
                title="Incidents by Severity Level",
            )
            st.plotly_chart(fig_sev, use_container_width=True)

# ---------------- ROOT CAUSE TAB ------------------
with tab_root:
    st.subheader("Root Causes & SLA Performance")

    if filtered_df.empty:
        st.warning("No data for the selected filters.")
    else:
        col1, col2 = st.columns(2)

        # Root cause counts
        with col1:
            rc_counts = (
                filtered_df["root_cause"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "root_cause", "root_cause": "count"})
            )
            fig_rc = px.bar(
                rc_counts,
                x="root_cause",
                y="count",
                title="Incidents by Root Cause",
            )
            st.plotly_chart(fig_rc, use_container_width=True)

        # SLA breach rate by root cause
        with col2:
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
            st.plotly_chart(fig_sla_rc, use_container_width=True)

# ------------- SYSTEMS / REGION / CHANNEL TAB -----
with tab_systems:
    st.subheader("Systems, Regions & Channels")

    if filtered_df.empty:
        st.warning("No data for the selected filters.")
    else:
        col1, col2 = st.columns(2)

        # Incidents by subsystem
        with col1:
            ss_counts = (
                filtered_df["subsystem"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "subsystem", "subsystem": "count"})
            )
            fig_ss = px.bar(
                ss_counts,
                x="subsystem",
                y="count",
                title="Incidents by Subsystem",
            )
            st.plotly_chart(fig_ss, use_container_width=True)

        # Avg resolution by subsystem
        with col2:
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
                title="Average Resolution Time by Subsystem (hrs)",
            )
            st.plotly_chart(fig_rt, use_container_width=True)

        col3, col4 = st.columns(2)

        # Incidents by region
        with col3:
            reg_counts = (
                filtered_df["region"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "region", "region": "count"})
            )
            fig_reg = px.bar(
                reg_counts,
                x="region",
                y="count",
                title="Incidents by Region",
            )
            st.plotly_chart(fig_reg, use_container_width=True)

        # Incidents by channel
        with col4:
            ch_counts = (
                filtered_df["channel"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "channel", "channel": "count"})
            )
            fig_ch = px.bar(
                ch_counts,
                x="channel",
                y="count",
                title="Incidents by Channel",
            )
            st.plotly_chart(fig_ch, use_container_width=True)

# ---------------- FINANCIAL IMPACT TAB ------------
with tab_financial:
    st.subheader("Financial Impact of Incidents")

    if filtered_df.empty:
        st.warning("No data for the selected filters.")
    else:
        col1, col2 = st.columns(2)

        # Financial impact by category
        with col1:
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
            st.plotly_chart(fig_fi_cat, use_container_width=True)

        # Financial impact by subsystem
        with col2:
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
            st.plotly_chart(fig_fi_ss, use_container_width=True)

        st.markdown("### Top 10 High-Impact Incidents")
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
# AUTO-INSIGHTS PANEL
# --------------------------------------------------
st.markdown("---")
st.subheader("🔎 Auto-Generated Insights")

insights = generate_insights(filtered_df)
for text in insights:
    st.markdown(text)
