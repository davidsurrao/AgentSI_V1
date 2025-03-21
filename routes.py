from flask import Blueprint, request, render_template, send_from_directory, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
from models import store_text, query_text, get_active_model
from utils.ocr import extract_text
import ntpath

routes = Blueprint("routes", __name__)

UPLOAD_FOLDER = r"C:\Users\david\Documents\AgentSI_V1\uploads"
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    'txt', 'csv', 'json', 'pdf', 'docx', 'html', 'md', 'xlsx', 'pptx', 'xml', 'yaml',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Utility Functions for Config ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"categories": {"text": [], "image": [], "file": []}, "projects": [], "active_model": ""}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Static Files ---
@routes.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(os.getcwd(), "app/static"), filename)

# --- Home ---
@routes.route("/")
def home():
    return render_template("index.html")

# --- Store Data ---
@routes.route("/create_data")
def create_data():
    open_section = request.args.get("open", "")
    config = load_config()
    return render_template("create_data.html",
                           open_section=open_section,
                           categories=config.get("categories", {}),
                           projects=config.get("projects", []))

@routes.route("/upload_text", methods=["POST"])
def upload_text():
    text = request.form.get('textInput')
    category = request.form.get('textCategory')
    project = request.form.get('textProject')

    if not text or not category or not project:
        flash("Please complete all fields to store text.", "danger")
        return redirect(url_for('routes.create_data', open='collapseText'))

    metadata = {"category": category, "project": project}
    store_text(text, metadata)

    flash("Text uploaded successfully.", "success")
    return redirect(url_for('routes.create_data', open='collapseText'))

@routes.route("/upload_image", methods=["POST"])
def upload_image():
    image = request.files.get('imageInput')
    category = request.form.get('imageCategory')
    project = request.form.get('imageProject')

    if not image or image.filename == '' or not category or not project:
        flash("Please complete all fields and select an image.", "danger")
        return redirect(url_for('routes.create_data', open='collapseImage'))

    if allowed_file(image.filename):
        filename = secure_filename(image.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(file_path)

        content = extract_text(file_path)
        metadata = {"category": category, "project": project, "filename": filename, "filepath": file_path}
        store_text(content, metadata)

        flash("Image uploaded successfully.", "success")
        return redirect(url_for('routes.create_data', open='collapseImage'))

    flash("Invalid image file type.", "danger")
    return redirect(url_for('routes.create_data', open='collapseImage'))

@routes.route("/upload_file", methods=["POST"])
def upload_file():
    file = request.files.get('fileInput')
    category = request.form.get('fileCategory')
    project = request.form.get('fileProject')

    if not file or file.filename == '' or not category or not project:
        flash("Please complete all fields and select a file.", "danger")
        return redirect(url_for('routes.create_data', open='collapseFile'))

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        if filename.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp')):
            content = extract_text(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

        metadata = {"category": category, "project": project, "filename": filename, "filepath": file_path}
        store_text(content, metadata)

        flash("File uploaded successfully.", "success")
        return redirect(url_for('routes.create_data', open='collapseFile'))

    flash("Invalid file type.", "danger")
    return redirect(url_for('routes.create_data', open='collapseFile'))

# --- Query Data ---
@routes.route("/query", methods=["GET", "POST"])
def query():
    results = []
    error = None

    if request.method == "POST":
        query_text_value = request.form.get("query", "").strip()
        if not query_text_value:
            error = "Please enter a search query."
        else:
            query_results = query_text(query_text_value)
            if isinstance(query_results, list) and all(isinstance(doc, dict) for doc in query_results):
                results = [doc.get("page_content", "No content available") for doc in query_results]
            else:
                error = "Invalid response format from query."

    active_model_path = get_active_model()
    active_model = ntpath.basename(active_model_path) if active_model_path else None

    return render_template("query_results.html", results=results, error=error, active_model=active_model)

# --- Change Model ---
@routes.route("/change_model", methods=["GET", "POST"])
def change_model():
    models = [
        "C:\\Users\\david\\Documents\\AgentSI_V1\\models\\mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "C:\\Users\\david\\Documents\\AgentSI_V1\\models\\DeepSeek-R1-Distill-Qwen-7B-Q8_0.gguf",
        "C:\\Users\\david\\Documents\\AgentSI_V1\\models\\llama-2-7b.Q6_K.gguf",
        "C:\\Users\\david\\Documents\\AgentSI_V1\\models\\qwen2.5-coder-32b-instruct-q8_0.gguf"
    ]
    message = None
    current_active = get_active_model()

    if request.method == "POST":
        selected_model = request.form.get("model")
        if selected_model in models:
            config = load_config()
            config["active_model"] = selected_model
            save_config(config)
            message = "Model changed successfully!"
            current_active = selected_model

    return render_template("change_model.html", models=models, message=message, active_model=current_active)

# --- Admin Page ---
@routes.route("/admin", methods=["GET"])
def admin():
    config = load_config()
    return render_template("admin.html", categories=config.get("categories", {}), projects=config.get("projects", []))

@routes.route("/add_dropdown_value", methods=["POST"])
def add_dropdown_value():
    list_type = request.form.get("list_type")
    new_value = request.form.get("new_value")
    category_type = request.form.get("category_type")

    config = load_config()

    if list_type == "categories":
        if not category_type or not new_value:
            flash("Please select a category type and enter a value.", "danger")
            return redirect(url_for('routes.admin'))

        if category_type not in config["categories"]:
            config["categories"][category_type] = []

        if new_value in config["categories"][category_type]:
            flash(f"{new_value} already exists in {category_type} categories.", "warning")
        else:
            config["categories"][category_type].append(new_value)
            save_config(config)
            flash(f"{new_value} added to {category_type} categories.", "success")

    elif list_type == "projects":
        if new_value in config["projects"]:
            flash(f"{new_value} already exists in projects.", "warning")
        else:
            config["projects"].append(new_value)
            save_config(config)
            flash(f"{new_value} added to projects.", "success")

    return redirect(url_for('routes.admin'))

@routes.route("/delete_dropdown_value", methods=["POST"])
def delete_dropdown_value():
    list_type = request.form.get("list_type")
    value_to_remove = request.form.get("value_to_remove")
    category_type = request.form.get("category_type")

    config = load_config()

    if list_type == "categories":
        if category_type and category_type in config["categories"]:
            if value_to_remove in config["categories"][category_type]:
                config["categories"][category_type].remove(value_to_remove)
                save_config(config)
                flash(f"{value_to_remove} removed from {category_type} categories.", "success")
            else:
                flash(f"{value_to_remove} not found in {category_type} categories.", "danger")
    elif list_type == "projects":
        if value_to_remove in config["projects"]:
            config["projects"].remove(value_to_remove)
            save_config(config)
            flash(f"{value_to_remove} removed from projects.", "success")
        else:
            flash(f"{value_to_remove} not found in projects.", "danger")

    return redirect(url_for('routes.admin'))
