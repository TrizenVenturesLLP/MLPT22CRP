import os
import shutil
import joblib
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from pathlib import Path
from sklearn.cluster import KMeans
from flask_cors import CORS
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

app = Flask(__name__)

# Enable CORS for frontend (Vercel prod + preview) on /api/*
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "https://mlpt-22-crp.vercel.app",
            ]
        }
    },
)

project_root = Path(__file__).parent.resolve()

regressor = None
classifier = None
state_enc = None
district_enc = None
crime_enc = None
history_df_base = None
full_df = None
all_crime_types = []
models_loaded = False
models_error = None
config_loaded = False
config_error = None

# Hugging Face Hub (handles auth, LFS / xet; plain HTTP often returns 401 for large files)
HF_TREND_REPO_ID = os.environ.get("HF_TREND_REPO_ID", "Tarun516/trend-classifier")
HF_TREND_FILENAME = os.environ.get("HF_TREND_FILENAME", "trend_classifier.pkl")
_raw_hf = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
HF_TOKEN = None
if _raw_hf:
    _t = _raw_hf.strip()
    if _t:
        HF_TOKEN = _t
TREND_LOCAL_PATH = Path("/tmp/trend_classifier.pkl")


def _patch_monotonic(model):
    if hasattr(model, "estimators_"):
        for est in model.estimators_:
            if not hasattr(est, "tree_"):
                continue
            if not hasattr(est, "monotonic_cst"):
                est.monotonic_cst = None
    elif hasattr(model, "tree_"):
        if not hasattr(model, "monotonic_cst"):
            model.monotonic_cst = None


def load_config_data():
    global state_enc, district_enc, crime_enc, full_df, history_df_base, all_crime_types

    model_path = project_root / "models"
    state_enc = joblib.load(model_path / "state_encoder.pkl")
    district_enc = joblib.load(model_path / "district_encoder.pkl")
    crime_enc = joblib.load(model_path / "crime_encoder.pkl")

    csv_loc = project_root / "data" / "processed" / "crime_data_district_long.csv"
    df = pd.read_csv(csv_loc)
    df = df[df["Crime Description"] != "TOTAL IPC CRIMES"].copy()
    df["Crime Count"] = pd.to_numeric(df["Crime Count"], errors="coerce").fillna(0)

    full_df = df
    history_df_base = df[df["Year"] <= 2012].copy().sort_values(
        ["State", "District", "Crime Description", "Year"]
    )
    all_crime_types = list(crime_enc.classes_)
    all_crime_types.insert(0, "All Crimes")


def ensure_config_loaded():
    global config_loaded, config_error
    if config_loaded:
        return True
    try:
        load_config_data()
        config_loaded = True
        config_error = None
        return True
    except Exception as e:
        config_error = str(e)
        print(f"Error loading config data: {e}")
        return False


def ensure_models_loaded():
    global regressor, classifier, models_loaded, models_error
    if models_loaded:
        return True
    if not ensure_config_loaded():
        models_error = config_error
        return False
    try:
        model_path = project_root / "models"
        regressor = joblib.load(model_path / "model.pkl")
        # Trend classifier is stored on Hugging Face; download once per instance
        if not TREND_LOCAL_PATH.exists():
            print(
                f"Downloading {HF_TREND_FILENAME} from Hugging Face repo {HF_TREND_REPO_ID} ..."
            )
            try:
                cached = hf_hub_download(
                    repo_id=HF_TREND_REPO_ID,
                    filename=HF_TREND_FILENAME,
                    token=HF_TOKEN,
                )
                shutil.copy2(cached, TREND_LOCAL_PATH)
            except HfHubHTTPError as e:
                if getattr(e, "response", None) is not None and e.response.status_code == 401:
                    raise RuntimeError(
                        "Hugging Face returned 401 Unauthorized. "
                        "Set HF_TOKEN (or HUGGING_FACE_HUB_TOKEN) on this service with a valid "
                        "token from https://huggingface.co/settings/tokens , then redeploy. "
                        "If the repo is public, ensure the token has read access to your namespace. "
                        "Using huggingface_hub (not raw HTTP) fixes many LFS/xet auth issues."
                    ) from e
                raise
        print("Loading trend_classifier from local cache...")
        classifier = joblib.load(TREND_LOCAL_PATH)
        _patch_monotonic(regressor)
        _patch_monotonic(classifier)
        models_loaded = True
        models_error = None
        return True
    except Exception as e:
        models_error = str(e)
        print(f"Error loading prediction models: {e}")
        return False


