import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from pathlib import Path
import joblib
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Fast India Crime Map", layout="wide", page_icon="../stock/logo.png"
)

project_root = Path(os.getcwd()).resolve().parent


# Load saved Models & Files
@st.cache_resource
def load_models_data():
    model_path = project_root / "models"
    svr = joblib.load(model_path / "svr_model.pkl")
    state_enc = joblib.load(model_path / "state_encoder.pkl")
    crime_enc = joblib.load(model_path / "crime_encoder.pkl")

    csv_loc = project_root / "data" / "processed" / "crime_data_processed.csv"
    df = pd.read_csv(csv_loc)

    # Ensuring Field is numeric
    df["Crime Count"] = pd.to_numeric(df["Crime Count"], errors="coerce").fillna(0)

    history_df = df[df["Year"] <= 2023].copy()
    history_df = history_df.sort_values(["State", "Crime Description", "Year", "Month"])

    geojson_loc = project_root / "json" / "cleaned.geojson"
    with open(geojson_loc, "r") as f:
        india_states = json.load(f)

    all_states = [
        feature["properties"]["NAME_1"] for feature in india_states["features"]
    ]
    all_states_df = pd.DataFrame({"State": all_states})
    return svr, state_enc, crime_enc, history_df, df, india_states, all_states_df


# ============================
try:
    svr, state_enc, crime_enc, history_df_base, df, india_states, all_states_df = (
        load_models_data()
    )
except:
    st.error("Models not found. Make sure you ran the training script!")
    st.stop()
# ============================
# Ensure cache with data
if "forecast_cache" not in st.session_state:
    st.session_state.forecast_cache = history_df_base.copy()
    st.session_state.last_generated_year = 2023
# ============================


