import threading

from google.protobuf.json_format import MessageToDict

import api_request_handler
import product_compatibility_partition_pb2

# Global cache
cached_json_data = None
cached_version = None
lock = threading.Lock()  # Prevent race conditions when updating cache

RIB_PRODUCT_COMPATIBILITY_1_CATALOG_HRN = "hrn:here:data::olp-here:rib-product-compatibility-1"
RIB_2_CATALOG_HRN = "hrn:here:data::olp-here:rib-2"
RIB_EXTERNAL_REFERENCE_2_CATALOG_HRN = "hrn:here:data::olp-here:rib-external-references-2"
BASE_URL = "https://mabcd.metadata.data.api.platform.here.com/metadata/v1/catalogs"
BLOBSTORE_URL = "https://mabcd.blob.data.api.platform.here.com/blobstore/v1/catalogs"


def get_latest_catalog_version(catalog_hrn, token):
    url = f"{BASE_URL}/{catalog_hrn}/versions/latest?startVersion=0"
    response = api_request_handler.request_with_token_refresh(url)

    if response.status_code == 200:
        return response.json()["version"]
    else:
        raise Exception(f"Failed to fetch catalog version: {response.text}")


# 3. Get latest layer version
def get_layer_versions(token, catalog_version):
    url = f"{BASE_URL}/{RIB_PRODUCT_COMPATIBILITY_1_CATALOG_HRN}/layerVersions?version={catalog_version}"
    response = api_request_handler.request_with_token_refresh(url)

    if response.status_code == 200:
        layers = response.json()["layerVersions"]
        for layer in layers:
            if layer["layer"] == "versions":
                return layer["version"]
    else:
        raise Exception(f"Failed to fetch layer version: {response.text}")


# 4. Get partition data handle
def get_data_handle(token, layer_version):
    url = f"{BASE_URL}/{RIB_PRODUCT_COMPATIBILITY_1_CATALOG_HRN}/layers/versions/partitions?version={layer_version}"
    response = api_request_handler.request_with_token_refresh(url)

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
    token = api_request_handler.get_oauth_token()
    latest_version = get_latest_catalog_version(RIB_PRODUCT_COMPATIBILITY_1_CATALOG_HRN, token)

    with lock:
        if cached_version == latest_version:
            return

        layer_version = get_layer_versions(token, latest_version)
        data_handle = get_data_handle(token, layer_version)

        # 下載 PBF
        url = f"{BLOBSTORE_URL}/{RIB_PRODUCT_COMPATIBILITY_1_CATALOG_HRN}/layers/versions/data/{data_handle}"
        response = api_request_handler.request_with_token_refresh(url)

        if response.status_code == 200:
            partition_data = product_compatibility_partition_pb2.VersionsPartition()
            partition_data.ParseFromString(response.content)

            cached_json_data = MessageToDict(partition_data, preserving_proto_field_name=True)
            cached_version = latest_version
        else:
            raise Exception(f"Failed to download and parse PBF: {response.text}")


def get_rmob_dvn_query_worker(hmc_version, region=None, target_hrn=None):
    if cached_json_data is None:
        return {"error": "Data is not available yet. Try again later."}
    try:
        hmc_version = int(hmc_version)
    except ValueError:
        if hmc_version == 'latest':
            hmc_version = get_latest_catalog_version(RIB_2_CATALOG_HRN, api_request_handler.get_oauth_token())
    results = []
    for entry in cached_json_data.get("compatibility", []):
        entry_region = entry["region"]
        entry_dvn = entry["dvn"]

        if region and entry_region.upper() != region.upper():
            continue

        for catalog in entry.get("catalogs", []):
            if catalog["catalog_type"] == "HERE_MAP_CONTENT":
                min_v = catalog.get("min_version", 0)
                max_v = catalog.get("max_version", float("inf"))
                catalog_hrn = catalog.get("hrn")
                if not target_hrn:
                    if min_v <= hmc_version <= max_v:
                        results.append({"region": entry_region, "rmob_dvn": entry_dvn})
                if target_hrn:
                    if catalog_hrn == target_hrn:
                        if min_v <= hmc_version <= max_v:
                            results.append({"region": entry_region, "rmob_dvn": entry_dvn})

    return {"catalog_version": hmc_version, "catalog_hrn": catalog_hrn, "matches": results} if results else \
        {"message": "No matching version found",
         "catalog_version": hmc_version}


def get_hmc_dvn_query_worker(dvn, region=None):
    if cached_json_data is None:
        return {"error": "Data is not available yet. Try again later."}

    region_catalog_map = {}

    for entry in cached_json_data.get("compatibility", []):
        entry_region = entry["region"]
        entry_dvn = entry["dvn"]

        if entry_dvn == dvn and (region is None or entry_region.upper() == region.upper()):
            for catalog in entry.get("catalogs", []):
                min_version = catalog.get("min_version")
                max_version = catalog.get("max_version")
                # catalog_hrn = catalog["hrn"]
                # opensearch_matching = opensearch_version_query_service.filter_opensearch_versions_by_hrn(catalog_hrn, min_version, max_version)
                catalog_data = {
                    "catalog_type": catalog["catalog_type"],
                    "hrn": catalog["hrn"],
                    "min_version": min_version,
                    "max_version": max_version,
                    # "opensearch_versions": opensearch_matching
                }

                # 初始化該 region，如果還沒有出現過
                if entry_region not in region_catalog_map:
                    region_catalog_map[entry_region] = {"region": entry_region, "catalogs": []}

                # 加入該 region 的 catalog list
                region_catalog_map[entry_region]["catalogs"].append(catalog_data)

    # 把 dictionary 轉換為 list
    matches_list = list(region_catalog_map.values())

    return {"rmob_dvn": dvn, "matches": matches_list} if matches_list else \
        {"rmob_dvn": dvn, "message": "No matching versions found"}