def generate_localized_forecast(target_year, state, district, crime_type):
    mask = (history_df_base["State"] == state) & (history_df_base["District"] == district)
    if crime_type != "All Crimes":
        mask &= (history_df_base["Crime Description"] == crime_type)
        
    local_df = history_df_base[mask].copy()
    if local_df.empty:
        return pd.DataFrame()

    unique_crimes = local_df["Crime Description"].unique()

    s_enc = state_enc.transform([state])[0]
    d_enc = district_enc.transform([district])[0]

    for year in range(2013, target_year + 1):
        # Create input rows for the current year
        new_rows = []
        for cdesc in unique_crimes:
            new_rows.append({
                "State": state,
                "District": district,
                "Crime Description": cdesc,
                "Year": year,
                "Crime Count": 0 
            })
        
        local_df = pd.concat([local_df, pd.DataFrame(new_rows)], ignore_index=True)
        local_df = local_df.sort_values(["Crime Description", "Year"])

        grouper = local_df.groupby(["Crime Description"])["Crime Count"]
        
        local_df["Lag_1"] = grouper.shift(1)
        local_df["Lag_2"] = grouper.shift(2)
        local_df["Lag_3"] = grouper.shift(3)
        local_df["Lag_4"] = grouper.shift(4)
        
        local_df["Rolling_Mean_2"] = grouper.transform(lambda x: x.shift(1).rolling(2).mean())
        local_df["Rolling_Mean_3"] = grouper.transform(lambda x: x.shift(1).rolling(3).mean())
        local_df["Rolling_Mean_4"] = grouper.transform(lambda x: x.shift(1).rolling(4).mean())

        X_pred = local_df[local_df["Year"] == year].copy()
        
        X_pred["State_Enc"] = s_enc
        X_pred["District_Enc"] = d_enc
        X_pred["Crime_Enc"] = crime_enc.transform(X_pred["Crime Description"])

        features = [
            "State_Enc", "District_Enc", "Crime_Enc", "Year",
            "Lag_1", "Lag_2", "Lag_3", "Lag_4",
            "Rolling_Mean_2", "Rolling_Mean_3", "Rolling_Mean_4"
        ]
        
        X_pred[features] = X_pred[features].fillna(0)
        
        preds = regressor.predict(X_pred[features])
        trend_preds = classifier.predict(X_pred[features])
        
        final_preds = []
        for p, t, lag1 in zip(preds, trend_preds, X_pred["Lag_1"]):
            p = max(0, int(round(p)))
            lag1 = max(0, int(round(lag1))) if pd.notna(lag1) else 0
            if t == 1 and p <= lag1:
                # Force a small dynamic increase
                increase_amt = max(1, int(lag1 * 0.05))
                final_preds.append(lag1 + increase_amt)
            elif t == 0 and p > lag1:
                # Force a small dynamic decrease
                decrease_amt = max(1, int(lag1 * 0.05))
                final_preds.append(max(0, lag1 - decrease_amt))
            else:
                final_preds.append(p)
                
        local_df.loc[local_df["Year"] == year, "Crime Count"] = final_preds
        local_df.loc[local_df["Year"] == year, "Trend_Increase"] = trend_preds
        
    return local_df

