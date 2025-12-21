import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from pathlib import Path

@st.cache_data
def load_data():
    project_root = Path(os.getcwd()).resolve().parent
    csv_loc = project_root / "data" / "processed" / "crime_data_processed.csv"
    df = pd.read_csv(csv_loc)

    geojson_loc = project_root / "json" / "cleaned.geojson"
    with open(geojson_loc, 'r') as f:
        india_states = json.load(f)

    all_states = [feature["properties"]["NAME_1"] for feature in india_states["features"]]
    all_states_df = pd.DataFrame({"State": all_states})

    return df, india_states, all_states_df


df, india_states, all_states_df = load_data()


st.set_page_config(page_title="Fast India Crime Map", layout="wide", page_icon='../stock/logo.png')
st.title("India Crime Data Visualization")


# Filter UI



with st.form("filters_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        year_filter = st.selectbox("Year", sorted(df['Year'].unique()), index=0)
    with col2:
        months = sorted(df['Month'].unique())
        month_filter = st.selectbox("Month", ["All"] + [str(m) for m in months], index=0)
    with col3:
        crimes = sorted(df['Crime Description'].unique())
        crime_filter = st.selectbox("Crime Type", ["All"] + crimes, index=0)
    submitted = st.form_submit_button("Update Map")


# Processing n visualization on submit

if submitted:
    # Filter  year
    df_filtered = df[df['Year'] == year_filter]

    # Month filtering 
    if month_filter != "All":
        df_filtered = df_filtered[df_filtered['Month'] == int(month_filter)]

    # Crime filtering 
    if crime_filter != "All":
        df_filtered = df_filtered[df_filtered['Crime Description'] == crime_filter]

    # Group & aggregate by state
    df_agg = (
        df_filtered.groupby("State", as_index=False)["Crime Count"]
        .sum()
        .fillna(0)
    )

    merged_df = all_states_df.merge(df_agg, on="State", how="left").fillna(0)
    merged_df["Crime Count"] = merged_df["Crime Count"].astype(int)

    # Dynamic title
    title = f"Crime Data for {year_filter}"
    if month_filter != "All":
        title += f" - Month {month_filter}"
    if crime_filter != "All":
        title += f" ({crime_filter})"
    else:
        title += " (All Crimes)"

    # Create map
    fig = px.choropleth(
        merged_df,
        geojson=india_states,
        locations='State',
        featureidkey='properties.NAME_1',
        color='Crime Count',
        color_continuous_scale='Reds',
        title=title,
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=650
    )

    st.plotly_chart(fig, use_container_width=True)
    st.success("Map updated ")
else:
    st.info("Select filters and click **Update Map** to load visualization.")
