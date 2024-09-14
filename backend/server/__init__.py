# server/__init__.py
import os
from flask import Flask
from flask_cors import CORS


def create_app():

    # instantiate the app
    app = Flask( __name__ )
    CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust origins as needed

    # set config
    app_settings = os.getenv("APP_SETTINGS")
    app.config.from_object(app_settings)

    # register blueprints
    from server.main.routes import main_blueprint

    app.register_blueprint(main_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    return app
