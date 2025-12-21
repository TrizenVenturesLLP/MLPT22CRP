import os
import shutil
import kagglehub
from pathlib import Path

path = kagglehub.dataset_download("sudhanvahg/indian-crimes-dataset")
print(path)

# Define destination inside your project
project_root = Path(os.getcwd()).resolve().parent
project_data_path = project_root  / "crime_forecasting" / "data" / "raw"

# Make sure folder exists
os.makedirs(project_data_path, exist_ok=True)

# Copy dataset contents into project folder
for item in os.listdir(path):
    print(item)
    s = os.path.join(path, item)
    d = os.path.join(project_data_path, item)
    if os.path.isdir(s):
        shutil.copytree(s, d, dirs_exist_ok=True)
    else:
        shutil.copy2(s, d)

print("Dataset copied to:", project_data_path)



import geopandas as gpd

project_root = Path(os.getcwd()).resolve().parent

input_path = project_root / "json" / "india_state.geojson"
output_path = project_root / "json" / "cleaned.geojson"

# Load original geojson
gdf = gpd.read_file(input_path)

# Inspect column names
print(gdf.columns)

# Clean geometry values
gdf["geometry"] = gdf["geometry"].buffer(0)

gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.01, preserve_topology=True)

# Save cleaned file
gdf.to_file(output_path, driver="GeoJSON")

print(" Cleaned file saved with properties intact.")