def forecast_state_hotspots(target_end_year, state):
    # This is a bulk version of generate_localized_forecast
    mask = (history_df_base["State"] == state)
    local_df = history_df_base[mask].copy()
    if local_df.empty:
        return pd.DataFrame()

    unique_districts = local_df["District"].unique()
    unique_crimes = local_df["Crime Description"].unique()

    s_enc = state_enc.transform([state])[0]
    # Create mapping for district encoders to speed up
    d_enc_map = {d: district_enc.transform([d])[0] for d in unique_districts}

    # Initial year for forecasting
    for year in range(2013, target_end_year + 1):
        new_rows = []
        for dist in unique_districts:
            for cdesc in unique_crimes:
                new_rows.append({
                    "State": state,
                    "District": dist,
                    "Crime Description": cdesc,
                    "Year": year,
                    "Crime Count": 0 
                })
        
        local_df = pd.concat([local_df, pd.DataFrame(new_rows)], ignore_index=True)
        local_df = local_df.sort_values(["District", "Crime Description", "Year"])

        grouper = local_df.groupby(["District", "Crime Description"])["Crime Count"]
        
        local_df["Lag_1"] = grouper.shift(1)
        local_df["Lag_2"] = grouper.shift(2)
        local_df["Lag_3"] = grouper.shift(3)
        local_df["Lag_4"] = grouper.shift(4)
        
        local_df["Rolling_Mean_2"] = grouper.transform(lambda x: x.shift(1).rolling(2).mean())
        local_df["Rolling_Mean_3"] = grouper.transform(lambda x: x.shift(1).rolling(3).mean())
        local_df["Rolling_Mean_4"] = grouper.transform(lambda x: x.shift(1).rolling(4).mean())

        mask_year = local_df["Year"] == year
        X_pred = local_df[mask_year].copy()
        
        X_pred["State_Enc"] = s_enc
        X_pred["District_Enc"] = X_pred["District"].map(d_enc_map)
        X_pred["Crime_Enc"] = crime_enc.transform(X_pred["Crime Description"])

        features = [
            "State_Enc", "District_Enc", "Crime_Enc", "Year",
            "Lag_1", "Lag_2", "Lag_3", "Lag_4",
            "Rolling_Mean_2", "Rolling_Mean_3", "Rolling_Mean_4"
        ]
        
        X_pred[features] = X_pred[features].fillna(0)
        
        preds = regressor.predict(X_pred[features])
        trend_preds = classifier.predict(X_pred[features])
        
        final_preds = []
        for p, t, lag1 in zip(preds, trend_preds, X_pred["Lag_1"]):
            p = max(0, int(round(p)))
            lag1 = max(0, int(round(lag1))) if pd.notna(lag1) else 0
            if t == 1 and p <= lag1:
                increase_amt = max(1, int(lag1 * 0.05))
                final_preds.append(lag1 + increase_amt)
            elif t == 0 and p > lag1:
                decrease_amt = max(1, int(lag1 * 0.05))
                final_preds.append(max(0, lag1 - decrease_amt))
            else:
                final_preds.append(p)
                
        local_df.loc[mask_year, "Crime Count"] = final_preds
        
    return local_df

@app.route("/")
def index():
    return "models loaded and backend is working"

@app.route("/api/config", methods=["GET"])
def get_config():
    if not ensure_config_loaded():
        return jsonify({"error": f"Config failed to load: {config_error}"}), 500

    states = sorted(list(state_enc.classes_))
    # Map state to its districts based on our dataset
    state_district_map = {}
    for st in states:
        districts_in_state = sorted(full_df[full_df["State"] == st]["District"].unique().tolist())
        state_district_map[st] = districts_in_state

    return jsonify({
        "states": states,
        "state_district_map": state_district_map,
        "crimes": all_crime_types
    })

