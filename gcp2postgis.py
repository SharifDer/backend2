#!/usr/bin/env python3
import os
import json
from google.cloud import storage
import geopandas as gpd
from sqlalchemy import create_engine
import re
import io

# ----------------------------
# CONFIGURATION
# ----------------------------
GCP_BUCKET = "dev-s-locator"
POPULATION_PATH = "postgreSQL/dbo_operational/raw_schema_marketplace/population/"
AREA_INCOME_PATH = "postgreSQL/dbo_operational/raw_schema_marketplace/interpolated_riyadh/"
# Use the provided secrets file for DB config
DB_CONFIG_FILE = "secrets/postgres_db.json"  # Path to JSON file with DB credentials
# ----------------------------
# FUNCTIONS
# ----------------------------

def load_db_config(json_path):
    """Load DB connection details from JSON file."""
    with open(json_path, "r") as f:
        return json.load(f)

def get_latest_dir(bucket, base_path):
    """Return the latest date directory under the given GCS base path."""
    blobs = bucket.list_blobs(prefix=base_path)
    date_pattern = re.compile(rf"^{re.escape(base_path)}(\d{{8}})/")
    dates_found = set()

    for blob in blobs:
        match = date_pattern.match(blob.name)
        if match:
            dates_found.add(match.group(1))

    if not dates_found:
        raise ValueError(f"No date directories found under {base_path}")

    latest_date = max(dates_found)
    return f"{base_path}{latest_date}/"

def table_name_from_blob(blob_name):
    """Extract table name from blob."""
    parts = blob_name.split("/")
    filename = os.path.splitext(parts[-1])[0]
    version = parts[-2]
    return f"{filename}_{version}"

def import_geojson_to_postgis(bucket, gcs_path, table_name, engine):
    """Download latest geojson files from GCS and load into PostGIS."""
    dataset_type = table_name
    latest_prefix = get_latest_dir(bucket, gcs_path)
    if not latest_prefix:
        print(f"No data found for {table_name}")
        return
    latest_prefix = latest_prefix + table_name
    print(f"Latest path: {latest_prefix}")

    blobs = bucket.list_blobs(prefix=latest_prefix)
    for blob in blobs:
        if blob.name.endswith(".geojson"):
            geojson_bytes = blob.download_as_bytes()
            gdf = gpd.read_file(io.BytesIO(geojson_bytes))
            table_name = table_name_from_blob(blob.name)
            if 'population' in dataset_type and 'population' not in table_name:
                table_name = 'population_' + table_name
            elif 'area' in dataset_type:
                table_name = 'area_income_' + table_name
            gdf.to_postgis(table_name, engine, if_exists="replace", chunksize=500)
            print(f"Loaded {blob.name} --> PostGIS table '{table_name}'")

    print(f"Completed import for {dataset_type}")

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ggl_bucket_sa.json"

    # Load DB credentials from JSON
    db_conf = load_db_config(DB_CONFIG_FILE)

    # Connect to GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCP_BUCKET)

    # Use DATABASE_URL from config for SQLAlchemy engine
    db_url = db_conf["DATABASE_URL"]
    # If using psycopg2, ensure the URL is compatible
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(db_url)

    # Import datasets
    import_geojson_to_postgis(bucket, POPULATION_PATH, "population_json_files/", engine)
    import_geojson_to_postgis(bucket, AREA_INCOME_PATH, "area_income_geojson/", engine)

    print("All imports completed successfully!")