import threading

import requests
from flask import Flask, request, jsonify
from google.protobuf.json_format import MessageToDict
from requests_oauthlib import OAuth1

import product_compatibility_partition_pb2

# Initialize Flask app
app = Flask(__name__)

# Global cache
cached_json_data = None
cached_version = None
lock = threading.Lock()  # Prevent race conditions when updating cache

import os


# Load credentials from `credential.properties` or environment variables
def load_credentials(file_path="credential.properties"):
    credentials = {}

    # Try to read from file
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    credentials[key.strip()] = value.strip()

    # Load from environment variables if available
    return {
        "here.token.endpoint.url": credentials.get("here.token.endpoint.url", os.getenv("HERE_TOKEN_URL")),
        "here.access.key.id": credentials.get("here.access.key.id", os.getenv("HERE_CLIENT_ID")),
        "here.access.key.secret": credentials.get("here.access.key.secret", os.getenv("HERE_CLIENT_SECRET"))
    }


# Load HERE API credentials
CREDENTIALS = load_credentials()
OAUTH2_URL = CREDENTIALS["here.token.endpoint.url"]
CLIENT_ID = CREDENTIALS["here.access.key.id"]
CLIENT_SECRET = CREDENTIALS["here.access.key.secret"]

# Load HERE API credentials
CREDENTIALS = load_credentials()
OAUTH2_URL = CREDENTIALS["here.token.endpoint.url"]
CLIENT_ID = CREDENTIALS["here.access.key.id"]
CLIENT_SECRET = CREDENTIALS["here.access.key.secret"]

CATALOG_HRN = "hrn:here:data::olp-here:rib-product-compatibility-1"
BASE_URL = "https://mabcd.metadata.data.api.platform.here.com/metadata/v1/catalogs"
BLOBSTORE_URL = "https://mabcd.blob.data.api.platform.here.com/blobstore/v1/catalogs"


# 1. Get OAuth2 Token
def get_oauth_token():
    oauth = OAuth1(client_key=CLIENT_ID, client_secret=CLIENT_SECRET, signature_type='auth_header')
    r = requests.post(OAUTH2_URL, data=dict(grant_type="client_credentials"),
                      auth=oauth,
                      headers={'Content-Type': 'application/x-www-form-urlencoded'})

    if r.status_code == 200:
        token = r.json()["access_token"]
        print(token)
        return token
    else:
        raise Exception(f"OAuth2 Token error: {r.text}")


# 2. Get latest catalog version
def get_latest_catalog_version(token):
    url = f"{BASE_URL}/{CATALOG_HRN}/versions/latest?startVersion=0"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["version"]
    else:
        raise Exception(f"Failed to fetch catalog version: {response.text}")


# 3. Get latest layer version
def get_layer_versions(token, catalog_version):
    url = f"{BASE_URL}/{CATALOG_HRN}/layerVersions?version={catalog_version}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        layers = response.json()["layerVersions"]
        for layer in layers:
            if layer["layer"] == "versions":
                return layer["version"]
    else:
        raise Exception(f"Failed to fetch layer version: {response.text}")


# 4. Get partition data handle
def get_data_handle(token, layer_version):
    url = f"{BASE_URL}/{CATALOG_HRN}/layers/versions/partitions?version={layer_version}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        partitions = response.json()["partitions"]
        for partition in partitions:
            if partition["layer"] == "versions":
                return partition["dataHandle"]
    else:
        raise Exception(f"Failed to fetch DataHandle: {response.text}")


# 6. Fetch and parse PBF in memory
def fetch_pbf_and_cache():
    global cached_json_data, cached_version
    token = get_oauth_token()
    latest_version = get_latest_catalog_version(token)

    with lock:
        if cached_version == latest_version:
            print(f"Using cached version: {cached_version}")
            return

        print(f"Updating cache: New version {latest_version} detected.")
        layer_version = get_layer_versions(token, latest_version)
        data_handle = get_data_handle(token, layer_version)

        # Get PBF data directly in memory
        url = f"{BLOBSTORE_URL}/{CATALOG_HRN}/layers/versions/data/{data_handle}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            partition_data = product_compatibility_partition_pb2.VersionsPartition()
            partition_data.ParseFromString(response.content)

            cached_json_data = MessageToDict(partition_data, preserving_proto_field_name=True)
            cached_version = latest_version
        else:
            raise Exception(f"Failed to download and parse PBF: {response.text}")


