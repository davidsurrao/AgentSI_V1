from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    
    from routes import routes
    app.register_blueprint(routes)
    
    return app
