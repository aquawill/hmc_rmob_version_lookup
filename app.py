import os
import time

from flask import Flask, request, jsonify, session

import api_request_handler
from rmob_version_query_service import fetch_pbf_and_cache, get_rmob_dvn_query_worker, get_hmc_dvn_query_worker

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # 保護 session

# 環境變數設定的 debug token
DEBUG_TOKEN = os.getenv("DEBUG_TOKEN", "changeme")


# 環境變數控制是否啟用 Debug API
# DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


@app.route("/get_rmob_dvn", methods=["GET"])
def get_rmob_dvn():
    hmc_dvn = request.args.get("hmc_dvn", type=int)
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


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Healthy"}), 200


@app.route("/debug/enable", methods=["POST"])
def enable_debug():
    """
    Enable debug mode dynamically by passing a valid debug_token.
    """
    data = request.get_json()
    if not data or "debug_token" not in data:
        return jsonify({"error": "Missing debug_token"}), 400

    if data["debug_token"] == DEBUG_TOKEN:
        session["debug_enabled"] = True
        return jsonify({"message": "Debug mode enabled"}), 200
    else:
        return jsonify({"error": "Invalid debug_token"}), 403


@app.route("/debug/disable", methods=["POST"])
def disable_debug():
    """
    Disable debug mode manually.
    """
    if session.get("debug_enabled"):
        session.pop("debug_enabled", None)
        return jsonify({"message": "Debug mode disabled"}), 200
    return jsonify({"message": "Debug mode is already disabled"}), 200


@app.route("/debug/credentials", methods=["GET"])
def debug_credentials():
    """
    Hidden API to return current credentials and token information.
    Can only be accessed if debug mode is enabled via /debug/enable.
    """
    if not session.get("debug_enabled", False):
        return jsonify({"error": "Debug API is disabled"}), 403

    # 獲取目前的 Token 狀態
    token_info = api_request_handler.TOKEN_CACHE
    token = token_info.get("token")
    expires_at = token_info.get("expires_at")

    # 計算 Token 剩餘有效時間
    token_status = "Valid" if token and time.time() < expires_at else "Expired or Missing"

    return jsonify({
        "credentials": {
            "token_endpoint": api_request_handler.OAUTH2_URL,
            "client_id": api_request_handler.CLIENT_ID,
        },
        "token": {
            "status": token_status,
            "expires_in": max(0, int(expires_at - time.time())) if token else None,
            "token_value": token if os.getenv("SHOW_DEBUG_TOKEN", "false").lower() == "true" else "Hidden"
        }
    })


if __name__ == "__main__":
    # Ensure credentials are valid before starting API
    api_request_handler.validate_credentials()
    fetch_pbf_and_cache()  # 啟動時更新快取
    app.run(host="0.0.0.0", port=10000, debug=True)
