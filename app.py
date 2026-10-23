import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Uber Ride Request Dashboard",
    page_icon="🚕",
    layout="wide"
)

st.title("🚕 Uber Ride Request Dashboard")
st.write("Explore ride request outcomes, hourly demand, and pickup-point activity.")

# Load the dataset from the same folder as this app, or let the user upload it.
DATA_PATH = Path(__file__).parent / "Uber Request Data.csv"

@st.cache_data
def load_data(file):
    data = pd.read_csv(file)
    return data

df = None
if DATA_PATH.exists():
    try:
        df = load_data(str(DATA_PATH))
    except Exception as e:
        st.error(f"Could not read Uber Request Data.csv: {e}")

if df is None:
    st.info(
        "Upload **Uber Request Data.csv** to view the dashboard. "
        "For a permanent deployment, add this CSV file to the same GitHub repository as app.py."
    )
    uploaded_file = st.file_uploader("Choose the Uber Request Data CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
        except Exception as e:
            st.error(f"Could not read the uploaded CSV: {e}")
            st.stop()
    else:
        st.stop()

# Clean up column names and confirm the expected columns exist.
df.columns = df.columns.str.strip()
required_columns = ["Status", "Request timestamp", "Pickup point"]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(
        "The dataset is missing these required columns: "
        + ", ".join(missing_columns)
        + ". Please use the Uber Request Data.csv file from your lab."
    )
    st.stop()

df["Request timestamp"] = pd.to_datetime(
    df["Request timestamp"], dayfirst=True, errors="coerce"
)
df["Request Hour"] = df["Request timestamp"].dt.hour
df["Status"] = df["Status"].fillna("Unknown").astype(str)
df["Pickup point"] = df["Pickup point"].fillna("Unknown").astype(str)

# Sidebar filters
st.sidebar.header("Dashboard Filters")
all_statuses = sorted(df["Status"].dropna().unique().tolist())
selected_statuses = st.sidebar.multiselect(
    "Select ride status",
    options=all_statuses,
    default=all_statuses
)
pickup_points = sorted(df["Pickup point"].dropna().unique().tolist())
selected_pickup_points = st.sidebar.multiselect(
    "Select pickup point",
    options=pickup_points,
    default=pickup_points
)

filtered_df = df[
    df["Status"].isin(selected_statuses)
    & df["Pickup point"].isin(selected_pickup_points)
].copy()

# Key numbers
total_requests = len(filtered_df)
completed_count = int((filtered_df["Status"].str.strip().str.lower() == "trip completed").sum())
completed_pct = (completed_count / total_requests * 100) if total_requests else 0

m1, m2 = st.columns(2)
m1.metric("Total Requests (filtered)", f"{total_requests:,}")
m2.metric("Completed Rides", f"{completed_count:,}", f"{completed_pct:.1f}% of filtered requests")

st.caption("Charts update automatically when you change the filters in the sidebar.")

if filtered_df.empty:
    st.warning("No records match the selected filters. Select at least one status and pickup point.")
    st.stop()

# Chart 1: status distribution
st.subheader("1. Ride Request Status")
status_counts = (
    filtered_df["Status"].value_counts()
    .rename_axis("Status")
    .reset_index(name="Number of Requests")
)
fig_status = px.bar(
    status_counts,
    x="Status",
    y="Number of Requests",
    color="Status",
    text="Number of Requests",
    title="Number of Requests by Status"
)
fig_status.update_layout(showlegend=False, xaxis_title="Ride Status", yaxis_title="Requests")
st.plotly_chart(fig_status, use_container_width=True)

# Chart 2: requests by hour
st.subheader("2. Ride Requests by Hour")
hourly = (
    filtered_df.dropna(subset=["Request Hour"])
    .groupby("Request Hour")
    .size()
    .reindex(range(24), fill_value=0)
    .rename("Requests")
    .reset_index()
)
hourly.columns = ["Request Hour", "Requests"]
fig_hour = px.line(
    hourly,
    x="Request Hour",
    y="Requests",
    markers=True,
    title="Number of Ride Requests by Hour"
)
fig_hour.update_xaxes(dtick=1)
fig_hour.update_layout(xaxis_title="Hour of Day (24-hour clock)", yaxis_title="Requests")
st.plotly_chart(fig_hour, use_container_width=True)

# Chart 3: requests by pickup point
st.subheader("3. Requests by Pickup Point")
pickup_counts = (
    filtered_df["Pickup point"].value_counts()
    .rename_axis("Pickup point")
    .reset_index(name="Number of Requests")
)
fig_pickup = px.bar(
    pickup_counts,
    x="Pickup point",
    y="Number of Requests",
    color="Pickup point",
    text="Number of Requests",
    title="Ride Requests: City vs Airport"
)
fig_pickup.update_layout(showlegend=False, xaxis_title="Pickup Point", yaxis_title="Requests")
st.plotly_chart(fig_pickup, use_container_width=True)

with st.expander("Preview filtered data"):
    st.dataframe(filtered_df, use_container_width=True)

st.caption("Built with Streamlit and Plotly for the Data Visualization Lab.")
