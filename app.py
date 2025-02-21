import os

from flask import Flask, request, jsonify

import api_request_handler
from opensearch_version_query_service import get_opensearch_hmc_dvn_worker, get_latest_catalog_version
from rmob_version_query_service import fetch_pbf_and_cache, get_rmob_dvn_query_worker, get_hmc_dvn_query_worker

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # 保護 session

# 環境變數設定的 debug token
DEBUG_TOKEN = os.getenv("DEBUG_TOKEN", "changeme")


# 環境變數控制是否啟用 Debug API
# DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


@app.route("/get_rmob_dvn", methods=["GET"])
def get_rmob_dvn():
    hmc_dvn = request.args.get("hmc_dvn", type=str)
    region = request.args.get("rmob_region", type=str)
    if hmc_dvn is None:
        return jsonify({"error": "Missing required parameter: hmc_dvn"}), 400

    fetch_pbf_and_cache()  # 確保快取已更新
    return jsonify(get_rmob_dvn_query_worker(hmc_dvn, region))


@app.route("/get_hmc_dvn", methods=["GET"])
def get_hmc_dvn():
    rmob_dvn = request.args.get("rmob_dvn", type=str)
    region = request.args.get("rmob_region", type=str)

    if not rmob_dvn:
        return jsonify({"error": "Missing required parameter: rmob_dvn"}), 400

    fetch_pbf_and_cache()
    return jsonify(get_hmc_dvn_query_worker(rmob_dvn, region))


@app.route("/get_opensearch_dependencies", methods=["GET"])
def get_opensearch_dependencies():
    opensearch_version = request.args.get("opensearch_version", type=str)
    target_hrn = request.args.get("target_hrn", type=str)

    fetch_pbf_and_cache()  # 確保快取已更新

    if not opensearch_version:
        opensearch_version = get_latest_catalog_version(api_request_handler.get_oauth_token())
    else:
        try:
            opensearch_version = int(opensearch_version)
        except ValueError:
            if opensearch_version == "latest":
                opensearch_version = get_latest_catalog_version(api_request_handler.get_oauth_token())
    if not target_hrn:
        return jsonify({"error": "Missing required parameter: target_hrn"}), 400

    return jsonify(get_opensearch_hmc_dvn_worker(opensearch_version, target_hrn))


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Healthy"}), 200


if __name__ == "__main__":
    # Ensure credentials are valid before starting API
    api_request_handler.validate_credentials()
    fetch_pbf_and_cache()  # 啟動時更新快取
    app.run(host="0.0.0.0", port=10000, debug=True)
