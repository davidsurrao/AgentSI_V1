from flask import Flask
from routes import routes

# ✅ Explicitly Set Static Folder to app/static/
app = Flask(__name__, static_folder="app/static", static_url_path="/static")

# ✅ Added Secret Key for Session Security (required for flash messages)
app.secret_key = "f5b8e37df053e68e14f862a987b22032bb4ca77ae6241d944038f47e7bf38429"

app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
