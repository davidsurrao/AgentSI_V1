import subprocess
import json
import os
from flask import Flask
from routes import routes

# ✅ Explicitly Set Static Folder to app/static/
app = Flask(__name__, static_folder="app/static", static_url_path="/static")

# ✅ Added Secret Key for Session Security (required for flash messages)
app.secret_key = "f5b8e37df053e68e14f862a987b22032bb4ca77ae6241d944038f47e7bf38429"

# ✅ Register custom Jinja2 filter to support `| basename` in templates
@app.template_filter('basename')
def basename_filter(path):
    return os.path.basename(path)

# ✅ Register routes blueprint
app.register_blueprint(routes)

# ✅ Launch Background LLM Servers for all models
def launch_llm_servers():
    with open("config.json") as f:
        config = json.load(f)

    models = config.get("models", [])

    for model in models:
        model_path = model.get("path")
        port = model.get("port")

        if not model_path or not port:
            print("⚠️ Skipping model due to missing path or port:", model)
            continue

        command = [
            "python",
            "-m",
            "llama_cpp.server",
            "--model", model_path,
            "--port", str(port)
        ]

        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Launched: {os.path.basename(model_path)} on port {port}")

# ✅ Start Flask app and launch LLMs
if __name__ == "__main__":
    launch_llm_servers()
    app.run(host="0.0.0.0", port=8080, debug=True)
