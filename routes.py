from flask import Blueprint, request, jsonify, render_template, send_from_directory
import os
from models import store_text, query_text

routes = Blueprint("routes", __name__)

# ✅ Force Flask to Serve Static Files
@routes.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.abspath("app/static"), filename)

# ✅ Homepage Route
@routes.route("/")
def home():
    return render_template("index.html")

# ✅ Fix Create Data Route (Remove Login)
@routes.route("/create_data")
def create_data():
    return render_template("create_data.html")

# ✅ Store Text Data
@routes.route("/store", methods=["POST"])
def store():
    data = request.json
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    store_text(text, metadata)
    return jsonify({"message": "Text stored successfully!"})

# ✅ Fix Query Response Formatting
@routes.route("/query", methods=["GET"])
def query():
    query_text_value = request.args.get("query", "")
    results = query_text(query_text_value)
    return render_template("query_results.html", results=[doc.page_content for doc in results])
