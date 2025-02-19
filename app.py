from flask import Flask, request, jsonify
from query_service import fetch_pbf_and_cache, lookup_version, reverse_lookup_version

app = Flask(__name__)

@app.route("/lookup", methods=["GET"])
def api_lookup():
    hmc_version = request.args.get("hmc_version", type=int)
    region = request.args.get("rmob_region", type=str)

    if hmc_version is None:
        return jsonify({"error": "Missing required parameter: hmc_version"}), 400

    fetch_pbf_and_cache()  # 確保快取已更新
    return jsonify(lookup_version(hmc_version, region))

@app.route("/reverse-lookup", methods=["GET"])
def api_reverse_lookup():
    dvn = request.args.get("dvn", type=str)
    region = request.args.get("rmob_region", type=str)

    if not dvn:
        return jsonify({"error": "Missing required parameter: dvn"}), 400

    fetch_pbf_and_cache()
    return jsonify(reverse_lookup_version(dvn, region))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Healthy"}), 200

if __name__ == "__main__":
    fetch_pbf_and_cache()  # 啟動時更新快取
    app.run(host="0.0.0.0", port=10000, debug=True)
