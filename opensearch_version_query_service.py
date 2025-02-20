import threading
import time

import requests

import api_request_handler
import rmob_version_query_service

CATALOG_HRN = "hrn:here:data::olp-here:here-optimized-map-for-opensearch-3"
METADATA_URL = "https://sab.metadata.data.api.platform.here.com/metadata/v1/catalogs"
BLOBSTORE_URL = "https://sab.blob.data.api.platform.here.com/blobstore/v1/catalogs"

# Cache 變數與 Lock
CACHE = {
    "latest_version": None,
    "metadata": None
}
CACHE_LOCK = threading.Lock()  # 用於確保 thread safety


def epoch_converter(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(epoch))


def get_latest_catalog_version(token):
    url = f"{METADATA_URL}/{CATALOG_HRN}/versions/latest?startVersion=0"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["version"]
    else:
        raise Exception(f"Failed to fetch catalog version: {response.text}")


def get_earliest_catalog_version(token):
    url = f"{METADATA_URL}/{CATALOG_HRN}/versions/minimum?"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["version"]
    else:
        raise Exception(f"Failed to fetch catalog version: {response.text}")


def get_version_range_metadata(token, earliest_version, latest_version):
    """
    Fetch metadata only if latest_version has changed. Uses threading.Lock() to ensure thread safety.
    """
    global CACHE

    with CACHE_LOCK:  # 確保只有一個執行緒能夠存取與更新 Cache
        if CACHE["latest_version"] == latest_version and CACHE["metadata"] is not None:
            print("🔹 Using cached metadata")
            return CACHE["metadata"]

        url = f"{METADATA_URL}/{CATALOG_HRN}/versions?startVersion={earliest_version}&endVersion={latest_version}&context=super"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            metadata = response.json()
            CACHE["latest_version"] = latest_version  # 更新最新版本
            CACHE["metadata"] = metadata  # 更新 Cache
            print("✅ Cache updated with new metadata")
            return metadata
        else:
            raise Exception(f"Failed to fetch catalog version: {response.text}")


# def filter_opensearch_versions_by_hrn(target_hrn, min_version=None, max_version=None):
#     """
#     Filter metadata to find entries where the target HRN exists in dependencies
#     with a valid version within the specified range.
#
#     :param metadata_list: List of metadata dictionaries.
#     :param min_version: Minimum version number (inclusive).
#     :param max_version: Maximum version number (inclusive).
#     :return: List of dictionaries with version and timestamp.
#     """
#     earliest_version = get_earliest_catalog_version(api_request_handler.get_oauth_token())
#     latest_version = get_latest_catalog_version(api_request_handler.get_oauth_token())
#     metadata_list = get_version_range_metadata(api_request_handler.get_oauth_token(), earliest_version, latest_version)[
#         "versions"]
#
#     filtered_versions = []
#
#     closest_entry = None
#     closest_diff = float("inf")  # 設定一個極大值，確保可以找到最接近的版本
#
#     for entry in metadata_list:
#         version_number = entry.get("version")
#         timestamp = entry.get("timestamp")
#         dependencies = entry.get("dependencies", [])
#
#         for dependency in dependencies:
#             if dependency.get("hrn") == target_hrn:
#                 target_version = dependency.get("version")
#
#                 # 主要條件: 如果 target_version 落在 min/max_version 區間內，則正常返回
#                 if (min_version is None or target_version >= min_version) and (
#                         max_version is None or target_version <= max_version):
#                     filtered_versions.append({
#                         "version": version_number,
#                         "timestamp": epoch_converter(float(timestamp) / 1000)
#                     })
#                     break  # No need to check further dependencies
#
#                 # 找最接近 min_version 的版本
#                 if min_version is not None:
#                     diff = abs(target_version - min_version)
#                     if diff < closest_diff:
#                         closest_diff = diff
#                         closest_entry = {
#                             "version": version_number,
#                             "timestamp": epoch_converter(float(timestamp) / 1000)
#                         }
#
#     # 如果沒有找到符合 min/max_version 的版本，則回傳最接近的 min_version 版本
#     if not filtered_versions and closest_entry:
#         print(f"⚠️ No exact match found, returning closest version to min_version: {closest_entry}")
#         return [closest_entry]
#
#     return filtered_versions


def get_opensearch_hmc_dvn_worker(oepnsearch_version, target_hrn):
    metadata_list = \
        get_version_range_metadata(api_request_handler.get_oauth_token(), oepnsearch_version - 1, oepnsearch_version)[
            "versions"]
    for entry in metadata_list:
        version_number = entry.get("version")
        timestamp = entry.get("timestamp")
        dependencies = entry.get("dependencies", [])
        for dependency in dependencies:
            if dependency.get("hrn") == target_hrn:
                target_version = dependency.get("version")
                matches = rmob_version_query_service.get_rmob_dvn_query_worker(target_version, target_hrn=target_hrn)
                matches["catalog_hrn"] = target_hrn
                matches["catalog_dvn"] = target_version
                return matches
