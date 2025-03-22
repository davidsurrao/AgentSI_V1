from flask import Blueprint, request, render_template, send_from_directory, redirect, url_for, flash, session
import os
import json
import requests
import time
from werkzeug.utils import secure_filename
from models import store_text, query_text, get_active_model, list_stored_entries
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

# --- Manage Knowledge Base ---
@routes.route("/manage_knowledge")
def manage_knowledge():
    open_section = request.args.get("open", "")
    config = load_config()
    entries = list_stored_entries()

    return render_template("manage_knowledge_base.html",
                           open_section=open_section,
                           categories=config.get("categories", {}),
                           projects=config.get("projects", []),
                           records=entries)





@routes.route("/upload_text", methods=["POST"])
def upload_text():
    text = request.form.get('textInput')
    category = request.form.get('textCategory')
    project = request.form.get('textProject')

    # Save values to session
    session['stored_text'] = text
    session['stored_category'] = category
    session['stored_project'] = project

    if not text or not category or not project:
        flash("Please complete all fields to store text.", "danger")
        return redirect(url_for('routes.manage_knowledge', open='collapseText'))

    metadata = {"category": category, "project": project}
    store_text(text, metadata)

    # Clear session after successful upload
    session.pop('stored_text', None)
    session.pop('stored_category', None)
    session.pop('stored_project', None)

    flash("Text uploaded successfully.", "success")
    return redirect(url_for('routes.manage_knowledge', open='collapseText'))

@routes.route("/upload_image", methods=["POST"])
def upload_image():
    image = request.files.get('imageInput')
    category = request.form.get('imageCategory')
    project = request.form.get('imageProject')

    session['stored_category'] = category
    session['stored_project'] = project

    if not image or image.filename == '' or not category or not project:
        flash("Please complete all fields and select an image.", "danger")
        return redirect(url_for('routes.manage_knowledge', open='collapseImage'))

    if allowed_file(image.filename):
        filename = secure_filename(image.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(file_path)

        content = extract_text(file_path)
        metadata = {"category": category, "project": project, "filename": filename, "filepath": file_path}
        store_text(content, metadata)

        session.pop('stored_category', None)
        session.pop('stored_project', None)

        flash("Image uploaded successfully.", "success")
        return redirect(url_for('routes.manage_knowledge', open='collapseImage'))

    flash("Invalid image file type.", "danger")
    return redirect(url_for('routes.manage_knowledge', open='collapseImage'))


@routes.route("/upload_file", methods=["POST"])
def upload_file():
    file = request.files.get('fileInput')
    category = request.form.get('fileCategory')
    project = request.form.get('fileProject')

    session['stored_category'] = category
    session['stored_project'] = project

    if not file or file.filename == '' or not category or not project:
        flash("Please complete all fields and select a file.", "danger")
        return redirect(url_for('routes.manage_knowledge', open='collapseFile'))

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

        session.pop('stored_category', None)
        session.pop('stored_project', None)

        flash("File uploaded successfully.", "success")
        return redirect(url_for('routes.manage_knowledge', open='collapseFile'))

    flash("Invalid file type.", "danger")
    return redirect(url_for('routes.manage_knowledge', open='collapseFile'))

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

# --- Query All LLMs ---
@routes.route("/query_all_llms", methods=["GET", "POST"])
def query_all_llms():
    responses = {}
    query_text_value = ""
    config = load_config()
    model_entries = config.get("models", [])
    active_model = config.get("active_model")

    if request.method == "POST":
        query_text_value = request.form.get("query", "").strip()

        for model in model_entries:
            model_path = model.get("path")
            port = model.get("port")
            model_name = os.path.basename(model_path)

            if not model_path or not port:
                responses[model_name] = "⚠️ Invalid model entry."
                continue

            try:
                start_time = time.time()
                res = requests.post(f"http://localhost:{port}/v1/completions", json={
                    "prompt": query_text_value,
                    "max_tokens": 300,
                    "temperature": 0.7
                })
                elapsed = time.time() - start_time
                text = res.json().get("choices", [{}])[0].get("text", "No response")
                responses[model_name] = f"{text}\n\n⏱ Time: {elapsed:.2f} sec"
            except Exception as e:
                responses[model_name] = f"Error: {str(e)}"

    return render_template("query_all_llms.html", query=query_text_value, responses=responses)

# --- Change Model ---
@routes.route("/change_model", methods=["GET", "POST"])
def change_model():
    config = load_config()
    models = config.get("models", [])
    message = None
    current_active = get_active_model()

    if request.method == "POST":
        selected_model = request.form.get("model")
        if any(m["path"] == selected_model for m in models):
            config["active_model"] = selected_model
            save_config(config)
            message = "Model changed successfully!"
            current_active = selected_model

    return render_template("change_model.html", models=models, message=message, active_model=current_active)

# --- Admin Page (Dropdowns + Performance) ---
@routes.route("/admin", methods=["GET"])
def admin():
    config = load_config()
    return render_template("admin.html",
                           categories=config.get("categories", {}),
                           projects=config.get("projects", []),
                           models=config.get("models", []))

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

# --- Save Model Settings ---
@routes.route("/save_model_settings", methods=["POST"])
def save_model_settings():
    config = load_config()
    updated_models = []

    for i, model in enumerate(config.get("models", [])):
        prefix = f"model_{i}_"
        updated_model = {
            "path": model.get("path"),
            "port": model.get("port"),
            "settings": {
                "n_gpu_layers": int(request.form.get(prefix + "n_gpu_layers", -1)),
                "n_ctx": int(request.form.get(prefix + "n_ctx", 2048)),
                "n_threads": int(request.form.get(prefix + "n_threads", 8))
            }
        }
        updated_models.append(updated_model)

    config["models"] = updated_models
    save_config(config)
    flash("Model performance settings saved.", "success")
    return redirect(url_for("routes.admin"))

@routes.route("/delete_entry/<entry_id>", methods=["POST"])
def delete_entry(entry_id):
    try:
        from models import vector_store
        vector_store.delete([entry_id])
        vector_store.persist()
        flash("Entry deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete entry: {str(e)}", "danger")
    return redirect(url_for("routes.manage_knowledge"))