# 7. Cache update function
def update_cache():
    global cached_json_data, cached_version
    token = get_oauth_token()
    latest_version = get_latest_catalog_version(token)

    with lock:
        if cached_version == latest_version:
            print(f"Using cached version: {cached_version}")
            return

        print(f"Updating cache: New version {latest_version} detected.")
        layer_version = get_layer_versions(token, latest_version)
        data_handle = get_data_handle(token, layer_version)
        # pbf_file = download_pbf(token, data_handle)

        # cached_json_data = parse_pbf_to_json(pbf_file)
        cached_version = latest_version


# 8. Lookup version by `hmc_version`
def lookup_version(hmc_version, region=None):
    if region is not None:
        region = region.upper()
    if cached_json_data is None:
        return {"error": "Data is not available yet. Try again later."}

    results = []
    for entry in cached_json_data.get("compatibility", []):
        entry_region = entry["region"]
        entry_dvn = entry["dvn"]

        if region and entry_region != region:
            continue

        for catalog in entry.get("catalogs", []):
            min_v = catalog.get("min_version", 0)
            max_v = catalog.get("max_version", float("inf"))

            if hmc_version == min_v or hmc_version == max_v:
                results.append({"region": entry_region, "dvn": entry_dvn})
            elif min_v <= hmc_version <= max_v:
                results.append({"region": entry_region, "dvn": entry_dvn})

    if results:
        return {"hmc_version": hmc_version, "rmob_region": region, "matches": results}
    return {"hmc_version": hmc_version, "rmob_region": region, "message": "No matching version found"}


# 9. Reverse lookup by `dvn`
def reverse_lookup_version(dvn, region=None):
    if region is not None:
        region = region.upper()
    if cached_json_data is None:
        return {"error": "Data is not available yet. Try again later."}


    results = []
    for entry in cached_json_data.get("compatibility", []):
        entry_region = str(entry["region"]).upper()
        entry_dvn = entry["dvn"]

        if entry_dvn == dvn and (region is None or entry_region == region):
            for catalog in entry.get("catalogs", []):
                results.append({
                    "region": entry_region,
                    "dvn": entry_dvn,
                    "catalog_type": catalog["catalog_type"],
                    "hrn": catalog["hrn"],
                    "min_version": catalog.get("min_version", None),
                    "max_version": catalog.get("max_version", None)
                })

    if results:
        return {"dvn": dvn, "versions": results}
    return {"dvn": dvn, "message": "No matching versions found"}


# API: Lookup version
@app.route("/lookup", methods=["GET"])
def api_lookup():
    hmc_version = request.args.get("hmc_version", type=int)
    region = request.args.get("rmob_region", type=str)  # Optional

    if hmc_version is None:
        return jsonify({"error": "Missing required parameter: hmc_version"}), 400

    fetch_pbf_and_cache()

    lookup_result = lookup_version(hmc_version, region)
    return jsonify(lookup_result)


# API: Reverse lookup
@app.route("/reverse-lookup", methods=["GET"])
def api_reverse_lookup():
    dvn = request.args.get("dvn", type=str)
    region = request.args.get("rmob_region", type=str)  # Optional

    if not dvn:
        return jsonify({"error": "Missing required parameter: dvn"}), 400

    fetch_pbf_and_cache()

    lookup_result = reverse_lookup_version(dvn, region)
    return jsonify(lookup_result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Healthy"}), 200

@app.route('/', methods=['GET'])
def root():
    return 'https://github.com/aquawill/hmc_rmob_version_lookup', 200

# Start Flask server with cache initialization
if __name__ == "__main__":
    print("Initializing cache...")
    fetch_pbf_and_cache()  # Fetch PBF data on startup
    app.run(host="0.0.0.0", port=10000, debug=True)
