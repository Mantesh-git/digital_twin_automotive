import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager

st.title("Digital Twin - Smart Manufacturing Dashboard")
st.write("Automotive Robotic Assembly Line Monitor")

st.image(
    "data/factory.jpg",
    caption="Automotive Robotic Assembly Line - Digital Twin Monitor",
    width=700
)

db = DatabaseManager()

summary   = db.get_station_summary()
failures  = db.get_failure_rate()
daily     = db.get_daily_production()
anomalies = db.get_all_anomalies()

# Section 1 - KPI numbers at the top
st.subheader("Quick Stats")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Readings",   f"{sum(int(s['total_readings']) for s in summary):,}")
col2.metric("Total Failures",   f"{sum(int(s['total_failures']) for s in summary):,}")
col3.metric("Total Anomalies",  f"{len(anomalies):,}")
col4.metric("Stations Monitored", "6")

st.divider()

# Section 2 - Station Summary table
st.subheader("Station Summary")
if summary:
    df = pd.DataFrame(summary)
    st.dataframe(df, use_container_width=True)

st.divider()

# Section 3 - Bar chart for failures per station
st.subheader("Failures per Station")
if summary:
    df_chart = pd.DataFrame(summary)
    df_chart["total_failures"] = pd.to_numeric(df_chart["total_failures"], errors="coerce")
    st.bar_chart(df_chart.set_index("station_id")["total_failures"])

st.divider()

# Section 4 - Failure Rate table
st.subheader("Failure Rate per Station")
if failures:
    df2 = pd.DataFrame(failures)
    st.dataframe(df2, use_container_width=True)

st.divider()

# Section 5 - Daily Production table
st.subheader("Daily Production")
if daily:
    df3 = pd.DataFrame(daily)
    st.dataframe(df3, use_container_width=True)

st.divider()

# Section 6 - Line chart for daily production trend
st.subheader("Daily Production Trend")
if daily:
    df_line = pd.DataFrame(daily)
    df_line["production_date"] = pd.to_datetime(df_line["production_date"])
    df_line["total_readings"]  = pd.to_numeric(df_line["total_readings"],  errors="coerce")
    df_line["daily_failures"]  = pd.to_numeric(df_line["daily_failures"],  errors="coerce")
    st.line_chart(df_line.set_index("production_date")[["total_readings", "daily_failures"]])

st.divider()

# Section 7 - Recent Anomalies with severity filter
st.subheader("Recent Anomalies")
if anomalies:
    df4 = pd.DataFrame(anomalies)

    # Simple dropdown to filter by severity
    severity = st.selectbox("Filter by Severity", ["ALL", "HIGH", "MEDIUM", "LOW"])
    if severity != "ALL":
        df4 = df4[df4["severity"] == severity]

    cols_to_show = ["udi", "station_id", "failure_type",
                    "failure_desc", "severity", "detected_at"]
    available = [c for c in cols_to_show if c in df4.columns]
    st.dataframe(df4[available].head(50), use_container_width=True)
else:
    st.write("No anomalies found. Run main.py first.")

st.divider()
st.write("Mahantesh Hosmani | Digital Twin Automotive Dashboard")