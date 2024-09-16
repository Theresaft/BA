# server/__init__.py
import os
from flask import Flask
from flask_cors import CORS

from server.main.routes import main_blueprint

def create_app():

    # instantiate the app
    app = Flask( __name__ )
    CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust origins as needed

    # register blueprints
    app.register_blueprint(main_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    return app
