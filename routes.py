from flask import Blueprint, request, jsonify, render_template
from models import store_text, query_text

routes = Blueprint("routes", __name__)

# ✅ New Homepage Route (Fix for 404 Error)
@routes.route("/")
def home():
    return render_template("index.html")

@routes.route("/store", methods=["POST"])
def store():
    data = request.json
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    store_text(text, metadata)
    return jsonify({"message": "Text stored successfully!"})

@routes.route("/query", methods=["GET"])
def query():
    query_text_value = request.args.get("query", "")
    results = query_text(query_text_value)
    return jsonify({"results": [doc.page_content for doc in results]})