def visualization():
    st.title("India Crime Data Visualization")

    # Define the input fields
    with st.form("filters_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            year_filter = st.selectbox("Year", sorted(df["Year"].unique()), index=0)
        with col2:
            months = sorted(df["Month"].unique())
            month_filter = st.selectbox(
                "Month", ["All"] + [str(m) for m in months], index=0
            )
        with col3:
            crimes = sorted(df["Crime Description"].unique())
            crime_filter = st.selectbox("Crime Type", ["All"] + crimes, index=0)
        submitted = st.form_submit_button("Update Map")

    df["Crime Count"] = pd.to_numeric(df["Crime Count"], errors="coerce").fillna(0)

    # OnSubmit Filter data from Dataset
    if submitted:
        df_filtered = df[df["Year"] == year_filter]

        if month_filter != "All":
            df_filtered = df_filtered[df_filtered["Month"] == int(month_filter)]

        if crime_filter != "All":
            df_filtered = df_filtered[df_filtered["Crime Description"] == crime_filter]

        df_agg = (
            df_filtered.groupby("State", as_index=False)["Crime Count"].sum().fillna(0)
        )

        merged_df = all_states_df.merge(df_agg, on="State", how="left").fillna(0)
        merged_df["Crime Count"] = merged_df["Crime Count"].astype(int)

        title = f"Crime Data for {year_filter}"
        if month_filter != "All":
            title += f" - Month {month_filter}"
        if crime_filter != "All":
            title += f" ({crime_filter})"
        else:
            title += " (All Crimes)"

        fig = px.choropleth(
            merged_df,
            geojson=india_states,
            locations="State",
            featureidkey="properties.NAME_1",
            color="Crime Count",
            color_continuous_scale="Reds",
            title=title,
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)

        st.plotly_chart(fig, use_container_width=True)
        st.success("Map updated ")
    else:
        st.info("Select filters and click **Update Map** to load visualization.")


# ============================
#   Prediction / Forecasting Generator
def ensure_forecast_exists(target_year):
    """
    Since SVR treats time series as a regression problem, it requires context from the recent past
    to understand the current trend. Lags provide 'short-term memory', allowing 
    the model to predict the next value based on immediate history rather than just the general monthly average.
    """
    current_max = st.session_state.last_generated_year
    if target_year <= current_max:
        return
    years_to_gen = range(current_max + 1, target_year + 1)
    progress_text = "Forecasting timelines... Please wait."
    my_bar = st.progress(0, text=progress_text)

    cache = st.session_state.forecast_cache.copy()
    unique_combos = history_df_base[["State", "Crime Description"]].drop_duplicates()

    # Generate a year more than the selected, for faster access of data if needed.
    for year in years_to_gen:
        for month in range(1, 13):
            this_month_input = unique_combos.copy()
            this_month_input["Year"] = year
            this_month_input["Month"] = month
            this_month_input["Crime Count"] = 0

            temp_df = pd.concat([cache, this_month_input], ignore_index=True)

            # Force numeric type to prevent DataError in rolling mean
            temp_df["Crime Count"] = pd.to_numeric(
                temp_df["Crime Count"], errors="coerce"
            ).fillna(0)

            temp_df = temp_df.sort_values(
                ["State", "Crime Description", "Year", "Month"]
            )

            grouper = temp_df.groupby(["State", "Crime Description"])["Crime Count"]


            temp_df["Lag_1"] = grouper.shift(1)
            temp_df["Lag_3"] = grouper.shift(3)
            temp_df["Rolling_Mean_3"] = grouper.transform(
                lambda x: x.shift(1).rolling(3).mean()
            )

            X_pred = temp_df[
                (temp_df["Year"] == year) & (temp_df["Month"] == month)
            ].copy()

            features = [
                "State",
                "Year",
                "Month",
                "Crime Description",
                "Lag_1",
                "Lag_3",
                "Rolling_Mean_3",
            ]
            X_pred[features] = X_pred[features].fillna(0)

            try:

                preds = svr.predict(X_pred[features])
                preds = [max(0, int(round(p))) for p in preds]
                X_pred["Crime Count"] = preds
                cols_to_keep = [
                    "State",
                    "Crime Description",
                    "Year",
                    "Month",
                    "Crime Count",
                ]
                # Storing the data to cache.
                cache = pd.concat([cache, X_pred[cols_to_keep]], ignore_index=True)

            except Exception as e:
                st.error(f"Prediction Error: {e}")
                st.stop()

    my_bar.empty()
    st.session_state.forecast_cache = cache
    st.session_state.last_generated_year = target_year
    # st.success(f"Forecast for {target_year - 1}  generated successfully")
    st.success(f"Forecast generated successfully")


# ==================================


# Get Next 3,6, 12 month prediction from current selection
def get_long_term_forecast_from_cache(state, start_year, start_month, crime_type):
    end_year = start_year + 1
    ensure_forecast_exists(end_year)

    cache = st.session_state.forecast_cache

    mask = cache["State"] == state
    if crime_type != "All Crimes":
        mask &= cache["Crime Description"] == crime_type

    df_state = cache[mask].copy()

    df_state["Date"] = pd.to_datetime(df_state[["Year", "Month"]].assign(Day=1))
    start_date = pd.to_datetime(f"{start_year}-{start_month}-01")

    end_q = start_date + pd.DateOffset(months=3)
    q_val = df_state[(df_state["Date"] >= start_date) & (df_state["Date"] < end_q)][
        "Crime Count"
    ].sum()

    end_h = start_date + pd.DateOffset(months=6)
    h_val = df_state[(df_state["Date"] >= start_date) & (df_state["Date"] < end_h)][
        "Crime Count"
    ].sum()

    end_y = start_date + pd.DateOffset(months=12)
    y_val = df_state[(df_state["Date"] >= start_date) & (df_state["Date"] < end_y)][
        "Crime Count"
    ].sum()

    return int(q_val), int(h_val), int(y_val)


# Pre
def show_crime_prediction():
    st.title("India Crime Data Forecasting")

    tab1, tab2 = st.tabs(["Prediction Dashboard", "Heatmap Analysis"])

    # ==== 1: PREDICTION DASHBOARD =====
    with tab1:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Select Parameters")

            # Default options set via index
            all_states = state_enc.classes_
            selected_state = st.selectbox("Select State", all_states, index=0)

            col_y, col_m = st.columns(2)
            selected_year = col_y.number_input(
                "Year", min_value=2024, max_value=2030, value=2025
            )
            selected_month = col_m.selectbox(
                "Month",
                range(1, 13),
                index=0,  # Default to January
                format_func=lambda x: pd.to_datetime(f"2022-{x}-01").strftime("%B"),
            )

            all_crime_types = list(crime_enc.classes_)
            all_crime_types.insert(0, "All Crimes")
            selected_crime = st.selectbox("Crime Type", all_crime_types, index=0)

            run_pred = st.button("Generate Prediction", type="primary")

        with col2:
            if run_pred:
                if selected_year >= 2026:
                    st.warning(
                        "**Warning**: Predicting > 2 years ahead of 2023 relies on recursive estimation my have uncertainity.",
                        icon="⚠️",
                    )

                ensure_forecast_exists(selected_year + 1)

                cache = st.session_state.forecast_cache
                mask = (
                    (cache["Year"] == selected_year)
                    & (cache["Month"] == selected_month)
                    & (cache["State"] == selected_state)
                )

                if selected_crime != "All Crimes":
                    mask &= cache["Crime Description"] == selected_crime

                df_pred = cache[mask].copy()

                if not df_pred.empty:
                    st.subheader(
                        f"Forecast: {selected_state} ({pd.to_datetime(f'2022-{selected_month}-01').strftime('%B')} {selected_year})"
                    )

                    month_total = df_pred["Crime Count"].sum()

                    if not df_pred.empty:
                        top_crime = df_pred.loc[df_pred["Crime Count"].idxmax()][
                            "Crime Description"
                        ]
                    else:
                        top_crime = "N/A"

                    m1, m2 = st.columns(2)
                    m1.metric(label="Total Predicted Crimes", value=int(month_total))
                    m2.metric(label="Most Frequent Crime", value=top_crime)

                    df_display = df_pred[["Crime Description", "Crime Count"]].rename(
                        columns={
                            "Crime Description": "Crime Type",
                            "Crime Count": "Count",
                        }
                    )
                    df_display = df_display[df_display["Count"] > 0].sort_values(
                        by="Count", ascending=False
                    )

                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                    csv_data = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=" Download Results as CSV",
                        data=csv_data,
                        file_name=f"prediction_{selected_state}_{selected_year}_{selected_month}.csv",
                        mime="text/csv",
                    )
                    st.divider()
                    st.subheader(f"Long-Term Forecast ({selected_state})")

                    with st.spinner("Analyzing future trends..."):

                        q_val, h_val, y_val = get_long_term_forecast_from_cache(
                            selected_state,
                            selected_year,
                            selected_month,
                            selected_crime,
                        )

                    c1, c2, c3 = st.columns(3)
                    # The Future Pred is SUM (Aggretation count) of next 3,6,12 months from current DATE
                    c1.metric("Next 3 Months (Quarter)", f"{q_val} crimes")
                    c2.metric("Next 6 Months (Half-Year)", f"{h_val} crimes")
                    c3.metric("Next 1 Year (Annual)", f"{y_val} crimes")

                else:
                    st.error("No data found for this selection.")

    # ===== 2: HEATMAP ANALYSIS =====
    with tab2:
        st.subheader("State-wise Crime Intensity Heatmap")

        h_col1, h_col2 = st.columns([1, 3])

        with h_col1:
            h_year = st.number_input("Heatmap Year", 2024, 2030, 2025, key="h_year")
            h_month = st.selectbox("Heatmap Month", range(1, 13), key="h_month")
            h_crime = st.selectbox("Crime Type to Map", all_crime_types, key="h_crime")
            gen_map = st.button("Update Heatmap")

        with h_col2:
            if gen_map:
                if h_year > 2026:
                    st.warning("High Uncertainty: Long-term forecast active.")

                ensure_forecast_exists(h_year)

                cache = st.session_state.forecast_cache
                mask = (cache["Year"] == h_year) & (cache["Month"] == h_month)

                if h_crime != "All Crimes":
                    mask &= cache["Crime Description"] == h_crime

                map_data = (
                    cache[mask].groupby("State", as_index=False)["Crime Count"].sum()
                )

                merged_df = all_states_df.merge(
                    map_data, on="State", how="left"
                ).fillna(0)

                fig = px.choropleth(
                    merged_df,
                    geojson=india_states,
                    locations="State",
                    featureidkey="properties.NAME_1",
                    color="Crime Count",
                    color_continuous_scale="RdYlGn_r",
                    title=f"Crime Intensity: {h_crime} ({h_month}/{h_year})",
                )
                fig.update_geos(fitbounds="locations", visible=False)
                fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=650)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("View Raw Data"):
                    st.dataframe(map_data.sort_values("Crime Count", ascending=False))


def main():

    pg = st.navigation(
        [
            st.Page(visualization, title="Data Visualization"),
            st.Page(show_crime_prediction, title="Crime Prediction Model"),
        ]
    )

    pg.run()


if __name__ == "__main__":
    main()
