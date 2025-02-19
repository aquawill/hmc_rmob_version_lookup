import threading

import requests
from flask import Flask, request, jsonify
from google.protobuf.json_format import MessageToDict
from requests_oauthlib import OAuth1

import auth_service
import product_compatibility_partition_pb2

# Initialize Flask app
app = Flask(__name__)

# Global cache
cached_json_data = None
cached_version = None
lock = threading.Lock()  # Prevent race conditions when updating cache

import os


CATALOG_HRN = "hrn:here:data::olp-here:rib-product-compatibility-1"
BASE_URL = "https://mabcd.metadata.data.api.platform.here.com/metadata/v1/catalogs"
BLOBSTORE_URL = "https://mabcd.blob.data.api.platform.here.com/blobstore/v1/catalogs"



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
    token = auth_service.get_oauth_token()
    latest_version = get_latest_catalog_version(token)

    with lock:
        if cached_version == latest_version:
            return

        layer_version = get_layer_versions(token, latest_version)
        data_handle = get_data_handle(token, layer_version)

        # 下載 PBF
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

def lookup_version(hmc_version, region=None):
    if cached_json_data is None:
        return {"error": "Data is not available yet. Try again later."}

    results = []
    for entry in cached_json_data.get("compatibility", []):
        entry_region = entry["region"]
        entry_dvn = entry["dvn"]

        if region and entry_region.upper() != region.upper():
            continue

        for catalog in entry.get("catalogs", []):
            min_v = catalog.get("min_version", 0)
            max_v = catalog.get("max_version", float("inf"))

            if min_v <= hmc_version <= max_v:
                results.append({"region": entry_region, "dvn": entry_dvn})

    return {"hmc_version": hmc_version, "rmob_region": region, "matches": results} if results else \
        {"hmc_version": hmc_version, "rmob_region": region, "message": "No matching version found"}

def reverse_lookup_version(dvn, region=None):
    if cached_json_data is None:
        return {"error": "Data is not available yet. Try again later."}

    results = []
    for entry in cached_json_data.get("compatibility", []):
        entry_region = entry["region"]
        entry_dvn = entry["dvn"]

        if entry_dvn == dvn and (region is None or entry_region.upper() == region.upper()):
            for catalog in entry.get("catalogs", []):
                results.append({
                    "region": entry_region,
                    "dvn": entry_dvn,
                    "catalog_type": catalog["catalog_type"],
                    "hrn": catalog["hrn"],
                    "min_version": catalog.get("min_version"),
                    "max_version": catalog.get("max_version")
                })

    return {"dvn": dvn, "versions": results} if results else \
        {"dvn": dvn, "message": "No matching versions found"}