import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------
# STEP 2 — Page Config
# ----------------------------
st.set_page_config(layout="wide")
st.title("Provisional Natality Data Dashboard")
st.subheader("Birth Analysis by State and Gender")

# ----------------------------
# STEP 3 — Load Data
# ----------------------------
try:
    df = pd.read_csv("Provisional_Natality_2025_CDC.csv")
except FileNotFoundError:
    st.error("Dataset file not found in repository.")
    st.stop()

# Normalize column names
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Logical field matcher
def match_column(possible_keywords):
    for col in df.columns:
        if any(keyword in col for keyword in possible_keywords):
            return col
    return None

column_mapping = {
    "state_of_residence": match_column(["state"]),
    "month": match_column(["month"]),
    "month_code": match_column(["month_code"]),
    "year_code": match_column(["year"]),
    "sex_of_infant": match_column(["sex", "gender"]),
    "births": match_column(["birth"])
}

# Validate required logical fields
required_fields = ["state_of_residence", "month", "sex_of_infant", "births"]
missing_fields = [f for f in required_fields if column_mapping[f] is None]

if missing_fields:
    st.error(f"Missing required logical fields: {missing_fields}")
    st.write(df.columns)
    st.stop()

# Rename matched columns to logical names
rename_dict = {
    column_mapping[key]: key
    for key in column_mapping
    if column_mapping[key] is not None
}
df = df.rename(columns=rename_dict)

# Convert births to numeric
df["births"] = pd.to_numeric(df["births"], errors="coerce")
df = df.dropna(subset=["births"])

# ----------------------------
# STEP 4 — Sidebar Filters
# ----------------------------
st.sidebar.header("Filters")

def build_multiselect(label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(
        label,
        options=["All"] + options,
        default=["All"]
    )

selected_months = build_multiselect("Select Month", "month")
selected_genders = build_multiselect("Select Gender", "sex_of_infant")
selected_states = build_multiselect("Select State", "state_of_residence")

# ----------------------------
# STEP 5 — Filtering Logic
# ----------------------------
filtered_df = df.copy()

if "All" not in selected_months:
    filtered_df = filtered_df[
        filtered_df["month"].isin(selected_months)
    ]

if "All" not in selected_genders:
    filtered_df = filtered_df[
        filtered_df["sex_of_infant"].isin(selected_genders)
    ]

if "All" not in selected_states:
    filtered_df = filtered_df[
        filtered_df["state_of_residence"].isin(selected_states)
    ]

# Edge case: empty result
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ----------------------------
# STEP 6 — Aggregation
# ----------------------------
agg_df = (
    filtered_df
    .groupby(["state_of_residence", "sex_of_infant"], as_index=False)
    .agg({"births": "sum"})
    .sort_values("state_of_residence")
)

# ----------------------------
# STEP 7 — Plot
# ----------------------------
fig = px.bar(
    agg_df,
    x="state_of_residence",
    y="births",
    color="sex_of_infant",
    title="Total Births by State and Gender",
)

fig.update_layout(
    template="plotly_white",
    legend_title="Gender",
    xaxis_title="State of Residence",
    yaxis_title="Total Births",
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# STEP 8 — Show Filtered Table
# ----------------------------
st.subheader("Filtered Data")
st.dataframe(
    filtered_df.reset_index(drop=True),
    use_container_width=True
)
