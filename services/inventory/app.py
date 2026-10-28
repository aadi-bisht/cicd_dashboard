import time

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

item_dict = {}

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


@app.route("/stock/<name>", methods=["GET"])
def get_stock(name):
    if name not in item_dict:
        return jsonify({"error": "item name does not exist"}), 404

    quantity = item_dict[name]
    return jsonify({"name": name, "quantity": quantity}), 200


@app.route("/stock", methods=["POST"])
def add_item():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "JSON body with a valid data is required"}), 400
    if "name" not in data:
        return jsonify({"error": "'name' field is required"}), 400
    if "quantity" not in data:
        return jsonify({"error": "'quantity' field is required"}), 400

    item_dict[data["name"]] = data["quantity"]

    return jsonify({"name":data["name"], "quantity":item_dict[data["name"]]}), 201


@app.route("/metrics")
def metrics():
    output = generate_latest()
    return Response(output, mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)