@app.route("/api/predict", methods=["POST"])
def predict():
    if not ensure_models_loaded():
        return jsonify({"error": f"Prediction models failed to load: {models_error}"}), 500

    data = request.json
    state = data.get("state")
    district = data.get("district")
    year = int(data.get("year", 2024))
    crime = data.get("crime")

    if not all([state, district, year, crime]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        local_preds = generate_localized_forecast(year, state, district, crime)
        
        if local_preds.empty:
            return jsonify({"error": "No historical data found for this combination."}), 404
            
        df_pred = local_preds[local_preds["Year"] == year]
        
        if df_pred.empty:
             return jsonify({"error": "Unreachable prediction state."}), 500

        total_crimes = int(df_pred["Crime Count"].sum())
        
        crime_label = crime if crime != "All Crimes" else "Total Crime"
        
        output_string = f"Predicted {crime_label} Cases in {district} ({year}) = {total_crimes}"
        
        return jsonify({
            "prediction": output_string,
            "count": total_crimes,
            "district": district,
            "year": year,
            "crime_label": crime_label
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/hotspots", methods=["POST"])
def get_hotspots():
    if not ensure_models_loaded():
        return jsonify({"error": f"Prediction models failed to load: {models_error}"}), 500

    data = request.json
    state = data.get("state")
    start_year = int(data.get("start_year", 2015))
    end_year = int(data.get("end_year", 2020))

    if not state:
        return jsonify({"error": "State is required"}), 400

    try:
        fallback_msg = ""
        # Decide whether to use history or forecast
        if end_year <= 2012:
            # Historical range
            mask = (full_df["State"] == state) & (full_df["Year"] >= start_year) & (full_df["Year"] <= end_year)
            mask &= (full_df["Crime Description"] != "TOTAL IPC CRIMES")
            filtered_df = full_df[mask].copy()
        else:
            # Future range, use forecasting
            # Note: start_year might be historical and end_year might be future.
            # For simplicity, if end_year > 2012, we forecast everything.
            forecast_df = forecast_state_hotspots(end_year, state)
            if forecast_df.empty:
                return jsonify({"error": f"Unable to forecast for {state}"}), 500
            
            mask = (forecast_df["Year"] >= start_year) & (forecast_df["Year"] <= end_year)
            mask &= (forecast_df["Crime Description"] != "TOTAL IPC CRIMES")
            filtered_df = forecast_df[mask].copy()
            fallback_msg = " (Predicted based on trends)"

        if filtered_df.empty:
             return jsonify({"error": f"No data found for {state}"}), 404

        # Group by District and sum Crime Count
        district_counts = filtered_df.groupby("District")["Crime Count"].sum().reset_index()
        
        if len(district_counts) < 3:
            # Not enough districts to cluster into 3 levels
            # We can still return them as Medium/Low or just one level
            # For simplicity, we'll assign risk levels based on thresholds if < 3 districts
            results = {"High": [], "Medium": [], "Low": []}
            sorted_districts = district_counts.sort_values("Crime Count", ascending=False)
            for i, row in sorted_districts.iterrows():
                if i == 0: results["High"].append(row["District"])
                elif i == 1: results["Medium"].append(row["District"])
                else: results["Low"].append(row["District"])
            return jsonify(results)

        # Apply K-Means clustering
        X = district_counts["Crime Count"].values.reshape(-1, 1)
        kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
        district_counts["Cluster"] = kmeans.fit_predict(X)

        # Map Clusters to Risk Levels (High, Medium, Low) based on cluster centers
        centers = kmeans.cluster_centers_.flatten()
        idx_sorted = np.argsort(centers) # [low_idx, med_idx, high_idx]
        
        risk_map = {
            idx_sorted[0]: "Low",
            idx_sorted[1]: "Medium",
            idx_sorted[2]: "High"
        }
        
        district_counts["KMeans_Level"] = district_counts["Cluster"].map(risk_map)

        # Hybrid Logic: Apply Absolute Severity Thresholds
        # Thresholds (Average annual crimes): High > 15k, Medium 5k - 15k, Low < 5k
        num_years = max(1, end_year - start_year + 1)
        
        def get_absolute_level(count):
            annual = count / num_years
            if annual >= 15000: return "High"
            if annual >= 5000: return "Medium"
            return "Low"

        district_counts["Absolute_Level"] = district_counts["Crime Count"].apply(get_absolute_level)

        # Combine: Take the higher of the two (High > Medium > Low)
        level_order = {"High": 3, "Medium": 2, "Low": 1}
        def combine_risks(row):
            k_val = level_order[row["KMeans_Level"]]
            a_val = level_order[row["Absolute_Level"]]
            if a_val > k_val:
                return row["Absolute_Level"]
            return row["KMeans_Level"]

        district_counts["Risk Level"] = district_counts.apply(combine_risks, axis=1)

        # Prepare response with ranges
        def get_range(level):
            subset = district_counts[district_counts["Risk Level"] == level]
            if subset.empty: return "N/A"
            return f"{int(subset['Crime Count'].min())} - {int(subset['Crime Count'].max())}"

        # Load coordinates mapping
        coord_file = project_root / "data" / "district_coordinates.json"
        coords_map = {}
        if coord_file.exists():
            import json
            with open(coord_file, 'r') as f:
                coords_map = json.load(f)

        # State centroids for fallback
        state_centroids = {
            "ANDHRA PRADESH": [15.9129, 79.7400],
            "ARUNACHAL PRADESH": [28.2180, 94.7278],
            "ASSAM": [26.2006, 92.9376],
            "BIHAR": [25.0961, 85.3131],
            "CHHATTISGARH": [21.2787, 81.8661],
            "GOA": [15.2993, 74.1240],
            "GUJARAT": [22.2587, 71.1924],
            "HARYANA": [29.0588, 76.0856],
            "HIMACHAL PRADESH": [31.1048, 77.1734],
            "JAMMU & KASHMIR": [33.7782, 76.5762],
            "JHARKHAND": [23.6102, 85.2799],
            "KARNATAKA": [15.3173, 75.7139],
            "KERALA": [10.8505, 76.2711],
            "MADHYA PRADESH": [22.9734, 78.6569],
            "MAHARASHTRA": [19.7515, 75.7139],
            "MANIPUR": [24.6637, 93.9063],
            "MEGHALAYA": [25.4670, 91.3662],
            "MIZORAM": [23.1645, 92.9376],
            "NAGALAND": [26.1584, 94.5624],
            "ODISHA": [20.9517, 85.0985],
            "PUNJAB": [31.1471, 75.3412],
            "RAJASTHAN": [27.0238, 74.2179],
            "SIKKIM": [27.5330, 88.5122],
            "TAMIL NADU": [11.1271, 78.6569],
            "TRIPURA": [23.9408, 91.9882],
            "UTTAR PRADESH": [26.8467, 80.9462],
            "UTTARAKHAND": [30.0668, 79.0193],
            "WEST BENGAL": [22.9868, 87.8550],
            "DELHI UT": [28.6139, 77.2090]
        }

        def get_coords(district, state):
            dist_key = district.upper()
            if dist_key in coords_map:
                return coords_map[dist_key]
            
            # Fallback to state centroid with small random jitter
            state_key = state.upper()
            centroid = state_centroids.get(state_key, [20.5937, 78.9629]) # India centroid
            return [centroid[0] + np.random.uniform(-0.5, 0.5), centroid[1] + np.random.uniform(-0.5, 0.5)]

        def format_records(level):
            subset = district_counts[district_counts["Risk Level"] == level]
            out = []
            for _, row in subset.iterrows():
                coords = get_coords(row["District"], state)
                out.append({
                    "District": row["District"],
                    "Crime Count": int(row["Crime Count"]),
                    "lat": coords[0],
                    "lng": coords[1]
                })
            return out

        results = {
            "High": format_records("High"),
            "Medium": format_records("Medium"),
            "Low": format_records("Low"),
            "ranges": {
                "High": get_range("High"),
                "Medium": get_range("Medium"),
                "Low": get_range("Low")
            },
            "message": f"Hotspots for {state}{fallback_msg}"
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Use PORT provided by Render or default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
