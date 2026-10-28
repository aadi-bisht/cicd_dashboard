import os
import requests
import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

item_list = []

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://localhost:5001")

REQUEST_COUNT  = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY  = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)


@app.before_request
def before():
    start = time.perf_counter()
    g.start = start


@app.after_request
def after(response):
    path = request.path

    if path == "/metrics":
        return response

    rule = request.url_rule
    if rule is None:
        endpoint = "unmatched"
    else:
        endpoint = rule.rule

    end = time.perf_counter()
    duration = end - g.start

    method = request.method
    status = response.status_code
    REQUEST_COUNT.labels(method, endpoint, status).inc()
    REQUEST_LATENCY.labels(endpoint).observe(duration)

    return response


@app.route("/health")
def health():
    result = {"status": "ok"}
    return jsonify(result), 200


@app.route("/items", methods=["GET"])
def get_items():
    return jsonify(item_list), 200


@app.route("/items", methods=["POST"])
def add_item():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "JSON body with a 'name' field is required"}), 400
    if "name" not in data:
        return jsonify({"error": "JSON body with a 'name' field is required"}), 400

    new_id = len(item_list) + 1
    new_item = {"id": new_id, "name": data["name"]}
    item_list.append(new_item)

    return jsonify(new_item), 201


@app.route("/items/<name>/stock", methods=["GET"])
def get_item_stock(name):
    url = f"{INVENTORY_URL}/stock/{name}"

    try:
        resp = requests.get(url, timeout=2)
    except requests.exceptions.RequestException:
        return jsonify({"error": "inventory service unavailable"}), 503

    return jsonify(resp.json()), resp.status_code


@app.route("/metrics")
def metrics():
    output = generate_latest()
    return Response(output, mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)